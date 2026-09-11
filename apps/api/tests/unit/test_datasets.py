from datetime import date

import pytest
from app.dicom.datasets import (
    MODALITIES,
    SOP_CLASSES,
    build_mwl_query,
    dataset_summary,
    generate_test_dataset,
    parse_worklist_result,
)
from pydicom.uid import ExplicitVRLittleEndian


def test_mwl_query_builder_maps_filters_to_sps():
    query = build_mwl_query(
        {"date": date(2026, 9, 10), "modality": "ct", "station_ae": "ct01", "patient_id": "P1"}
    )
    sps = query.ScheduledProcedureStepSequence[0]
    assert sps.ScheduledProcedureStepStartDate == "20260910"
    assert sps.Modality == "CT"
    assert sps.ScheduledStationAETitle == "CT01"
    assert query.PatientID == "P1"


def test_broad_query_has_no_matching_keys():
    query = build_mwl_query({"date": date.today(), "modality": "CT"}, broad=True)
    assert query.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate == ""
    assert query.ScheduledProcedureStepSequence[0].Modality == ""


@pytest.mark.parametrize("sop_key", ["secondary_capture", "ct", "mr", "ultrasound", "cr", "dx"])
def test_each_synthetic_generator_has_valid_metadata_and_pixels(sop_key):
    ds = generate_test_dataset(sop_key, "explicit_vr_little_endian")
    summary = dataset_summary(ds)
    assert ds.SOPClassUID == SOP_CLASSES[sop_key]
    assert ds.file_meta.TransferSyntaxUID == ExplicitVRLittleEndian
    assert ds.file_meta.MediaStorageSOPInstanceUID == ds.SOPInstanceUID
    assert ds.PatientName == "DCMSIM^TEST"
    assert ds.PatientID.startswith("DCMSIM-")
    assert ds.Modality == MODALITIES[sop_key]
    assert ds.Rows == 480
    assert ds.Columns == 640
    assert ds.PhotometricInterpretation == "MONOCHROME2"
    assert (
        summary["study_instance_uid"]
        and summary["series_instance_uid"]
        and summary["sop_instance_uid"]
    )
    assert len(ds.PixelData) == 640 * 480


def test_modality_generators_add_sop_specific_attributes():
    assert (
        generate_test_dataset("secondary_capture", "explicit_vr_little_endian").ConversionType
        == "WSD"
    )
    assert generate_test_dataset("ct", "explicit_vr_little_endian").KVP == "120"
    assert generate_test_dataset("mr", "explicit_vr_little_endian").MRAcquisitionType == "2D"
    assert generate_test_dataset("ultrasound", "explicit_vr_little_endian").NumberOfFrames == 1
    assert generate_test_dataset("cr", "explicit_vr_little_endian").PlateType == "ST"
    assert (
        generate_test_dataset("dx", "explicit_vr_little_endian").PresentationIntentType
        == "FOR PRESENTATION"
    )


def test_worklist_parser_reads_scheduled_sequence():
    query = build_mwl_query({"modality": "MR", "station_ae": "MR01"})
    query.PatientID = "DCMSIM-TEST-0001"
    row = parse_worklist_result(query)
    assert row["patient_id"] == "DCMSIM-TEST-0001"
    assert row["modality"] == "MR"
    assert any(item["name"] == "Scheduled Procedure Step Sequence" for item in row["dataset"])
