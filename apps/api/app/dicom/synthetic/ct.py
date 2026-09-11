from pydicom import FileDataset

from app.dicom.synthetic.base import build_base_dataset


def generate(transfer_key: str) -> FileDataset:
    dataset = build_base_dataset("ct", transfer_key)
    dataset.ImageType = ["ORIGINAL", "PRIMARY", "AXIAL"]
    dataset.KVP = "120"
    dataset.SliceThickness = "5"
    dataset.PixelSpacing = ["0.75", "0.75"]
    dataset.RescaleIntercept = "0"
    dataset.RescaleSlope = "1"
    dataset.PatientPosition = "HFS"
    return dataset
