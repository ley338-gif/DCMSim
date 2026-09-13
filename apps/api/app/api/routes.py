import csv
import io
import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import monotonic

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import ValidationError
from pydicom.errors import InvalidDicomError
from sqlalchemy import delete, desc, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from app.core.config import settings
from app.core.dates import as_utc
from app.core.logging import effective_log_level
from app.db.session import get_db
from app.dicom.datasets import (
    SOP_LABELS,
    TRANSFER_LABELS,
    build_mwl_query,
    build_study_query,
    dataset_summary,
    generate_test_dataset,
    read_uploaded_dataset,
)
from app.dicom.errors import DicomError
from app.dicom.network import echo, find_studies, find_worklist, store_dataset
from app.models import (
    Area,
    DicomEndpoint,
    DicomSystem,
    ModalityProfile,
    Site,
    Target,
    TestRun,
    WorklistChannel,
)
from app.schemas.common import (
    AreaCreate,
    AreaRead,
    ConfigurationImport,
    DicomEndpointCreate,
    DicomEndpointRead,
    DicomSystemCreate,
    DicomSystemRead,
    EchoRequest,
    Endpoint,
    HistoryRetentionRequest,
    InlineModalityProfileCreate,
    InlineModalityProfileRead,
    ModalityCheckRequest,
    ModalityProfileCreate,
    SiteCreate,
    SiteRead,
    StoreRequest,
    StudyQueryRequest,
    TargetCreate,
    TargetRead,
    TargetTestStatusRead,
    TestRunPage,
    TestRunRead,
    WorklistChannelCreate,
    WorklistChannelRead,
    WorklistRequest,
)
from app.services.diagnostics import recommendation_for
from app.services.history import (
    dashboard_summary,
    latest_target_test_statuses,
    query_history,
    record_run,
)
from app.services.modality_checks import run_modality_check
from app.services.modality_profiles import (
    apply_inline_profile,
    collect_internal_channel,
    resolved_profile,
)
from app.services.operations import (
    create_sqlite_backup,
    export_configuration,
    import_configuration,
    purge_history,
)
from app.services.topology_validation import (
    validate_endpoint_service_change,
    validate_worklist_channel_identity_change,
)

router = APIRouter(prefix="/api")


def endpoint_name(db: Session, endpoint: dict) -> str:
    target = db.get(Target, endpoint.get("target_id")) if endpoint.get("target_id") else None
    return target.name if target else "Manuelles Ziel"


def error_result(exc: DicomError, started: float) -> dict:
    return {
        "success": False,
        "code": exc.code,
        "message": exc.message,
        "details": exc.details,
        "recommendation": recommendation_for(exc.code),
        "duration_ms": round((monotonic() - started) * 1000),
    }


@router.get("/health")
def health():
    return {"status": "ok", "version": "0.3.22"}


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Database unavailable") from exc
    return {"status": "ready", "version": "0.3.22"}


@router.get("/settings/runtime")
def runtime_settings():
    """Expose only effective, non-sensitive DICOM process settings."""
    return {
        "connect_timeout": settings.connect_timeout,
        "association_timeout": settings.association_timeout,
        "dimse_timeout": settings.dimse_timeout,
        "log_level": logging.getLevelName(effective_log_level(settings.log_level)),
    }


@router.get("/configuration/export")
def configuration_export(db: Session = Depends(get_db)):
    return export_configuration(db)


@router.post("/configuration/import")
def configuration_import(payload: ConfigurationImport, db: Session = Depends(get_db)):
    return import_configuration(db, payload)


@router.post("/maintenance/history-retention")
def history_retention(payload: HistoryRetentionRequest, db: Session = Depends(get_db)):
    return purge_history(db, payload.days)


@router.get("/maintenance/database-backup")
def database_backup(db: Session = Depends(get_db)):
    path = create_sqlite_backup(db)
    filename = f"dcmsim-backup-{datetime.now():%Y%m%d-%H%M%S}.sqlite3"
    return FileResponse(
        path,
        filename=filename,
        media_type="application/vnd.sqlite3",
        background=BackgroundTask(os.unlink, path),
    )


