from pathlib import Path
from time import monotonic

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from pydicom.errors import InvalidDicomError
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.dicom.datasets import (
    SOP_LABELS,
    TRANSFER_LABELS,
    build_mwl_query,
    dataset_summary,
    generate_test_dataset,
    read_uploaded_dataset,
)
from app.dicom.errors import DicomError
from app.dicom.network import echo, find_worklist, store_dataset
from app.models import Target, TestRun
from app.schemas.common import (
    EchoRequest,
    Endpoint,
    StoreRequest,
    TargetCreate,
    TargetRead,
    TestRunRead,
    WorklistRequest,
)
from app.services.history import record_run

router = APIRouter(prefix="/api")


def error_result(exc: DicomError, started: float) -> dict:
    return {"success": False, "code": exc.code, "message": exc.message, "details": exc.details, "duration_ms": round((monotonic() - started) * 1000)}


@router.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@router.get("/targets", response_model=list[TargetRead])
def list_targets(db: Session = Depends(get_db)):
    return db.scalars(select(Target).order_by(Target.name)).all()


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
    db.delete(target)
    db.commit()


@router.post("/dicom/echo")
def dicom_echo(payload: EchoRequest, db: Session = Depends(get_db)):
    endpoint, started = payload.model_dump(), monotonic()
    try:
        result = echo(endpoint)
    except DicomError as exc:
        result = error_result(exc, started)
    run = record_run(db, "dicom_echo", endpoint, result)
    return {**result, "run_id": run.id}


@router.post("/dicom/mwl")
def dicom_mwl(payload: WorklistRequest, db: Session = Depends(get_db)):
    endpoint, started = payload.model_dump(), monotonic()
    query = build_mwl_query(payload.filters.model_dump(), payload.broad)
    try:
        result = find_worklist(endpoint, query)
        result["active_filters"] = {} if payload.broad else {k: str(v) for k, v in payload.filters.model_dump().items() if v}
        result["broad"] = payload.broad
    except DicomError as exc:
        result = error_result(exc, started)
    run = record_run(db, "mwl_find", endpoint, result)
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
    result.update(summary)
    result.update({"sop_class": SOP_LABELS[payload.sop_class], "transfer_syntax": TRANSFER_LABELS[payload.transfer_syntax], "calling_ae": payload.calling_ae, "called_ae": payload.called_ae, "target": f"{payload.host}:{payload.port}"})
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
    file: UploadFile = File(...), host: str = Form(...), port: int = Form(...), called_ae: str = Form(...), calling_ae: str = Form("DCMSIM"), target_id: int | None = Form(None), db: Session = Depends(get_db),
):
    try:
        endpoint = Endpoint(host=host, port=port, called_ae=called_ae, calling_ae=calling_ae, target_id=target_id).model_dump()
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
    result.update(summary)
    result.update({"calling_ae": calling_ae, "called_ae": called_ae, "target": f"{host}:{port}"})
    run = record_run(db, "dicom_store", endpoint, result)
    return {**result, "run_id": run.id}


@router.get("/test-runs", response_model=list[TestRunRead])
def list_runs(limit: int = 100, db: Session = Depends(get_db)):
    limit = min(max(limit, 1), 500)
    return db.scalars(select(TestRun).order_by(desc(TestRun.started_at)).limit(limit)).all()


@router.get("/test-runs/{run_id}", response_model=TestRunRead)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(TestRun, run_id)
    if not run:
        raise HTTPException(404, "Test run not found")
    return run

