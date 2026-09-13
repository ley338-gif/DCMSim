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
from app.models import DicomEndpoint, ModalityProfile, Target
from app.services.diagnostics import recommendation_for
from app.services.history import record_run

MODALITY_SOP_CLASS = {"CT": "ct", "MR": "mr", "US": "ultrasound", "CR": "cr", "DX": "dx"}


def _legacy_endpoint(profile: ModalityProfile, target: Target, service: str) -> dict[str, Any]:
    return {
        "host": target.host,
        "port": getattr(target, f"{service}_port"),
        "called_ae": getattr(target, f"{service}_called_ae"),
        "calling_ae": profile.calling_ae,
        "target_id": target.id,
    }


def _endpoint(profile: ModalityProfile, endpoint: DicomEndpoint) -> dict[str, Any]:
    return {
        "host": endpoint.host,
        "port": endpoint.port,
        "called_ae": endpoint.called_ae,
        "calling_ae": profile.calling_ae,
        "endpoint_id": endpoint.id,
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
        "message": f"No {service} endpoint is configured for this modality profile",
        "duration_ms": 0,
        "association": False,
        "recommendation": recommendation_for("MODALITY_TARGET_MISSING"),
    }


def _resolved_worklist(profile: ModalityProfile):
    channel = profile.worklist_channel
    if channel is not None:
        station = {
            "profile": profile.calling_ae,
            "fixed": channel.station_ae_fixed_value,
            "omit": None,
        }[channel.station_ae_mode]
        modality = {
            "profile": profile.modality,
            "fixed": channel.modality_filter_fixed_value,
            "omit": None,
        }[channel.modality_filter_mode]
        return _endpoint(profile, channel.mwl_endpoint), channel.mwl_endpoint.name, station, modality
    target = profile.mwl_target
    if target is None or not target.mwl_enabled:
        return None
    return _legacy_endpoint(profile, target, "mwl"), target.name, profile.calling_ae, profile.modality


def _worklist_check(profile: ModalityProfile, diagnostic_broad: bool = False) -> dict[str, Any]:
    resolved = _resolved_worklist(profile)
    if resolved is None:
        return _missing_target("worklist")
    endpoint, target_name, station_ae, modality = resolved
    filters = {"date": date.today(), "modality": modality, "station_ae": station_ae}
    started = monotonic()
    try:
        raw = find_worklist(endpoint, build_mwl_query(filters))
    except DicomError as exc:
        return {
            **_failure(exc, started),
            "query": {key: str(value) for key, value in filters.items() if value},
            "target_name": target_name,
        }
    result = {key: value for key, value in raw.items() if key != "entries"}
    result.update(
        {
            "association": True,
            "query": {key: str(value) for key, value in filters.items() if value},
            "target_name": target_name,
            "privacy": "No automatic broad query was sent",
        }
    )
    if raw["count"] == 0 and diagnostic_broad:
        broad_filters = {"date": filters["date"], "modality": None, "station_ae": None}
        broad_started = monotonic()
        try:
            broad = find_worklist(endpoint, build_mwl_query(broad_filters))
            result["diagnostic_retry"] = {
                "success": True,
                "count": broad["count"],
                "status": broad["status"],
                "duration_ms": broad["duration_ms"],
                "explicit_broad_query": True,
                "active_filters": {"date": str(filters["date"])},
            }
        except DicomError as exc:
            result["diagnostic_retry"] = {
                **_failure(exc, broad_started),
                "explicit_broad_query": True,
            }
    return result


def _resolved_store(profile: ModalityProfile):
    if profile.store_endpoint is not None:
        return _endpoint(profile, profile.store_endpoint), profile.store_endpoint.name
    target = profile.store_target
    if target is None or not target.store_enabled:
        return None
    return _legacy_endpoint(profile, target, "store"), target.name


def _store_check(profile: ModalityProfile, transfer_syntax: str) -> dict[str, Any]:
    resolved = _resolved_store(profile)
    if resolved is None:
        return _missing_target("store")
    endpoint, target_name = resolved
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
            "target_name": target_name,
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
    diagnostic_broad: bool = False,
) -> dict[str, Any]:
    started = monotonic()
    worklist = _worklist_check(profile, diagnostic_broad) if profile.mwl_enabled else {"skipped": True}
    store = _store_check(profile, transfer_syntax) if profile.store_enabled else {"skipped": True}
    enabled_results = [
        result
        for enabled, result in ((profile.mwl_enabled, worklist), (profile.store_enabled, store))
        if enabled
    ]
    success = bool(enabled_results) and all(
        result.get("success", False) for result in enabled_results
    )
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
