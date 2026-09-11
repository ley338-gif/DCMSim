import pytest
from app.dicom.datasets import build_study_query
from app.dicom.errors import DicomPresentationContextError
from app.dicom.network import find_studies
from pydicom import Dataset
from pynetdicom import AE, evt
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind, Verification


def study(index: int) -> Dataset:
    dataset = Dataset()
    dataset.QueryRetrieveLevel = "STUDY"
    dataset.PatientName = f"DCMSIM^QUERY{index}"
    dataset.PatientID = f"DCMSIM-Q{index}"
    dataset.StudyDate = "20260911"
    dataset.StudyTime = f"{9 + index:02d}0000"
    dataset.AccessionNumber = f"QR-{index}"
    dataset.StudyDescription = "SYNTHETIC QUERY TEST"
    dataset.StudyInstanceUID = f"1.2.826.0.1.3680043.10.543.{index}"
    dataset.ModalitiesInStudy = "CT" if index == 1 else "MR"
    dataset.NumberOfStudyRelatedSeries = str(index)
    dataset.NumberOfStudyRelatedInstances = str(index * 10)
    return dataset


def test_real_study_root_find_roundtrip_and_query_keys():
    requests = []

    def handle_find(event):
        requests.append(event.identifier)
        yield 0xFF00, study(1)
        yield 0xFF01, study(2)
        yield 0x0000, None

    ae = AE(ae_title="TESTQR")
    ae.add_supported_context(StudyRootQueryRetrieveInformationModelFind)
    server = ae.start_server(
        ("127.0.0.1", 0), block=False, evt_handlers=[(evt.EVT_C_FIND, handle_find)]
    )
    try:
        result = find_studies(
            {
                "host": "127.0.0.1",
                "port": server.server_address[1],
                "called_ae": "TESTQR",
                "calling_ae": "DCMSIM",
            },
            build_study_query({"study_date": "2026-09-11", "modality": "CT"}),
        )
    finally:
        server.shutdown()

    assert result["success"] is True
    assert result["count"] == 2
    assert [entry["patient_id"] for entry in result["entries"]] == ["DCMSIM-Q1", "DCMSIM-Q2"]
    assert result["entries"][0]["instance_count"] == 10
    assert requests[0].QueryRetrieveLevel == "STUDY"
    assert requests[0].StudyDate == "20260911"
    assert requests[0].ModalitiesInStudy == "CT"


def test_study_query_reports_rejected_presentation_context():
    ae = AE(ae_title="TESTQR")
    ae.add_supported_context(Verification)
    server = ae.start_server(("127.0.0.1", 0), block=False)
    try:
        with pytest.raises(DicomPresentationContextError):
            find_studies(
                {
                    "host": "127.0.0.1",
                    "port": server.server_address[1],
                    "called_ae": "TESTQR",
                    "calling_ae": "DCMSIM",
                },
                build_study_query({"study_date": "2026-09-11"}),
            )
    finally:
        server.shutdown()
