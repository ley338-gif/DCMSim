from pydicom import FileDataset

from app.dicom.synthetic.base import build_base_dataset


def generate(transfer_key: str) -> FileDataset:
    dataset = build_base_dataset("cr", transfer_key)
    dataset.ImageType = ["ORIGINAL", "PRIMARY"]
    dataset.BodyPartExamined = "CHEST"
    dataset.ViewPosition = "PA"
    dataset.PlateType = "ST"
    return dataset
