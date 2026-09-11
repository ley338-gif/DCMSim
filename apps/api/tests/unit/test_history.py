from app.services.history import sanitize_history_result


def test_query_results_keep_counts_but_remove_patient_data_and_filters():
    raw = {
        "success": True,
        "count": 1,
        "entries": [{"patient_name": "PRIVATE^PATIENT", "patient_id": "PRIVATE-1"}],
        "active_filters": {"patient_id": "PRIVATE-1"},
    }

    stored = sanitize_history_result("mwl_find", raw)

    assert stored == {"success": True, "count": 1}
    assert raw["entries"][0]["patient_id"] == "PRIVATE-1"


def test_store_history_removes_patient_identity_but_keeps_technical_uids():
    stored = sanitize_history_result(
        "dicom_store",
        {
            "success": True,
            "patient_name": "PRIVATE^PATIENT",
            "patient_id": "PRIVATE-1",
            "study_instance_uid": "1.2.3",
            "sop_instance_uid": "1.2.3.4",
        },
    )

    assert "patient_name" not in stored
    assert "patient_id" not in stored
    assert stored["study_instance_uid"] == "1.2.3"
    assert stored["sop_instance_uid"] == "1.2.3.4"
