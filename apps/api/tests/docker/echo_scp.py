"""Disposable DICOM Verification SCP for the Docker egress smoke test."""

from pynetdicom import AE
from pynetdicom.sop_class import Verification

ae = AE(ae_title="TESTSCP")
ae.add_supported_context(Verification)
ae.start_server(("0.0.0.0", 11112), block=True)
