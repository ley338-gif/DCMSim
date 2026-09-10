from datetime import date

from app.dicom.datasets import (
    build_mwl_query,
    dataset_summary,
    generate_test_dataset,
    parse_worklist_result,
)
from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian


def test_mwl_query_builder_maps_filters_to_sps():
    query = build_mwl_query({"date": date(2026, 9, 10), "modality": "ct", "station_ae": "ct01", "patient_id": "P1"})
    sps = query.ScheduledProcedureStepSequence[0]
    assert sps.ScheduledProcedureStepStartDate == "20260910"
    assert sps.Modality == "CT"
    assert sps.ScheduledStationAETitle == "CT01"
    assert query.PatientID == "P1"


def test_broad_query_has_no_matching_keys():
    query = build_mwl_query({"date": date.today(), "modality": "CT"}, broad=True)
    assert query.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate == ""
    assert query.ScheduledProcedureStepSequence[0].Modality == ""


def test_synthetic_ct_has_valid_identifiers_and_pixels():
    ds = generate_test_dataset("ct", "explicit_vr_little_endian")
    summary = dataset_summary(ds)
    assert ds.SOPClassUID == CTImageStorage
    assert ds.file_meta.TransferSyntaxUID == ExplicitVRLittleEndian
    assert ds.PatientName == "DCMSIM^TEST"
    assert summary["study_instance_uid"] and summary["series_instance_uid"] and summary["sop_instance_uid"]
    assert len(ds.PixelData) == 640 * 480


def test_worklist_parser_reads_scheduled_sequence():
    query = build_mwl_query({"modality": "MR", "station_ae": "MR01"})
    query.PatientID = "DCMSIM-TEST-0001"
    row = parse_worklist_result(query)
    assert row["patient_id"] == "DCMSIM-TEST-0001"
    assert row["modality"] == "MR"
    assert any(item["name"] == "Scheduled Procedure Step Sequence" for item in row["dataset"])

