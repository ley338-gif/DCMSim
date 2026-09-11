from datetime import date
from time import monotonic
from typing import Any

from sqlalchemy.orm import Session

from app.dicom.datasets import (
    SOP_LABELS,
    TRANSFER_LABELS,
    build_mwl_query,
    dataset_summary,
    generate_test_dataset,
)
from app.dicom.errors import DicomError
from app.dicom.network import find_worklist, store_dataset
from app.models import ModalityProfile, Target
from app.services.diagnostics import recommendation_for
from app.services.history import record_run

MODALITY_SOP_CLASS = {
    "CT": "ct",
    "MR": "mr",
    "US": "ultrasound",
    "CR": "cr",
    "DX": "dx",
}


def _endpoint(profile: ModalityProfile, target: Target, service: str) -> dict[str, Any]:
    return {
        "host": target.host,
        "port": getattr(target, f"{service}_port"),
        "called_ae": getattr(target, f"{service}_called_ae"),
        "calling_ae": profile.calling_ae,
        "target_id": target.id,
    }


def _failure(exc: DicomError, started: float) -> dict[str, Any]:
    return {
        "success": False,
        "code": exc.code,
        "message": exc.message,
        "details": exc.details,
        "duration_ms": round((monotonic() - started) * 1000),
        "association": bool(exc.details.get("association", False)),
        "recommendation": recommendation_for(exc.code),
    }


def _missing_target(service: str) -> dict[str, Any]:
    return {
        "success": False,
        "code": "MODALITY_TARGET_MISSING",
        "message": f"No {service} target is configured for this modality profile",
        "duration_ms": 0,
        "association": False,
        "recommendation": recommendation_for("MODALITY_TARGET_MISSING"),
    }


def _worklist_check(profile: ModalityProfile) -> dict[str, Any]:
    target = profile.mwl_target
    if target is None or not target.mwl_enabled:
        return _missing_target("worklist")
    endpoint = _endpoint(profile, target, "mwl")
    filters = {
        "date": date.today(),
        "modality": profile.modality,
        "station_ae": profile.calling_ae,
    }
    started = monotonic()
    try:
        raw = find_worklist(endpoint, build_mwl_query(filters))
    except DicomError as exc:
        return {
            **_failure(exc, started),
            "query": {key: str(value) for key, value in filters.items()},
            "target_name": target.name,
        }

    result = {
        key: value for key, value in raw.items() if key != "entries"
    }
    result.update(
        {
            "association": True,
            "query": {key: str(value) for key, value in filters.items()},
            "target_name": target.name,
        }
    )
    if raw["count"] == 0:
        retry_filters = {**filters, "station_ae": None}
        retry_started = monotonic()
        try:
            retry = find_worklist(endpoint, build_mwl_query(retry_filters))
            result["diagnostic_retry"] = {
                "success": True,
                "count": retry["count"],
                "status": retry["status"],
                "duration_ms": retry["duration_ms"],
                "without_station_ae": True,
            }
            if retry["count"] > 0:
                result["observation"] = (
                    f"Worklist is reachable. No entries matched Scheduled Station AE Title "
                    f"{profile.calling_ae}; without Station AE, {retry['count']} entries were returned."
                )
        except DicomError as exc:
            result["diagnostic_retry"] = {
                **_failure(exc, retry_started),
                "without_station_ae": True,
            }
    return result


def _store_check(profile: ModalityProfile, transfer_syntax: str) -> dict[str, Any]:
    target = profile.store_target
    if target is None or not target.store_enabled:
        return _missing_target("store")
    endpoint = _endpoint(profile, target, "store")
    sop_key = MODALITY_SOP_CLASS.get(profile.modality, "secondary_capture")
    fallback = sop_key == "secondary_capture" and profile.modality != "OT"
    dataset = generate_test_dataset(sop_key, transfer_syntax)
    summary = dataset_summary(dataset)
    started = monotonic()
    try:
        result = store_dataset(endpoint, dataset)
    except DicomError as exc:
        result = _failure(exc, started)
    if result.get("code") and not result.get("recommendation"):
        result["recommendation"] = recommendation_for(result["code"])
    result.update(summary)
    result.update(
        {
            "association": bool(
                result.get("details", {}).get("association")
                or "Association accepted" in result.get("steps", [])
            ),
            "target_name": target.name,
            "sop_class": SOP_LABELS[sop_key],
            "sop_key": sop_key,
            "transfer_syntax": TRANSFER_LABELS[transfer_syntax],
            "fallback_secondary_capture": fallback,
        }
    )
    return result


def run_modality_check(
    db: Session,
    profile: ModalityProfile,
    transfer_syntax: str = "explicit_vr_little_endian",
) -> dict[str, Any]:
    started = monotonic()
    worklist = _worklist_check(profile) if profile.mwl_enabled else {"skipped": True}
    store = (
        _store_check(profile, transfer_syntax) if profile.store_enabled else {"skipped": True}
    )
    enabled_results = [
        result
        for enabled, result in (
            (profile.mwl_enabled, worklist),
            (profile.store_enabled, store),
        )
        if enabled
    ]
    success = all(result.get("success", False) for result in enabled_results)
    result = {
        "success": success,
        "status": "PASS" if success else "FAIL",
        "overall": "success" if success else "failure",
        "profile_id": profile.id,
        "profile_name": profile.name,
        "modality": profile.modality,
        "calling_ae": profile.calling_ae,
        "worklist": worklist,
        "store": store,
        "duration_ms": round((monotonic() - started) * 1000),
    }
    run = record_run(db, "modality_check", {}, result)
    return {**result, "run_id": run.id}