def _commit_named(db: Session, duplicate_message: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, duplicate_message) from exc


@router.get("/sites", response_model=list[SiteRead])
def list_sites(db: Session = Depends(get_db)):
    return db.scalars(select(Site).order_by(Site.name)).all()


@router.post("/sites", response_model=SiteRead, status_code=201)
def create_site(payload: SiteCreate, db: Session = Depends(get_db)):
    item = Site(**payload.model_dump())
    db.add(item)
    _commit_named(db, "A site with this name already exists")
    db.refresh(item)
    return item


@router.get("/sites/{item_id}", response_model=SiteRead)
def get_site(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Site, item_id)
    if not item:
        raise HTTPException(404, "Site not found")
    return item


@router.put("/sites/{item_id}", response_model=SiteRead)
def update_site(item_id: int, payload: SiteCreate, db: Session = Depends(get_db)):
    item = get_site(item_id, db)
    item.name = payload.name
    _commit_named(db, "A site with this name already exists")
    db.refresh(item)
    return item


@router.delete("/sites/{item_id}", status_code=204)
def delete_site(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Site, item_id)
    if not item:
        raise HTTPException(404, "Site not found")
    area_ids = select(Area.id).where(Area.site_id == item_id)
    db.execute(update(ModalityProfile).where(ModalityProfile.area_id.in_(area_ids)).values(area_id=None))
    db.execute(update(WorklistChannel).where(WorklistChannel.area_id.in_(area_ids)).values(area_id=None))
    db.execute(delete(Area).where(Area.site_id == item_id))
    db.delete(item)
    db.commit()


@router.get("/areas", response_model=list[AreaRead])
def list_areas(site_id: int | None = None, db: Session = Depends(get_db)):
    query = select(Area)
    if site_id is not None:
        query = query.where(Area.site_id == site_id)
    return db.scalars(query.order_by(Area.name)).all()


@router.post("/areas", response_model=AreaRead, status_code=201)
def create_area(payload: AreaCreate, db: Session = Depends(get_db)):
    if not db.get(Site, payload.site_id):
        raise HTTPException(422, "Configured site does not exist")
    item = Area(**payload.model_dump())
    db.add(item)
    _commit_named(db, "An area with this name already exists at the site")
    db.refresh(item)
    return item


@router.get("/areas/{item_id}", response_model=AreaRead)
def get_area(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Area, item_id)
    if not item:
        raise HTTPException(404, "Area not found")
    return item


@router.put("/areas/{item_id}", response_model=AreaRead)
def update_area(item_id: int, payload: AreaCreate, db: Session = Depends(get_db)):
    item = get_area(item_id, db)
    if not db.get(Site, payload.site_id):
        raise HTTPException(422, "Configured site does not exist")
    item.name, item.site_id = payload.name, payload.site_id
    _commit_named(db, "An area with this name already exists at the site")
    db.refresh(item)
    return item


@router.delete("/areas/{item_id}", status_code=204)
def delete_area(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Area, item_id)
    if not item:
        raise HTTPException(404, "Area not found")
    db.execute(update(ModalityProfile).where(ModalityProfile.area_id == item_id).values(area_id=None))
    db.execute(update(WorklistChannel).where(WorklistChannel.area_id == item_id).values(area_id=None))
    db.delete(item)
    db.commit()


@router.get("/dicom-systems", response_model=list[DicomSystemRead])
def list_dicom_systems(db: Session = Depends(get_db)):
    return db.scalars(select(DicomSystem).order_by(DicomSystem.name)).all()


@router.post("/dicom-systems", response_model=DicomSystemRead, status_code=201)
def create_dicom_system(payload: DicomSystemCreate, db: Session = Depends(get_db)):
    item = DicomSystem(**payload.model_dump())
    db.add(item)
    _commit_named(db, "A DICOM system with this name already exists")
    db.refresh(item)
    return item


@router.get("/dicom-systems/{item_id}", response_model=DicomSystemRead)
def get_dicom_system(item_id: int, db: Session = Depends(get_db)):
    item = db.get(DicomSystem, item_id)
    if not item:
        raise HTTPException(404, "DICOM system not found")
    return item


