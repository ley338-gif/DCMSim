"""Local FastAPI plus synthetic DICOM SCPs for browser smoke tests."""

import os
import shutil
import sys
import tempfile
from pathlib import Path

from pydicom import Dataset
from pynetdicom import AE, evt
from pynetdicom.sop_class import ModalityWorklistInformationFind

API_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(API_ROOT))
database_directory = tempfile.mkdtemp(prefix="dcmsim-full-stack-")
os.environ["DCMSIM_DATABASE_URL"] = f"sqlite:///{Path(database_directory) / 'smoke.db'}"

from app.dicom.synthetic import SOP_CLASSES, TRANSFER_SYNTAXES  # noqa: E402
from app.main import app  # noqa: E402


def worklist_result():
    dataset = Dataset()
    dataset.PatientName = "DCMSIM^FULLSTACK"
    dataset.PatientID = "DCMSIM-FULLSTACK-001"
    dataset.PatientBirthDate = "20000101"
    dataset.AccessionNumber = "DCMSIMFSACC001"
    dataset.RequestedProcedureDescription = "FULL STACK SMOKE"
    step = Dataset()
    step.Modality = "CT"
    step.ScheduledStationAETitle = "DCMSIM"
    step.ScheduledProcedureStepStartDate = "20260911"
    step.ScheduledProcedureStepStartTime = "104200"
    step.ScheduledProcedureStepDescription = "NOT FOR CLINICAL USE"
    dataset.ScheduledProcedureStepSequence = [step]
    return dataset


def handle_find(_event):
    yield 0xFF00, worklist_result()
    yield 0x0000, None


def handle_store(event):
    dataset = event.dataset
    if not str(dataset.PatientID).startswith("DCMSIM-"):
        return 0xC000
    return 0x0000


def start_servers():
    mwl_ae = AE(ae_title="TESTMWL")
    mwl_ae.add_supported_context(ModalityWorklistInformationFind)
    mwl_server = mwl_ae.start_server(
        ("127.0.0.1", 11112),
        block=False,
        evt_handlers=[(evt.EVT_C_FIND, handle_find)],
    )

    store_ae = AE(ae_title="TESTPACS")
    for sop_class in SOP_CLASSES.values():
        store_ae.add_supported_context(sop_class, list(TRANSFER_SYNTAXES.values()))
    store_server = store_ae.start_server(
        ("127.0.0.1", 11113),
        block=False,
        evt_handlers=[(evt.EVT_C_STORE, handle_store)],
    )
    return mwl_server, store_server


if __name__ == "__main__":
    import uvicorn

    servers = start_servers()
    try:
        uvicorn.run(app, host="127.0.0.1", port=18080, log_level="warning")
    finally:
        for server in servers:
            server.shutdown()
        shutil.rmtree(database_directory, ignore_errors=True)
