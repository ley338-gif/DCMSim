from pydicom import FileDataset

from app.dicom.synthetic.base import build_base_dataset


def generate(transfer_key: str) -> FileDataset:
    dataset = build_base_dataset("dx", transfer_key)
    dataset.ImageType = ["ORIGINAL", "PRIMARY"]
    dataset.PresentationIntentType = "FOR PRESENTATION"
    dataset.BodyPartExamined = "CHEST"
    dataset.ViewPosition = "PA"
    dataset.ImageLaterality = "U"
    return dataset