@router.put("/dicom-systems/{item_id}", response_model=DicomSystemRead)
def update_dicom_system(item_id: int, payload: DicomSystemCreate, db: Session = Depends(get_db)):
    item = get_dicom_system(item_id, db)
    item.name = payload.name
    _commit_named(db, "A DICOM system with this name already exists")
    db.refresh(item)
    return item


@router.delete("/dicom-systems/{item_id}", status_code=204)
def delete_dicom_system(item_id: int, db: Session = Depends(get_db)):
    item = db.get(DicomSystem, item_id)
    if not item:
        raise HTTPException(404, "DICOM system not found")
    endpoint_ids = select(DicomEndpoint.id).where(DicomEndpoint.system_id == item_id)
    if db.scalar(select(WorklistChannel.id).where(WorklistChannel.mwl_endpoint_id.in_(endpoint_ids))):
        raise HTTPException(409, "DICOM system is still used by a worklist channel")
    db.execute(update(ModalityProfile).where(ModalityProfile.store_endpoint_id.in_(endpoint_ids)).values(store_endpoint_id=None))
    db.execute(delete(DicomEndpoint).where(DicomEndpoint.system_id == item_id))
    db.delete(item)
    db.commit()


@router.get("/dicom-endpoints", response_model=list[DicomEndpointRead])
def list_dicom_endpoints(system_id: int | None = None, service: str | None = None, db: Session = Depends(get_db)):
    query = select(DicomEndpoint)
    if system_id is not None:
        query = query.where(DicomEndpoint.system_id == system_id)
    if service is not None:
        query = query.where(DicomEndpoint.service == service.upper())
    return db.scalars(query.order_by(DicomEndpoint.name)).all()


@router.post("/dicom-systems/{system_id}/endpoints", response_model=DicomEndpointRead, status_code=201)
def create_dicom_endpoint(system_id: int, payload: DicomEndpointCreate, db: Session = Depends(get_db)):
    if not db.get(DicomSystem, system_id):
        raise HTTPException(422, "Configured DICOM system does not exist")
    item = DicomEndpoint(system_id=system_id, **payload.model_dump())
    db.add(item)
    _commit_named(db, "An endpoint with this name already exists in the system")
    db.refresh(item)
    return item


@router.get("/dicom-endpoints/{item_id}", response_model=DicomEndpointRead)
def get_dicom_endpoint(item_id: int, db: Session = Depends(get_db)):
    item = db.get(DicomEndpoint, item_id)
    if not item:
        raise HTTPException(404, "DICOM endpoint not found")
    return item


@router.put("/dicom-endpoints/{item_id}", response_model=DicomEndpointRead)
def update_dicom_endpoint(item_id: int, payload: DicomEndpointCreate, db: Session = Depends(get_db)):
    item = get_dicom_endpoint(item_id, db)
    validate_endpoint_service_change(db, item.id, item.service, payload.service)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    _commit_named(db, "An endpoint with this name already exists in the system")
    db.refresh(item)
    return item


@router.delete("/dicom-endpoints/{item_id}", status_code=204)
def delete_dicom_endpoint(item_id: int, db: Session = Depends(get_db)):
    item = db.get(DicomEndpoint, item_id)
    if not item:
        raise HTTPException(404, "DICOM endpoint not found")
    if db.scalar(select(WorklistChannel.id).where(WorklistChannel.mwl_endpoint_id == item_id)):
        raise HTTPException(409, "Endpoint is still used by a worklist channel")
    db.execute(update(ModalityProfile).where(ModalityProfile.store_endpoint_id == item_id).values(store_endpoint_id=None))
    db.delete(item)
    db.commit()


def _validate_channel(payload: WorklistChannelCreate, db: Session) -> None:
    if payload.area_id is not None and not db.get(Area, payload.area_id):
        raise HTTPException(422, "Configured area does not exist")
    endpoint = db.get(DicomEndpoint, payload.mwl_endpoint_id)
    if not endpoint or endpoint.service != "MWL":
        raise HTTPException(422, "Worklist channel requires an MWL endpoint")


