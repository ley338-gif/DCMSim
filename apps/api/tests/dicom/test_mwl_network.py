from time import sleep

import pytest
from app.core.config import settings
from app.dicom.datasets import build_mwl_query
from app.dicom.errors import (
    DicomAssociationAborted,
    DicomAssociationRejected,
    DicomFindError,
    DicomTimeoutError,
)
from app.dicom.network import find_worklist
from pydicom import Dataset
from pynetdicom import AE, evt
from pynetdicom.sop_class import ModalityWorklistInformationFind

ENDPOINT = {"host": "127.0.0.1", "called_ae": "TESTMWL", "calling_ae": "DCMSIM"}


def worklist_dataset(index: int, pending_status: int = 0xFF00) -> tuple[int, Dataset]:
    dataset = Dataset()
    dataset.PatientName = f"DCMSIM^PATIENT{index}"
    dataset.PatientID = f"DCMSIM-P{index}"
    dataset.AccessionNumber = f"DCMSIM-ACC-{index}"
    dataset.PatientBirthDate = "20000101"
    dataset.RequestedProcedureDescription = "SYNTHETIC TEST"
    step = Dataset()
    step.Modality = ["CT", "MR", "US"][index - 1]
    step.ScheduledStationAETitle = "DCMSIM"
    step.ScheduledProcedureStepStartDate = "20260911"
    step.ScheduledProcedureStepStartTime = f"{8 + index:02d}0000"
    step.ScheduledProcedureStepDescription = "NOT FOR CLINICAL USE"
    dataset.ScheduledProcedureStepSequence = [step]
    return pending_status, dataset


def start_mwl_server(handler, *, require_called_ae: bool = False):
    ae = AE(ae_title="TESTMWL")
    ae.add_supported_context(ModalityWorklistInformationFind)
    ae.require_called_aet = require_called_ae
    return ae.start_server(
        ("127.0.0.1", 0),
        block=False,
        evt_handlers=[(evt.EVT_C_FIND, handler)],
    )


def call_mwl(server, **overrides):
    endpoint = {**ENDPOINT, "port": server.server_address[1], **overrides}
    return find_worklist(endpoint, build_mwl_query({}, broad=True))


def test_real_mwl_roundtrip_serializes_three_pending_results_and_final_success():
    requests = []

    def handle_find(event):
        requests.append(event.identifier)
        yield worklist_dataset(1, 0xFF00)
        yield worklist_dataset(2, 0xFF01)
        yield worklist_dataset(3, 0xFF00)
        yield 0x0000, None

    server = start_mwl_server(handle_find)
    try:
        result = call_mwl(server)
    finally:
        server.shutdown()

    assert result["success"] is True
    assert result["status"] == "0x0000"
    assert result["count"] == 3
    assert [row["patient_id"] for row in result["entries"]] == [
        "DCMSIM-P1",
        "DCMSIM-P2",
        "DCMSIM-P3",
    ]
    assert [row["accession_number"] for row in result["entries"]] == [
        "DCMSIM-ACC-1",
        "DCMSIM-ACC-2",
        "DCMSIM-ACC-3",
    ]
    assert [row["modality"] for row in result["entries"]] == ["CT", "MR", "US"]
    assert {row["station_ae"] for row in result["entries"]} == {"DCMSIM"}
    assert [row["start_time"] for row in result["entries"]] == ["090000", "100000", "110000"]
    assert all(row["start_date"] == "20260911" for row in result["entries"])
    assert all(row["dataset"] for row in result["entries"])
    assert requests and requests[0].ScheduledProcedureStepSequence
    assert "Association accepted" in result["steps"]


def test_real_mwl_zero_results():
    def handle_find(_event):
        yield 0x0000, None

    server = start_mwl_server(handle_find)
    try:
        result = call_mwl(server)
    finally:
        server.shutdown()
    assert result["success"] is True
    assert result["count"] == 0


def test_real_mwl_association_reject():
    def handle_find(_event):
        yield 0x0000, None

    server = start_mwl_server(handle_find, require_called_ae=True)
    try:
        with pytest.raises(DicomAssociationRejected):
            call_mwl(server, called_ae="WRONGAE")
    finally:
        server.shutdown()


def test_real_mwl_association_abort():
    def handle_find(event):
        event.assoc.abort()
        yield 0x0000, None

    server = start_mwl_server(handle_find)
    try:
        with pytest.raises(DicomAssociationAborted):
            call_mwl(server)
    finally:
        server.shutdown()


def test_real_mwl_c_find_failure():
    def handle_find(_event):
        yield 0xA700, None

    server = start_mwl_server(handle_find)
    try:
        with pytest.raises(DicomFindError) as raised:
            call_mwl(server)
    finally:
        server.shutdown()
    assert raised.value.code == "DICOM_C_FIND_FAILED"
    assert raised.value.details["status"] == "0xA700"


def test_real_mwl_missing_final_response_times_out(monkeypatch):
    def handle_find(_event):
        yield worklist_dataset(1)
        sleep(0.35)

    monkeypatch.setattr(settings, "dimse_timeout", 0.1)
    server = start_mwl_server(handle_find)
    try:
        with pytest.raises(DicomTimeoutError):
            call_mwl(server)
    finally:
        server.shutdown()
