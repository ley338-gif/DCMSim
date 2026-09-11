from pydicom import FileDataset

from app.dicom.synthetic.base import build_base_dataset


def generate(transfer_key: str) -> FileDataset:
    dataset = build_base_dataset("mr", transfer_key)
    dataset.ImageType = ["ORIGINAL", "PRIMARY", "OTHER"]
    dataset.ScanningSequence = "GR"
    dataset.SequenceVariant = "NONE"
    dataset.ScanOptions = "NONE"
    dataset.MRAcquisitionType = "2D"
    dataset.RepetitionTime = "500"
    dataset.EchoTime = "15"
    dataset.MagneticFieldStrength = "1.5"
    dataset.PixelSpacing = ["0.75", "0.75"]
    return dataset
