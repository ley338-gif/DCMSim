class DicomError(Exception):
    code = "DICOM_ERROR"

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DicomConnectionError(DicomError):
    code = "DICOM_CONNECTION_FAILED"


class DicomAssociationRejected(DicomError):
    code = "DICOM_ASSOCIATION_REJECTED"


class DicomTimeoutError(DicomError):
    code = "DICOM_TIMEOUT"


class DicomPresentationContextError(DicomError):
    code = "DICOM_NO_PRESENTATION_CONTEXT"


class DicomStoreError(DicomError):
    code = "DICOM_STORE_FAILED"


class DicomFindError(DicomError):
    code = "DICOM_FIND_FAILED"

