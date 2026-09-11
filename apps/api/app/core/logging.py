import logging

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
SENSITIVE_DICOM_LOGGERS = ("pydicom", "pynetdicom")


def configure_logging(log_level: str) -> None:
    """Configure app logs without allowing dependency-level DICOM dataset dumps."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    if not isinstance(level, int):
        level = logging.INFO
    logging.basicConfig(level=level, format=LOG_FORMAT)
    logging.getLogger().setLevel(level)
    for logger_name in SENSITIVE_DICOM_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
