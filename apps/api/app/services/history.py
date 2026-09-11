import logging
from copy import deepcopy
from typing import Any

from sqlalchemy.orm import Session

from app.models import TestRun

logger = logging.getLogger("dcmsim.tests")


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
