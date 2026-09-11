from app.dicom.datasets import generate_test_dataset
from app.dicom.network import echo, store_dataset
from pynetdicom import AE, evt
from pynetdicom.sop_class import CTImageStorage, Verification


def test_real_echo_roundtrip():
    ae = AE(ae_title="TESTSCP")
    ae.add_supported_context(Verification)
    server = ae.start_server(("127.0.0.1", 0), block=False)
    try:
        result = echo(
            {
                "host": "127.0.0.1",
                "port": server.server_address[1],
                "called_ae": "TESTSCP",
                "calling_ae": "DCMSIM",
            }
        )
        assert result["success"] is True
        assert result["status"] == "0x0000"
    finally:
        server.shutdown()


def test_real_store_roundtrip():
    received = []

    def handle_store(event):
        received.append(event.dataset)
        return 0x0000

    ae = AE(ae_title="STORESCP")
    ae.add_supported_context(CTImageStorage)
    server = ae.start_server(
        ("127.0.0.1", 0), block=False, evt_handlers=[(evt.EVT_C_STORE, handle_store)]
    )
    try:
        ds = generate_test_dataset("ct", "explicit_vr_little_endian")
        result = store_dataset(
            {
                "host": "127.0.0.1",
                "port": server.server_address[1],
                "called_ae": "STORESCP",
                "calling_ae": "DCMSIM",
            },
            ds,
        )
        assert result["success"] is True
        assert received[0].PatientID.startswith("DCMSIM-")
        assert received[0].SOPClassUID == CTImageStorage
    finally:
        server.shutdown()
