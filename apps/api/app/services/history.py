import logging
from collections.abc import Sequence
from copy import deepcopy
from typing import Any

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models import Target, TestRun

logger = logging.getLogger("dcmsim.tests")


def history_filters(
    test_type: str | None = None,
    success: bool | None = None,
    search: str | None = None,
) -> list[Any]:
    filters: list[Any] = []
    if test_type:
        filters.append(TestRun.test_type == test_type)
    if success is not None:
        filters.append(TestRun.success == success)
    if search and (term := search.strip()):
        pattern = f"%{term}%"
        filters.append(
            or_(
                TestRun.status.ilike(pattern),
                TestRun.test_type.ilike(pattern),
                Target.name.ilike(pattern),
                cast(TestRun.manual_target_json, String).ilike(pattern),
                cast(TestRun.result_json["profile_name"], String).ilike(pattern),
            )
        )
    return filters


def query_history(
    db: Session,
    *,
    test_type: str | None = None,
    success: bool | None = None,
    search: str | None = None,
    limit: int | None = 50,
    offset: int = 0,
) -> tuple[Sequence[TestRun], int]:
    filters = history_filters(test_type, success, search)
    base = select(TestRun).outerjoin(Target).where(*filters)
    total = db.scalar(
        select(func.count()).select_from(TestRun).outerjoin(Target).where(*filters)
    ) or 0
    query = base.order_by(TestRun.started_at.desc(), TestRun.id.desc()).offset(offset)
    if limit is not None:
        query = query.limit(limit)
    items = db.scalars(query).all()
    return items, total


def sanitize_history_result(test_type: str, result: dict[str, Any]) -> dict[str, Any]:
    """Return the technical result that may safely be persisted in test history."""
    sanitized = deepcopy(result)
    if test_type in {"mwl_find", "qr_find"}:
        sanitized.pop("entries", None)
        sanitized.pop("active_filters", None)
    if test_type == "dicom_store":
        sanitized.pop("patient_name", None)
        sanitized.pop("patient_id", None)
    return sanitized


def record_run(
    db: Session, test_type: str, endpoint: dict[str, Any], result: dict[str, Any]
) -> TestRun:
    target_id = endpoint.get("target_id")
    manual = None
    if not target_id and endpoint.get("host"):
        manual = {
            key: endpoint.get(key) for key in ("host", "port", "called_ae", "calling_ae")
        }
    run = TestRun(
        test_type=test_type,
        target_id=target_id,
        manual_target_json=manual,
        duration_ms=result.get("duration_ms", 0),
        success=result.get("success", False),
        status=result.get("status") or result.get("code", "UNKNOWN"),
        result_json=sanitize_history_result(test_type, result),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    logger.info(
        "test_complete type=%s target=%s calling_ae=%s called_ae=%s duration_ms=%s success=%s error_class=%s",
        test_type,
        endpoint.get("host"),
        endpoint.get("calling_ae"),
        endpoint.get("called_ae"),
        run.duration_ms,
        run.success,
        result.get("code"),
    )
    return run
