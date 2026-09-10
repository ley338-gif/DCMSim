from app.dicom.status import classify_store_status, status_hex


def test_store_status_mapping():
    assert classify_store_status(0x0000) == ("success", "Success")
    assert classify_store_status(0xB006)[0] == "warning"
    assert classify_store_status(0xC123)[0] == "failure"
    assert status_hex(0xA700) == "0xA700"

