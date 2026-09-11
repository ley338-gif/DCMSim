from pydicom import FileDataset

from app.dicom.synthetic.base import build_base_dataset


def generate(transfer_key: str) -> FileDataset:
    dataset = build_base_dataset("ultrasound", transfer_key)
    dataset.ImageType = ["ORIGINAL", "PRIMARY"]
    dataset.NumberOfFrames = 1
    dataset.UltrasoundColorDataPresent = 0
    dataset.LossyImageCompression = "00"
    return dataset
