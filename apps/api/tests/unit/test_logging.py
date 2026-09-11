import logging

from app.core.logging import configure_logging


def test_dicom_dependency_info_logs_are_suppressed():
    root = logging.getLogger()
    pynetdicom = logging.getLogger("pynetdicom")
    pydicom = logging.getLogger("pydicom")
    previous = (root.level, pynetdicom.level, pydicom.level)
    records: list[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    capture = Capture()
    pynetdicom.addHandler(capture)
    try:
        configure_logging("DEBUG")
        pynetdicom.info("PatientName=PRIVATE^PATIENT")
        pynetdicom.warning("Association warning without dataset")
        assert root.level == logging.DEBUG
        assert pynetdicom.level == logging.WARNING
        assert pydicom.level == logging.WARNING
        assert [record.getMessage() for record in records] == [
            "Association warning without dataset"
        ]
    finally:
        pynetdicom.removeHandler(capture)
        root.setLevel(previous[0])
        pynetdicom.setLevel(previous[1])
        pydicom.setLevel(previous[2])


def test_invalid_application_log_level_falls_back_to_info():
    root = logging.getLogger()
    previous = root.level
    try:
        configure_logging("not-a-level")
        assert root.level == logging.INFO
    finally:
        root.setLevel(previous)
