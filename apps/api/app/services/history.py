import logging
from collections.abc import Sequence
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import String, case, cast, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Target, TestRun

logger = logging.getLogger("dcmsim.tests")


def history_filters(
    test_type: str | None = None,
    success: bool | None = None,
    search: str | None = None,
    started_from: datetime | None = None,
    started_before: datetime | None = None,
) -> list[Any]:
    filters: list[Any] = []
    if test_type:
        filters.append(TestRun.test_type == test_type)
    if success is not None:
        filters.append(TestRun.success == success)
    if started_from is not None:
        filters.append(TestRun.started_at >= started_from.astimezone(UTC))
    if started_before is not None:
        filters.append(TestRun.started_at < started_before.astimezone(UTC))
    if search and (term := search.strip()):
        pattern = f"%{term}%"
        filters.append(
            or_(
                TestRun.status.ilike(pattern),
                TestRun.test_type.ilike(pattern),
                Target.name.ilike(pattern),
                cast(TestRun.manual_target_json, String).ilike(pattern),
                cast(TestRun.target_snapshot_json, String).ilike(pattern),
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
    started_from: datetime | None = None,
    started_before: datetime | None = None,
    limit: int | None = 50,
    offset: int = 0,
) -> tuple[Sequence[TestRun], int]:
    filters = history_filters(test_type, success, search, started_from, started_before)
    base = select(TestRun).outerjoin(Target).where(*filters)
    total = db.scalar(
        select(func.count()).select_from(TestRun).outerjoin(Target).where(*filters)
    ) or 0
    query = base.order_by(TestRun.started_at.desc(), TestRun.id.desc()).offset(offset)
    if limit is not None:
        query = query.limit(limit)
    items = db.scalars(query).all()
    return items, total


def dashboard_summary(db: Session, day_start: datetime, day_end: datetime) -> dict[str, Any]:
    today_total, today_success = db.execute(
        select(
            func.count(TestRun.id),
            func.sum(case((TestRun.success.is_(True), 1), else_=0)),
        ).where(TestRun.started_at >= day_start, TestRun.started_at < day_end)
    ).one()
    by_type = dict(
        db.execute(
            select(TestRun.test_type, func.count(TestRun.id)).group_by(TestRun.test_type)
        ).all()
    )
    return {
        "today_total": today_total,
        "today_success": today_success or 0,
        "by_type": by_type,
    }


def target_configuration_state(run: TestRun) -> str:
    """Decide whether the latest run proves the target's *current* endpoint."""
    snapshot = run.target_snapshot_json
    target = run.target
    if not snapshot or not target:
        return "unknown"
    if any(snapshot.get(key) is None for key in ("host", "port", "called_ae", "calling_ae")):
        return "unknown"

    services = {
        "mwl_find": ("mwl",),
        "qr_find": ("qr",),
        "dicom_store": ("store",),
        "dicom_echo": ("mwl", "store", "qr"),
    }.get(run.test_type)
    if not services:
        return "unknown"

    if str(snapshot["host"]).casefold() != target.host.casefold():
        return "changed"
    if snapshot["calling_ae"] != target.default_calling_ae:
        return "changed"
    for service in services:
        if (
            getattr(target, f"{service}_enabled")
            and snapshot["port"] == getattr(target, f"{service}_port")
            and snapshot["called_ae"] == getattr(target, f"{service}_called_ae")
        ):
            return "current"
    return "changed"


def latest_target_test_statuses(db: Session) -> list[dict[str, Any]]:
    latest_ids = (
        select(TestRun.target_id, func.max(TestRun.id).label("run_id"))
        .where(TestRun.target_id.is_not(None))
        .group_by(TestRun.target_id)
        .subquery()
    )
    runs = db.scalars(
        select(TestRun)
        .join(latest_ids, TestRun.id == latest_ids.c.run_id)
        .options(joinedload(TestRun.target))
    ).all()
    return [
        {
            "target_id": run.target_id,
            "run_id": run.id,
            "test_type": run.test_type,
            "started_at": run.started_at,
            "duration_ms": run.duration_ms,
            "success": run.success,
            "status": run.status,
            "configuration_state": target_configuration_state(run),
        }
        for run in runs
        if run.target_id is not None
    ]


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
    snapshot = None
    if endpoint.get("host"):
        snapshot = {
            key: endpoint.get(key) for key in ("host", "port", "called_ae", "calling_ae")
        }
        if target_id and result.get("target_name"):
            snapshot["name"] = result["target_name"]
    run = TestRun(
        test_type=test_type,
        target_id=target_id,
        manual_target_json=manual,
        target_snapshot_json=snapshot,
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