@router.get("/worklist-channels", response_model=list[WorklistChannelRead])
def list_worklist_channels(area_id: int | None = None, db: Session = Depends(get_db)):
    query = select(WorklistChannel)
    if area_id is not None:
        query = query.where(WorklistChannel.area_id == area_id)
    return db.scalars(query.order_by(WorklistChannel.name)).all()


@router.post("/worklist-channels", response_model=WorklistChannelRead, status_code=201)
def create_worklist_channel(payload: WorklistChannelCreate, db: Session = Depends(get_db)):
    _validate_channel(payload, db)
    item = WorklistChannel(**payload.model_dump())
    db.add(item)
    _commit_named(db, "A worklist channel with this name already exists")
    db.refresh(item)
    return item


@router.get("/worklist-channels/{item_id}", response_model=WorklistChannelRead)
def get_worklist_channel(item_id: int, db: Session = Depends(get_db)):
    item = db.get(WorklistChannel, item_id)
    if not item:
        raise HTTPException(404, "Worklist channel not found")
    return item


@router.put("/worklist-channels/{item_id}", response_model=WorklistChannelRead)
def update_worklist_channel(item_id: int, payload: WorklistChannelCreate, db: Session = Depends(get_db)):
    item = get_worklist_channel(item_id, db)
    _validate_channel(payload, db)
    validate_worklist_channel_identity_change(
        db, item.id, payload.area_id, payload.modality_code
    )
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    _commit_named(db, "A worklist channel with this name already exists")
    db.refresh(item)
    return item


@router.delete("/worklist-channels/{item_id}", status_code=204)
def delete_worklist_channel(item_id: int, db: Session = Depends(get_db)):
    item = db.get(WorklistChannel, item_id)
    if not item:
        raise HTTPException(404, "Worklist channel not found")
    db.execute(update(ModalityProfile).where(ModalityProfile.worklist_channel_id == item_id).values(worklist_channel_id=None))
    db.delete(item)
    db.commit()


@router.get("/targets", response_model=list[TargetRead])
def list_targets(db: Session = Depends(get_db)):
    return db.scalars(select(Target).order_by(Target.name)).all()


@router.get("/targets/test-status", response_model=list[TargetTestStatusRead])
def target_test_status(db: Session = Depends(get_db)):
    return latest_target_test_statuses(db)


@router.post("/targets", response_model=TargetRead, status_code=201)
def create_target(payload: TargetCreate, db: Session = Depends(get_db)):
    target = Target(**payload.model_dump())
    db.add(target)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "A target with this name already exists") from exc
    db.refresh(target)
    return target


@router.get("/targets/{target_id}", response_model=TargetRead)
def get_target(target_id: int, db: Session = Depends(get_db)):
    target = db.get(Target, target_id)
    if not target:
        raise HTTPException(404, "Target not found")
    return target


@router.put("/targets/{target_id}", response_model=TargetRead)
def update_target(target_id: int, payload: TargetCreate, db: Session = Depends(get_db)):
    target = db.get(Target, target_id)
    if not target:
        raise HTTPException(404, "Target not found")
    for key, value in payload.model_dump().items():
        setattr(target, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "A target with this name already exists") from exc
    db.refresh(target)
    return target


@router.delete("/targets/{target_id}", status_code=204)
def delete_target(target_id: int, db: Session = Depends(get_db)):
    target = db.get(Target, target_id)
    if not target:
        raise HTTPException(404, "Target not found")
    db.execute(
        update(ModalityProfile)
        .where(ModalityProfile.mwl_target_id == target_id)
        .values(mwl_target_id=None)
    )
    db.execute(
        update(ModalityProfile)
        .where(ModalityProfile.store_target_id == target_id)
        .values(store_target_id=None)
    )
    db.delete(target)
    db.commit()


