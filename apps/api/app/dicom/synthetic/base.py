from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
from pydicom import FileDataset, FileMetaDataset
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
TRANSFER_SYNTAXES = {
    "explicit_vr_little_endian": ExplicitVRLittleEndian,
    "implicit_vr_little_endian": ImplicitVRLittleEndian,
}
MODALITIES = {
    "secondary_capture": "OT",
    "ct": "CT",
    "mr": "MR",
    "ultrasound": "US",
    "cr": "CR",
    "dx": "DX",
}


def test_pixels(patient_id: str) -> bytes:
    image = Image.new("L", (640, 480), color=20)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=28)
    draw.rectangle((18, 18, 621, 461), outline=220, width=4)
    lines = [
        "DCMSIM TEST",
        "NOT FOR DIAGNOSTIC USE",
        f"Patient: {patient_id}",
        "Study: PACS STORE TEST",
    ]
    for index, line in enumerate(lines):
        draw.text((55, 105 + index * 65), line, fill=240, font=font)
    return image.tobytes()


def build_base_dataset(sop_key: str, transfer_key: str) -> FileDataset:
    now = datetime.now()
    sop_uid, study_uid, series_uid = generate_uid(), generate_uid(), generate_uid()
    sop_class = SOP_CLASSES[sop_key]
    transfer_syntax = TRANSFER_SYNTAXES[transfer_key]
    patient_id = f"DCMSIM-{now:%Y%m%d-%H%M%S}-{sop_uid[-6:]}"

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = sop_class
    meta.MediaStorageSOPInstanceUID = sop_uid
    meta.TransferSyntaxUID = transfer_syntax
    meta.ImplementationClassUID = generate_uid()

    dataset = FileDataset(None, {}, file_meta=meta, preamble=b"\0" * 128)
    dataset.set_original_encoding(
        is_implicit_vr=transfer_syntax == ImplicitVRLittleEndian,
        is_little_endian=True,
    )
    dataset.SOPClassUID = sop_class
    dataset.SOPInstanceUID = sop_uid
    dataset.StudyInstanceUID = study_uid
    dataset.SeriesInstanceUID = series_uid
    dataset.PatientName = "DCMSIM^TEST"
    dataset.PatientID = patient_id
    dataset.PatientBirthDate = ""
    dataset.PatientSex = "O"
    dataset.StudyDate = dataset.SeriesDate = dataset.ContentDate = now.strftime("%Y%m%d")
    dataset.StudyTime = dataset.SeriesTime = dataset.ContentTime = now.strftime("%H%M%S")
    dataset.AccessionNumber = f"DCMSIM-{now:%H%M%S}"
    dataset.StudyID = "DCMSIM"
    dataset.SeriesNumber = 1
    dataset.InstanceNumber = 1
    dataset.Modality = MODALITIES[sop_key]
    dataset.Manufacturer = "DCMSim"
    dataset.ManufacturerModelName = "Synthetic Test Generator"
    dataset.StudyDescription = "PACS STORE TEST"
    dataset.SeriesDescription = "NOT FOR DIAGNOSTIC USE"
    dataset.Rows = 480
    dataset.Columns = 640
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 8
    dataset.BitsStored = 8
    dataset.HighBit = 7
    dataset.PixelRepresentation = 0
    dataset.PixelData = test_pixels(patient_id)
    return dataset
