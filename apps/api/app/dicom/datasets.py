from datetime import date
from io import BytesIO
from typing import Any

from pydicom import Dataset, FileDataset, dcmread

from app.dicom.synthetic import (
    MODALITIES,
    SOP_CLASSES,
    TRANSFER_SYNTAXES,
    generate_test_dataset,
)

__all__ = [
    "MODALITIES",
    "SOP_CLASSES",
    "TRANSFER_SYNTAXES",
    "build_mwl_query",
    "build_study_query",
    "dataset_summary",
    "generate_test_dataset",
    "parse_worklist_result",
    "parse_study_result",
    "read_uploaded_dataset",
    "serialize_dataset",
]

SOP_LABELS = {
    "secondary_capture": "Secondary Capture Image Storage",
    "ct": "CT Image Storage",
    "mr": "MR Image Storage",
    "ultrasound": "Ultrasound Image Storage",
    "cr": "Computed Radiography Image Storage",
    "dx": "Digital X-Ray Image Storage",
}
TRANSFER_LABELS = {
    "explicit_vr_little_endian": "Explicit VR Little Endian",
    "implicit_vr_little_endian": "Implicit VR Little Endian",
}


def build_mwl_query(filters: dict[str, Any], broad: bool = False) -> Dataset:
    query = Dataset()
    query.PatientName = ""
    query.PatientID = ""
    query.PatientBirthDate = ""
    query.AccessionNumber = ""
    query.RequestedProcedureDescription = ""
    sps = Dataset()
    sps.ScheduledStationAETitle = ""
    sps.ScheduledProcedureStepStartDate = ""
    sps.ScheduledProcedureStepStartTime = ""
    sps.Modality = ""
    sps.ScheduledProcedureStepDescription = ""
    if not broad:
        if filters.get("patient_name"):
            query.PatientName = filters["patient_name"]
        if filters.get("patient_id"):
            query.PatientID = filters["patient_id"]
        if filters.get("accession_number"):
            query.AccessionNumber = filters["accession_number"]
        filter_date = filters.get("date")
        if isinstance(filter_date, date):
            filter_date = filter_date.strftime("%Y%m%d")
        if filter_date:
            sps.ScheduledProcedureStepStartDate = str(filter_date).replace("-", "")
        if filters.get("modality"):
            sps.Modality = filters["modality"].upper()
        if filters.get("station_ae"):
            sps.ScheduledStationAETitle = filters["station_ae"].upper()
    query.ScheduledProcedureStepSequence = [sps]
    return query


def build_study_query(filters: dict[str, Any]) -> Dataset:
    query = Dataset()
    query.QueryRetrieveLevel = "STUDY"
    query.PatientName = filters.get("patient_name") or ""
    query.PatientID = filters.get("patient_id") or ""
    query.AccessionNumber = filters.get("accession_number") or ""
    study_date = filters.get("study_date")
    if isinstance(study_date, date):
        study_date = study_date.strftime("%Y%m%d")
    query.StudyDate = str(study_date).replace("-", "") if study_date else ""
    query.StudyTime = ""
    query.StudyInstanceUID = ""
    query.StudyDescription = ""
    query.ModalitiesInStudy = (filters.get("modality") or "").upper()
    query.NumberOfStudyRelatedSeries = ""
    query.NumberOfStudyRelatedInstances = ""
    return query


def read_uploaded_dataset(content: bytes) -> FileDataset:
    return dcmread(BytesIO(content), force=False)


def dataset_summary(ds: Dataset) -> dict[str, str]:
    return {
        "patient_name": str(ds.get("PatientName", "")),
        "patient_id": str(ds.get("PatientID", "")),
        "study_instance_uid": str(ds.get("StudyInstanceUID", "")),
        "series_instance_uid": str(ds.get("SeriesInstanceUID", "")),
        "sop_instance_uid": str(ds.get("SOPInstanceUID", "")),
        "sop_class_uid": str(ds.get("SOPClassUID", "")),
        "transfer_syntax_uid": str(getattr(ds.file_meta, "TransferSyntaxUID", "")),
        "modality": str(ds.get("Modality", "")),
    }


def serialize_dataset(ds: Dataset) -> list[dict[str, Any]]:
    result = []
    for elem in ds:
        if elem.tag.group == 0x7FE0:
            value: Any = f"<binary pixel data: {len(elem.value)} bytes>"
        elif elem.VR == "SQ":
            value = [serialize_dataset(item) for item in elem.value]
        else:
            value = str(elem.value)
        result.append({"tag": str(elem.tag), "name": elem.name, "vr": elem.VR, "value": value})
    return result


def parse_worklist_result(ds: Dataset) -> dict[str, Any]:
    sequence = getattr(ds, "ScheduledProcedureStepSequence", [])
    sps = sequence[0] if sequence else Dataset()
    return {
        "patient_name": str(ds.get("PatientName", "")),
        "patient_id": str(ds.get("PatientID", "")),
        "birth_date": str(ds.get("PatientBirthDate", "")),
        "accession_number": str(ds.get("AccessionNumber", "")),
        "modality": str(sps.get("Modality", "")),
        "station_ae": str(sps.get("ScheduledStationAETitle", "")),
        "start_date": str(sps.get("ScheduledProcedureStepStartDate", "")),
        "start_time": str(sps.get("ScheduledProcedureStepStartTime", "")),
        "sps_description": str(sps.get("ScheduledProcedureStepDescription", "")),
        "requested_procedure_description": str(ds.get("RequestedProcedureDescription", "")),
        "dataset": serialize_dataset(ds),
    }


def parse_study_result(ds: Dataset) -> dict[str, Any]:
    modalities = ds.get("ModalitiesInStudy", "")
    if not isinstance(modalities, str) and hasattr(modalities, "__iter__"):
        modalities = "\\".join(str(item) for item in modalities)
    def count(keyword: str) -> int:
        try:
            return int(ds.get(keyword, 0) or 0)
        except (TypeError, ValueError):
            return 0
    return {
        "patient_name": str(ds.get("PatientName", "")),
        "patient_id": str(ds.get("PatientID", "")),
        "accession_number": str(ds.get("AccessionNumber", "")),
        "study_date": str(ds.get("StudyDate", "")),
        "study_time": str(ds.get("StudyTime", "")),
        "study_description": str(ds.get("StudyDescription", "")),
        "study_instance_uid": str(ds.get("StudyInstanceUID", "")),
        "modalities": str(modalities),
        "series_count": count("NumberOfStudyRelatedSeries"),
        "instance_count": count("NumberOfStudyRelatedInstances"),
        "dataset": serialize_dataset(ds),
    }
