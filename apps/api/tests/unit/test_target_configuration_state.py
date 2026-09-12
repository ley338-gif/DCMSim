from app.models import Target
from app.models import TestRun as RunModel
from app.services.history import target_configuration_state


def target():
    return Target(
        name="PACS",
        host="pacs.example",
        mwl_enabled=True,
        mwl_port=104,
        mwl_called_ae="WORKLIST",
        store_enabled=True,
        store_port=11112,
        store_called_ae="STORE",
        qr_enabled=False,
        default_calling_ae="DCMSIM",
    )


def run(test_type="dicom_store", **snapshot_changes):
    snapshot = {
        "host": "pacs.example",
        "port": 11112,
        "called_ae": "STORE",
        "calling_ae": "DCMSIM",
    }
    snapshot.update(snapshot_changes)
    return RunModel(test_type=test_type, target=target(), target_snapshot_json=snapshot)


def test_current_configuration_requires_the_same_service_endpoint():
    assert target_configuration_state(run()) == "current"
    assert target_configuration_state(run("dicom_echo")) == "current"
    assert target_configuration_state(run("mwl_find")) == "changed"
    assert target_configuration_state(run("qr_find")) == "changed"


def test_each_network_parameter_can_make_a_result_stale():
    for change in (
        {"host": "other.example"},
        {"port": 104},
        {"called_ae": "OTHER"},
        {"calling_ae": "OTHER"},
    ):
        assert target_configuration_state(run(**change)) == "changed"


def test_older_runs_without_complete_snapshot_cannot_verify_current_configuration():
    old = run()
    old.target_snapshot_json = None
    assert target_configuration_state(old) == "unknown"
    assert target_configuration_state(run(port=None)) == "unknown"
