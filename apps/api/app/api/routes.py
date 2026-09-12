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
from sqlalchemy import desc, select, update
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
from app.models import ModalityProfile, Target, TestRun
from app.schemas.common import (
    ConfigurationImport,
    EchoRequest,
    Endpoint,
    HistoryRetentionRequest,
    ModalityCheckRequest,
    ModalityProfileCreate,
    ModalityProfileRead,
    StoreRequest,
    StudyQueryRequest,
    TargetCreate,
    TargetRead,
    TargetTestStatusRead,
    TestRunPage,
    TestRunRead,
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
from app.services.operations import (
    create_sqlite_backup,
    export_configuration,
    import_configuration,
    purge_history,
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
    return {"status": "ok", "version": "0.3.16"}


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Database unavailable") from exc
    return {"status": "ready", "version": "0.3.16"}


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
    checks = (
        (payload.mwl_enabled, payload.mwl_target_id, "mwl", "worklist"),
        (payload.store_enabled, payload.store_target_id, "store", "store"),
    )
    for enabled, target_id, attribute, label in checks:
        if not enabled:
            continue
        target = db.get(Target, target_id)
        if not target:
            raise HTTPException(422, f"Configured {label} target does not exist")
        if not getattr(target, f"{attribute}_enabled"):
            raise HTTPException(422, f"Selected target does not support {label}")


@router.get("/modality-profiles", response_model=list[ModalityProfileRead])
def list_modality_profiles(db: Session = Depends(get_db)):
    return db.scalars(select(ModalityProfile).order_by(ModalityProfile.name)).all()


@router.post("/modality-profiles", response_model=ModalityProfileRead, status_code=201)
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
    return profile


@router.get("/modality-profiles/{profile_id}", response_model=ModalityProfileRead)
def get_modality_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(ModalityProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Modality profile not found")
    return profile


@router.put("/modality-profiles/{profile_id}", response_model=ModalityProfileRead)
def update_modality_profile(
    profile_id: int, payload: ModalityProfileCreate, db: Session = Depends(get_db)
):
    profile = db.get(ModalityProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Modality profile not found")
    _validate_profile_targets(payload, db)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "A modality profile with this name already exists") from exc
    db.refresh(profile)
    return profile


@router.delete("/modality-profiles/{profile_id}", status_code=204)
def delete_modality_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(ModalityProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Modality profile not found")
    db.delete(profile)
    db.commit()


@router.post("/modality-profiles/{profile_id}/check")
def check_modality_profile(
    profile_id: int, payload: ModalityCheckRequest, db: Session = Depends(get_db)
):
    profile = db.get(ModalityProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Modality profile not found")
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
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    items, total = query_history(
        db,
        test_type=test_type,
        success=success,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


def csv_cell(value: object) -> object:
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value


@router.get("/test-runs/export.csv")
def export_runs_csv(
    test_type: str | None = None,
    success: bool | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    items, _ = query_history(
        db,
        test_type=test_type,
        success=success,
        search=search,
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
