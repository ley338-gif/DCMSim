import pytest
from app.services.diagnostics import RECOMMENDATIONS, recommendation_for


@pytest.mark.parametrize(
    "code",
    [
        "TCP_CONNECTION_FAILED",
        "DICOM_ASSOCIATION_REJECTED",
        "DICOM_ASSOCIATION_ABORTED",
        "DICOM_TIMEOUT",
        "DICOM_NO_PRESENTATION_CONTEXT",
        "DICOM_C_FIND_FAILED",
        "DICOM_STORE_WARNING",
        "DICOM_STORE_FAILED",
        "MODALITY_TARGET_MISSING",
    ],
)
def test_every_supported_failure_has_an_actionable_recommendation(code):
    assert recommendation_for(code) == RECOMMENDATIONS[code]


def test_unknown_codes_do_not_get_a_misleading_recommendation():
    assert recommendation_for("UNKNOWN") is None
