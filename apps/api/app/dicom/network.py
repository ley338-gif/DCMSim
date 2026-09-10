from time import monotonic
from typing import Any

from pydicom import Dataset
from pynetdicom import AE
from pynetdicom.sop_class import ModalityWorklistInformationFind, Verification

from app.core.config import settings
from app.dicom.datasets import parse_worklist_result
from app.dicom.errors import (
    DicomAssociationRejected,
    DicomConnectionError,
    DicomFindError,
    DicomPresentationContextError,
    DicomTimeoutError,
)
from app.dicom.status import classify_store_status, status_hex


def _ae(calling_ae: str) -> AE:
    ae = AE(ae_title=calling_ae)
    ae.acse_timeout = settings.association_timeout
    ae.connection_timeout = settings.connect_timeout
    ae.dimse_timeout = settings.dimse_timeout
    return ae


def _association_error(assoc, called_ae: str):
    if assoc.is_rejected:
        raise DicomAssociationRejected("Association rejected by remote AE", {"called_ae": called_ae})
    if assoc.is_aborted:
        raise DicomConnectionError("Connection aborted by remote AE")
    raise DicomConnectionError("TCP connection or DICOM association failed")


def echo(endpoint: dict[str, Any]) -> dict[str, Any]:
    started = monotonic()
    ae = _ae(endpoint["calling_ae"])
    ae.add_requested_context(Verification)
    assoc = ae.associate(endpoint["host"], endpoint["port"], ae_title=endpoint["called_ae"])
    if not assoc.is_established:
        _association_error(assoc, endpoint["called_ae"])
    try:
        status = assoc.send_c_echo()
        code = getattr(status, "Status", None)
        if code is None:
            raise DicomTimeoutError("No C-ECHO response received")
        return {"success": code == 0, "status": status_hex(code), "duration_ms": round((monotonic() - started) * 1000), "steps": ["TCP reachable", "Association accepted", "C-ECHO response received"]}
    finally:
        assoc.release()


def find_worklist(endpoint: dict[str, Any], query: Dataset) -> dict[str, Any]:
    started = monotonic()
    ae = _ae(endpoint["calling_ae"])
    ae.add_requested_context(ModalityWorklistInformationFind)
    assoc = ae.associate(endpoint["host"], endpoint["port"], ae_title=endpoint["called_ae"])
    if not assoc.is_established:
        _association_error(assoc, endpoint["called_ae"])
    rows, final_code = [], None
    try:
        for status, identifier in assoc.send_c_find(query, ModalityWorklistInformationFind):
            code = getattr(status, "Status", None) if status else None
            if code in (0xFF00, 0xFF01) and identifier is not None:
                rows.append(parse_worklist_result(identifier))
            else:
                final_code = code
        if final_code is None:
            raise DicomTimeoutError("No final C-FIND response received")
        if final_code != 0:
            raise DicomFindError("C-FIND failed", {"status": status_hex(final_code)})
        return {"success": True, "status": status_hex(final_code), "count": len(rows), "entries": rows, "duration_ms": round((monotonic() - started) * 1000), "steps": ["TCP reachable", "Association accepted", "C-FIND completed successfully"]}
    finally:
        assoc.release()


def store_dataset(endpoint: dict[str, Any], ds: Dataset) -> dict[str, Any]:
    started = monotonic()
    ae = _ae(endpoint["calling_ae"])
    transfer_syntax = ds.file_meta.TransferSyntaxUID
    ae.add_requested_context(ds.SOPClassUID, transfer_syntax)
    assoc = ae.associate(endpoint["host"], endpoint["port"], ae_title=endpoint["called_ae"])
    if not assoc.is_established:
        _association_error(assoc, endpoint["called_ae"])
    try:
        accepted = any(cx.abstract_syntax == ds.SOPClassUID and transfer_syntax in cx.transfer_syntax for cx in assoc.accepted_contexts)
        if not accepted:
            raise DicomPresentationContextError("No acceptable presentation context", {"sop_class": str(ds.SOPClassUID), "transfer_syntax": str(transfer_syntax)})
        status = assoc.send_c_store(ds)
        code = getattr(status, "Status", None) if status else None
        category, message = classify_store_status(code)
        return {"success": category in ("success", "warning"), "category": category, "code": "DICOM_STORE_WARNING" if category == "warning" else "DICOM_STORE_FAILED" if category == "failure" else None, "message": message, "status": status_hex(code), "duration_ms": round((monotonic() - started) * 1000), "steps": ["TCP reachable", "Association accepted", "Presentation Context accepted", "C-STORE sent", "C-STORE response received"]}
    finally:
        assoc.release()
