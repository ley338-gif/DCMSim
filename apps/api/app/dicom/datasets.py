from datetime import date, datetime
from io import BytesIO
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from pydicom import Dataset, FileDataset, FileMetaDataset, dcmread
from pydicom.uid import (
    ComputedRadiographyImageStorage,
    CTImageStorage,
    DigitalXRayImageStorageForPresentation,
    ExplicitVRLittleEndian,
    ImplicitVRLittleEndian,
    MRImageStorage,
    SecondaryCaptureImageStorage,
    UltrasoundImageStorage,
    generate_uid,
)

SOP_CLASSES = {
    "secondary_capture": SecondaryCaptureImageStorage,
    "ct": CTImageStorage,
    "mr": MRImageStorage,
    "ultrasound": UltrasoundImageStorage,
    "cr": ComputedRadiographyImageStorage,
    "dx": DigitalXRayImageStorageForPresentation,
}
SOP_LABELS = {
    "secondary_capture": "Secondary Capture Image Storage",
    "ct": "CT Image Storage",
    "mr": "MR Image Storage",
    "ultrasound": "Ultrasound Image Storage",
    "cr": "Computed Radiography Image Storage",
    "dx": "Digital X-Ray Image Storage",
}
TRANSFER_SYNTAXES = {
    "explicit_vr_little_endian": ExplicitVRLittleEndian,
    "implicit_vr_little_endian": ImplicitVRLittleEndian,
}
TRANSFER_LABELS = {
    "explicit_vr_little_endian": "Explicit VR Little Endian",
    "implicit_vr_little_endian": "Implicit VR Little Endian",
}
MODALITIES = {
    "secondary_capture": "OT", "ct": "CT", "mr": "MR",
    "ultrasound": "US", "cr": "CR", "dx": "DX",
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


def _test_pixels(patient_id: str) -> bytes:
    image = Image.new("L", (640, 480), color=20)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=28)
    draw.rectangle((18, 18, 621, 461), outline=220, width=4)
    lines = ["DCMSIM TEST", "NOT FOR DIAGNOSTIC USE", f"Patient: {patient_id}", "Study: PACS STORE TEST"]
    for idx, line in enumerate(lines):
        draw.text((55, 105 + idx * 65), line, fill=240, font=font)
    return image.tobytes()


def generate_test_dataset(sop_key: str, transfer_key: str) -> FileDataset:
    sop_uid, study_uid, series_uid = generate_uid(), generate_uid(), generate_uid()
    sop_class = SOP_CLASSES[sop_key]
    transfer_syntax = TRANSFER_SYNTAXES[transfer_key]
    now = datetime.now()
    patient_id = f"DCMSIM-{now:%Y%m%d-%H%M%S}"
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = sop_class
    meta.MediaStorageSOPInstanceUID = sop_uid
    meta.TransferSyntaxUID = transfer_syntax
    meta.ImplementationClassUID = generate_uid()
    ds = FileDataset(None, {}, file_meta=meta, preamble=b"\0" * 128)
    ds.SOPClassUID, ds.SOPInstanceUID = sop_class, sop_uid
    ds.StudyInstanceUID, ds.SeriesInstanceUID = study_uid, series_uid
    ds.PatientName, ds.PatientID, ds.PatientBirthDate, ds.PatientSex = "DCMSIM^TEST", patient_id, "", "O"
    ds.StudyDate = ds.SeriesDate = ds.ContentDate = now.strftime("%Y%m%d")
    ds.StudyTime = ds.SeriesTime = ds.ContentTime = now.strftime("%H%M%S")
    ds.AccessionNumber, ds.StudyID = f"DCMSIM-{now:%H%M%S}", "DCMSIM"
    ds.SeriesNumber, ds.InstanceNumber, ds.Modality = 1, 1, MODALITIES[sop_key]
    ds.Manufacturer = "DCMSim"
    ds.StudyDescription, ds.SeriesDescription = "PACS STORE TEST", "NOT FOR DIAGNOSTIC USE"
    ds.Rows, ds.Columns, ds.SamplesPerPixel = 480, 640, 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated, ds.BitsStored, ds.HighBit, ds.PixelRepresentation = 8, 8, 7, 0
    ds.PixelData = _test_pixels(patient_id)
    return ds


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
        "patient_name": str(ds.get("PatientName", "")), "patient_id": str(ds.get("PatientID", "")),
        "birth_date": str(ds.get("PatientBirthDate", "")), "accession_number": str(ds.get("AccessionNumber", "")),
        "modality": str(sps.get("Modality", "")), "station_ae": str(sps.get("ScheduledStationAETitle", "")),
        "start_date": str(sps.get("ScheduledProcedureStepStartDate", "")), "start_time": str(sps.get("ScheduledProcedureStepStartTime", "")),
        "sps_description": str(sps.get("ScheduledProcedureStepDescription", "")),
        "requested_procedure_description": str(ds.get("RequestedProcedureDescription", "")),
        "dataset": serialize_dataset(ds),
    }
