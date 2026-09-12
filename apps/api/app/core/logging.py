import logging

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
SENSITIVE_DICOM_LOGGERS = ("pydicom", "pynetdicom")


def effective_log_level(log_level: str) -> int:
    level = getattr(logging, log_level.upper(), logging.INFO)
    return level if isinstance(level, int) else logging.INFO


def configure_logging(log_level: str) -> None:
    """Configure app logs without allowing dependency-level DICOM dataset dumps."""
    level = effective_log_level(log_level)
    logging.basicConfig(level=level, format=LOG_FORMAT)
    logging.getLogger().setLevel(level)
    for logger_name in SENSITIVE_DICOM_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
