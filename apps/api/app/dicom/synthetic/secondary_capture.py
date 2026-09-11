from pydicom import FileDataset

from app.dicom.synthetic.base import build_base_dataset


def generate(transfer_key: str) -> FileDataset:
    dataset = build_base_dataset("secondary_capture", transfer_key)
    dataset.ImageType = ["DERIVED", "SECONDARY"]
    dataset.ConversionType = "WSD"
    dataset.DateOfSecondaryCapture = dataset.ContentDate
    dataset.TimeOfSecondaryCapture = dataset.ContentTime
    return dataset