def _validate_profile_targets(payload: ModalityProfileCreate, db: Session) -> None:
    if payload.mwl_enabled and payload.worklist_channel_id is not None:
        channel = db.get(WorklistChannel, payload.worklist_channel_id)
        if not channel:
            raise HTTPException(422, "Configured worklist channel does not exist")
        if channel.area_id != payload.area_id:
            raise HTTPException(422, "Worklist channel belongs to a different area")
        if channel.modality_code != payload.modality:
            raise HTTPException(422, "Profile modality does not match worklist channel")
    elif payload.mwl_enabled:
        target = db.get(Target, payload.mwl_target_id)
        if not target:
            raise HTTPException(422, "Configured worklist target does not exist")
        if not target.mwl_enabled:
            raise HTTPException(422, "Selected target does not support worklist")

    if payload.store_enabled and payload.store_endpoint_id is not None:
        store_endpoint = db.get(DicomEndpoint, payload.store_endpoint_id)
        if not store_endpoint or store_endpoint.service != "STORE":
            raise HTTPException(422, "Profile requires a STORE endpoint")
    elif payload.store_enabled:
        target = db.get(Target, payload.store_target_id)
        if not target:
            raise HTTPException(422, "Configured store target does not exist")
        if not target.store_enabled:
            raise HTTPException(422, "Selected target does not support store")


@router.get("/modality-profiles", response_model=list[InlineModalityProfileRead])
def list_modality_profiles(db: Session = Depends(get_db)):
    return [
        resolved_profile(item)
        for item in db.scalars(select(ModalityProfile).order_by(ModalityProfile.name)).all()
    ]


@router.post("/modality-profiles", response_model=InlineModalityProfileRead, status_code=201)
def create_modality_profile(payload: ModalityProfileCreate, db: Session = Depends(get_db)):
    _validate_profile_targets(payload, db)
    profile = ModalityProfile(**payload.model_dump())
    db.add(profile)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "A modality profile with this name already exists") from exc
    db.refresh(profile)
    return resolved_profile(profile)


@router.post(
    "/modality-profiles/inline",
    response_model=InlineModalityProfileRead,
    status_code=201,
)
def create_inline_modality_profile(
    payload: InlineModalityProfileCreate, db: Session = Depends(get_db)
):
    try:
        profile = apply_inline_profile(db, payload)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "A modality profile with this name already exists") from exc
    db.refresh(profile)
    return resolved_profile(profile)


