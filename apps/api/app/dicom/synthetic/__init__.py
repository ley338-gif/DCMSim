from collections.abc import Callable

from pydicom import FileDataset

from app.dicom.synthetic import cr, ct, dx, mr, secondary_capture, ultrasound
from app.dicom.synthetic.base import MODALITIES, SOP_CLASSES, TRANSFER_SYNTAXES

GENERATORS: dict[str, Callable[[str], FileDataset]] = {
    "secondary_capture": secondary_capture.generate,
    "ct": ct.generate,
    "mr": mr.generate,
    "ultrasound": ultrasound.generate,
    "cr": cr.generate,
    "dx": dx.generate,
}


def generate_test_dataset(sop_key: str, transfer_key: str) -> FileDataset:
    return GENERATORS[sop_key](transfer_key)


__all__ = [
    "MODALITIES",
    "SOP_CLASSES",
    "TRANSFER_SYNTAXES",
    "generate_test_dataset",
]
