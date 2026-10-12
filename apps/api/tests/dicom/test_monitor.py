import json
import subprocess
from datetime import datetime

from app import monitor
from pydicom import Dataset
from pynetdicom import AE, evt
from pynetdicom.sop_class import ModalityWorklistInformationFind, Verification


def endpoint(port: int, service: str = "MWL") -> dict:
    return {"id": 1, "system": "RIS", "name": "Radiologie", "service": service, "host": "127.0.0.1", "port": port, "called_ae": "TESTSCP", "calling_ae": "DCMSIM", "window": None, "min_count": 0}


def test_real_mwl_monitor_counts_without_patient_output():
    def find(_event):
        ds = Dataset()
        ds.PatientName = "SECRET^PATIENT"
        ds.PatientID = "SECRET-123"
        ds.ScheduledProcedureStepSequence = [Dataset()]
        yield 0xFF00, ds
        yield 0x0000, None

    ae = AE(ae_title="TESTSCP")
    ae.add_supported_context(ModalityWorklistInformationFind)
    server = ae.start_server(("127.0.0.1", 0), block=False, evt_handlers=[(evt.EVT_C_FIND, find)])
    try:
        result = monitor.check_endpoint(endpoint(server.server_address[1]))
    finally:
        server.shutdown()
    line = monitor.local_check_line(endpoint(104), result)
    assert result["state"] == 0
    assert result["count"] == 1
    assert "count=1|duration_ms=" in line
    assert "SECRET" not in json.dumps(result) + line


def test_real_echo_and_failed_find_are_classified():
    ae = AE(ae_title="TESTSCP")
    ae.add_supported_context(Verification)
    ae.add_supported_context(ModalityWorklistInformationFind)

    def find(_event):
        yield 0xA700, None

    server = ae.start_server(("127.0.0.1", 0), block=False, evt_handlers=[(evt.EVT_C_FIND, find)])
    try:
        store = monitor.check_endpoint(endpoint(server.server_address[1], "STORE"))
        mwl = monitor.check_endpoint(endpoint(server.server_address[1]))
    finally:
        server.shutdown()
    assert store["state"] == 0
    assert mwl["state"] == 2
    assert "DICOM_C_FIND_FAILED" in mwl["message"]
    assert "prüfen" in mwl["message"]


def test_window_warn_and_overnight_logic():
    assert monitor.window_active("22:00-06:00", datetime(2026, 10, 12, 23))
    assert monitor.window_active("22:00-06:00", datetime(2026, 10, 13, 5))
    assert not monitor.window_active("22:00-06:00", datetime(2026, 10, 13, 12))
    value = endpoint(104)
    value.update(window="07:00-18:00", min_count=1)
    from unittest.mock import patch

    with patch("app.monitor.find_worklist", return_value={"success": True, "count": 0, "duration_ms": 1}):
        warn = monitor.check_endpoint(value, datetime(2026, 10, 12, 9))
        ok = monitor.check_endpoint(value, datetime(2026, 10, 12, 19))
    assert warn["state"] == 1 and ok["state"] == 0
    assert "Mindestanzahl" in warn["message"]


def test_worker_timeout_is_crit_and_other_endpoints_continue(monkeypatch):
    def expired(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("worker", 0.1)

    monkeypatch.setattr(monitor.subprocess, "run", expired)
    first = monitor._worker(endpoint(104), 0.1)
    assert first["state"] == 2
    assert "DICOM_TIMEOUT" in monitor.local_check_line(endpoint(104), first)
    results = monitor.run_checks([endpoint(104), endpoint(105)], timeout=0.2, jobs=2, per_endpoint_timeout=0.1)
    assert len(results) == 2
    assert all(result["state"] == 2 for result in results)