@router.get("/modality-profiles/{profile_id}", response_model=InlineModalityProfileRead)
def get_modality_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(ModalityProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Modality profile not found")
    return resolved_profile(profile)


@router.put("/modality-profiles/{profile_id}", response_model=InlineModalityProfileRead)
def update_modality_profile(
    profile_id: int, payload: ModalityProfileCreate, db: Session = Depends(get_db)
):
    profile = db.get(ModalityProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Modality profile not found")
    _validate_profile_targets(payload, db)
    old_channel_id = profile.worklist_channel_id
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    try:
        db.flush()
        if old_channel_id != profile.worklist_channel_id:
            collect_internal_channel(db, old_channel_id)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "A modality profile with this name already exists") from exc
    db.refresh(profile)
    return resolved_profile(profile)


@router.put(
    "/modality-profiles/{profile_id}/inline",
    response_model=InlineModalityProfileRead,
)
def update_inline_modality_profile(
    profile_id: int,
    payload: InlineModalityProfileCreate,
    db: Session = Depends(get_db),
):
    profile = db.get(ModalityProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Modality profile not found")
    try:
        apply_inline_profile(db, payload, profile)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "A modality profile with this name already exists") from exc
    db.refresh(profile)
    return resolved_profile(profile)


@router.delete("/modality-profiles/{profile_id}", status_code=204)
def delete_modality_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(ModalityProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Modality profile not found")
    old_channel_id = profile.worklist_channel_id
    db.delete(profile)
    db.flush()
    collect_internal_channel(db, old_channel_id)
    db.commit()


@router.post("/modality-profiles/{profile_id}/check")
def check_modality_profile(
    profile_id: int, payload: ModalityCheckRequest, db: Session = Depends(get_db)
):
    profile = db.get(ModalityProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Modality profile not found")
    if payload.diagnostic_broad:
        return run_modality_check(
            db, profile, payload.transfer_syntax, diagnostic_broad=True
        )
    return run_modality_check(db, profile, payload.transfer_syntax)


@router.post("/dicom/echo")
def dicom_echo(payload: EchoRequest, db: Session = Depends(get_db)):
    endpoint, started = payload.model_dump(), monotonic()
    try:
        result = echo(endpoint)
    except DicomError as exc:
        result = error_result(exc, started)
    result["target_name"] = endpoint_name(db, endpoint)
    run = record_run(db, "dicom_echo", endpoint, result)
    return {**result, "run_id": run.id}


@router.post("/dicom/mwl")
def dicom_mwl(payload: WorklistRequest, db: Session = Depends(get_db)):
    endpoint, started = payload.model_dump(), monotonic()
    query = build_mwl_query(payload.filters.model_dump(), payload.broad)
    try:
        result = find_worklist(endpoint, query)
        result["active_filters"] = (
            {}
            if payload.broad
            else {k: str(v) for k, v in payload.filters.model_dump().items() if v}
        )
        result["broad"] = payload.broad
    except DicomError as exc:
        result = error_result(exc, started)
    result["target_name"] = endpoint_name(db, endpoint)
    run = record_run(db, "mwl_find", endpoint, result)
    return {**result, "run_id": run.id}


@router.post("/dicom/studies")
def dicom_studies(payload: StudyQueryRequest, db: Session = Depends(get_db)):
    endpoint, started = payload.model_dump(), monotonic()
    query = build_study_query(payload.filters.model_dump())
    try:
        result = find_studies(endpoint, query)
        result["active_filters"] = {
            key: str(value) for key, value in payload.filters.model_dump().items() if value
        }
    except DicomError as exc:
        result = error_result(exc, started)
    result["target_name"] = endpoint_name(db, endpoint)
    run = record_run(db, "qr_find", endpoint, result)
    return {**result, "run_id": run.id}


@router.post("/dicom/store/generated")
def dicom_store_generated(payload: StoreRequest, db: Session = Depends(get_db)):
    endpoint, started = payload.model_dump(), monotonic()
    ds = generate_test_dataset(payload.sop_class, payload.transfer_syntax)
    summary = dataset_summary(ds)
    try:
        result = store_dataset(endpoint, ds)
    except DicomError as exc:
        result = error_result(exc, started)
    if result.get("code") and not result.get("recommendation"):
        result["recommendation"] = recommendation_for(result["code"])
    result.update(summary)
    result.update(
        {
            "sop_class": SOP_LABELS[payload.sop_class],
            "transfer_syntax": TRANSFER_LABELS[payload.transfer_syntax],
            "calling_ae": payload.calling_ae,
            "called_ae": payload.called_ae,
            "target": f"{payload.host}:{payload.port}",
            "target_name": endpoint_name(db, endpoint),
        }
    )
    run = record_run(db, "dicom_store", endpoint, result)
    return {**result, "run_id": run.id}


async def checked_upload(file: UploadFile) -> bytes:
    if not file.filename or Path(file.filename).suffix.lower() not in {".dcm", ".dicom"}:
        raise HTTPException(400, "Only .dcm or .dicom files are accepted")
    content = await file.read(settings.max_upload_bytes + 1)
    await file.close()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(413, "DICOM file exceeds upload limit")
    return content


@router.post("/dicom/store/analyze")
async def analyze_upload(file: UploadFile = File(...)):
    try:
        return dataset_summary(read_uploaded_dataset(await checked_upload(file)))
    except InvalidDicomError as exc:
        raise HTTPException(400, "File is not a valid DICOM object") from exc


@router.post("/dicom/store/upload")
async def dicom_store_upload(
    file: UploadFile = File(...),
    host: str = Form(...),
    port: int = Form(...),
    called_ae: str = Form(...),
    calling_ae: str = Form("DCMSIM"),
    target_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    try:
        endpoint = Endpoint(
            host=host, port=port, called_ae=called_ae, calling_ae=calling_ae, target_id=target_id
        ).model_dump()
    except ValidationError as exc:
        raise HTTPException(422, exc.errors()) from exc
    started = monotonic()
    try:
        ds = read_uploaded_dataset(await checked_upload(file))
    except InvalidDicomError as exc:
        raise HTTPException(400, "File is not a valid DICOM object") from exc
    summary = dataset_summary(ds)
    try:
        result = store_dataset(endpoint, ds)
    except DicomError as exc:
        result = error_result(exc, started)
    if result.get("code") and not result.get("recommendation"):
        result["recommendation"] = recommendation_for(result["code"])
    result.update(summary)
    result.update({"calling_ae": calling_ae, "called_ae": called_ae, "target": f"{host}:{port}", "target_name": endpoint_name(db, endpoint)})
    run = record_run(db, "dicom_store", endpoint, result)
    return {**result, "run_id": run.id}


@router.get("/test-runs", response_model=list[TestRunRead])
def list_runs(limit: int = 100, db: Session = Depends(get_db)):
    limit = min(max(limit, 1), 500)
    return db.scalars(select(TestRun).order_by(desc(TestRun.started_at), desc(TestRun.id)).limit(limit)).all()


@router.get("/dashboard/summary")
def get_dashboard_summary(day_start: datetime, day_end: datetime, db: Session = Depends(get_db)):
    if day_start.utcoffset() is None or day_end.utcoffset() is None:
        raise HTTPException(422, "Day boundaries require a timezone offset")
    start_utc, end_utc = day_start.astimezone(UTC), day_end.astimezone(UTC)
    if not timedelta(0) < end_utc - start_utc <= timedelta(hours=26):
        raise HTTPException(422, "Invalid day boundaries")
    return dashboard_summary(db, start_utc, end_utc)


@router.get("/test-runs/search", response_model=TestRunPage)
def search_runs(
    test_type: str | None = None,
    success: bool | None = None,
    search: str | None = None,
    started_from: datetime | None = None,
    started_before: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    validate_history_range(started_from, started_before)
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    items, total = query_history(
        db,
        test_type=test_type,
        success=success,
        search=search,
        started_from=started_from,
        started_before=started_before,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


def csv_cell(value: object) -> object:
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value


def validate_history_range(started_from: datetime | None, started_before: datetime | None) -> None:
    if any(value is not None and value.utcoffset() is None for value in (started_from, started_before)):
        raise HTTPException(422, "History boundaries require a timezone offset")
    if started_from is not None and started_before is not None and started_from >= started_before:
        raise HTTPException(422, "History start must precede end")


@router.get("/test-runs/export.csv")
def export_runs_csv(
    test_type: str | None = None,
    success: bool | None = None,
    search: str | None = None,
    started_from: datetime | None = None,
    started_before: datetime | None = None,
    db: Session = Depends(get_db),
):
    validate_history_range(started_from, started_before)
    items, _ = query_history(
        db,
        test_type=test_type,
        success=success,
        search=search,
        started_from=started_from,
        started_before=started_before,
        limit=None,
    )
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")
    writer.writerow(
        [
            "Zeitpunkt",
            "Testtyp",
            "Ziel oder Profil",
            "Host",
            "Calling AE",
            "Called AE",
            "Erfolgreich",
            "Status",
            "Dauer ms",
            "Treffer",
        ]
    )
    for run in items:
        endpoint = run.target_snapshot_json or run.manual_target_json or {}
        profile_name = run.result_json.get("profile_name", "")
        target_name = endpoint.get("name") or run.result_json.get("target_name") or (run.target.name if run.target else "")
        writer.writerow(
            [
                as_utc(run.started_at).isoformat(),
                run.test_type,
                csv_cell(profile_name or target_name),
                csv_cell(endpoint.get("host", "")),
                csv_cell(endpoint.get("calling_ae", "")),
                csv_cell(endpoint.get("called_ae", "")),
                "ja" if run.success else "nein",
                csv_cell(run.status),
                run.duration_ms,
                run.result_json.get("count", ""),
            ]
        )
    filename = f"dcmsim-history-{datetime.now():%Y%m%d-%H%M%S}.csv"
    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/test-runs/{run_id}", response_model=TestRunRead)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(TestRun, run_id)
    if not run:
        raise HTTPException(404, "Test run not found")
    return run
