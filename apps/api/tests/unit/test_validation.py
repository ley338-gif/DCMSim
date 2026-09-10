import pytest
from app.schemas.common import Endpoint
from pydantic import ValidationError


@pytest.mark.parametrize("ae", ["A" * 17, "AE/TITLE", "", "ÄE"])
def test_rejects_invalid_ae_titles(ae):
    with pytest.raises(ValidationError):
        Endpoint(host="127.0.0.1", port=104, called_ae=ae)


@pytest.mark.parametrize("port", [0, 65536])
def test_rejects_invalid_ports(port):
    with pytest.raises(ValidationError):
        Endpoint(host="pacs.local", port=port, called_ae="PACS")


def test_normalizes_ae_titles():
    endpoint = Endpoint(host="pacs.local", port=104, called_ae="pacs", calling_ae="dcmsim")
    assert endpoint.called_ae == "PACS"
    assert endpoint.calling_ae == "DCMSIM"

