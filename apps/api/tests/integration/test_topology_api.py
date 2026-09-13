import pytest
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'topology.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def session_override():
        with factory() as database:
            yield database

    app.dependency_overrides[get_db] = session_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_topology_crud_and_organizational_delete_preserves_profile(client):
    site = client.post("/api/sites", json={"name": "Klinikum Nord"})
    assert site.status_code == 201
    site_id = site.json()["id"]
    area = client.post("/api/areas", json={"name": "Radiologie", "site_id": site_id})
    assert area.status_code == 201
    area_id = area.json()["id"]

    system = client.post("/api/dicom-systems", json={"name": "PACS Nord"})
    assert system.status_code == 201
    system_id = system.json()["id"]
    mwl = client.post(
        f"/api/dicom-systems/{system_id}/endpoints",
        json={"name": "RIS MWL", "service": "MWL", "host": "ris.local", "port": 104, "called_ae": "RIS_MWL"},
    )
    store = client.post(
        f"/api/dicom-systems/{system_id}/endpoints",
        json={"name": "PACS Store", "service": "STORE", "host": "pacs.local", "port": 11112, "called_ae": "PACS"},
    )
    assert mwl.status_code == store.status_code == 201

    channel = client.post(
        "/api/worklist-channels",
        json={
            "name": "Radiologie CT",
            "area_id": area_id,
            "modality_code": "CT",
            "mwl_endpoint_id": mwl.json()["id"],
            "station_ae_mode": "profile",
            "station_ae_fixed_value": None,
            "modality_filter_mode": "fixed",
            "modality_filter_fixed_value": "CT",
        },
    )
    assert channel.status_code == 201
    profile = client.post(
        "/api/modality-profiles",
        json={
            "name": "CT 1",
            "description": None,
            "modality": "CT",
            "calling_ae": "CT01",
            "area_id": area_id,
            "worklist_channel_id": channel.json()["id"],
            "store_endpoint_id": store.json()["id"],
        },
    )
    assert profile.status_code == 201

    assert client.delete(f"/api/areas/{area_id}").status_code == 204
    preserved = client.get(f"/api/modality-profiles/{profile.json()['id']}").json()
    assert preserved["area_id"] is None
    assert preserved["worklist_channel_id"] == channel.json()["id"]
    assert preserved["store_endpoint_id"] == store.json()["id"]
    preserved_channel = client.get(f"/api/worklist-channels/{channel.json()['id']}").json()
    assert preserved_channel["area_id"] is None
    assert client.get("/api/sites").json()[0]["name"] == "Klinikum Nord"


def test_endpoint_and_channel_service_validation(client):
    site = client.post("/api/sites", json={"name": "S"}).json()
    area = client.post("/api/areas", json={"name": "A", "site_id": site["id"]}).json()
    system = client.post("/api/dicom-systems", json={"name": "Archive"}).json()
    store = client.post(
        f"/api/dicom-systems/{system['id']}/endpoints",
        json={"name": "Store", "service": "STORE", "host": "pacs.local", "port": 104, "called_ae": "PACS"},
    ).json()
    response = client.post(
        "/api/worklist-channels",
        json={
            "name": "Bad",
            "area_id": area["id"],
            "modality_code": "CT",
            "mwl_endpoint_id": store["id"],
            "station_ae_mode": "fixed",
            "station_ae_fixed_value": None,
            "modality_filter_mode": "omit",
            "modality_filter_fixed_value": None,
        },
    )
    assert response.status_code == 422


def test_referenced_endpoint_service_cannot_change_but_unused_endpoint_can(client):
    system = client.post("/api/dicom-systems", json={"name": "Archive"}).json()
    mwl = client.post(
        f"/api/dicom-systems/{system['id']}/endpoints",
        json={"name": "MWL", "service": "MWL", "host": "ris.local", "port": 104, "called_ae": "RIS"},
    ).json()
    store = client.post(
        f"/api/dicom-systems/{system['id']}/endpoints",
        json={"name": "Store", "service": "STORE", "host": "pacs.local", "port": 104, "called_ae": "PACS"},
    ).json()
    unused = client.post(
        f"/api/dicom-systems/{system['id']}/endpoints",
        json={"name": "Unused", "service": "QR", "host": "pacs.local", "port": 105, "called_ae": "PACSQR"},
    ).json()
    channel = client.post(
        "/api/worklist-channels",
        json={"name": "CT", "area_id": None, "modality_code": "CT", "mwl_endpoint_id": mwl["id"], "station_ae_mode": "profile", "station_ae_fixed_value": None, "modality_filter_mode": "profile", "modality_filter_fixed_value": None},
    ).json()
    assert client.post(
        "/api/modality-profiles",
        json={"name": "CT 1", "description": None, "modality": "CT", "calling_ae": "CT01", "area_id": None, "worklist_channel_id": channel["id"], "store_endpoint_id": store["id"]},
    ).status_code == 201

    for endpoint, service in ((mwl, "STORE"), (store, "QR")):
        response = client.put(
            f"/api/dicom-endpoints/{endpoint['id']}",
            json={**endpoint, "service": service},
        )
        assert response.status_code == 409
        assert client.get(f"/api/dicom-endpoints/{endpoint['id']}").json()["service"] == endpoint["service"]

    changed = client.put(
        f"/api/dicom-endpoints/{unused['id']}",
        json={**unused, "service": "STORE"},
    )
    assert changed.status_code == 200
    assert changed.json()["service"] == "STORE"


def test_configuration_export_v2_contains_normalized_topology(client):
    site = client.post("/api/sites", json={"name": "Nord"}).json()
    area = client.post("/api/areas", json={"name": "Radiologie", "site_id": site["id"]}).json()
    system = client.post("/api/dicom-systems", json={"name": "RIS"}).json()
    mwl = client.post(
        f"/api/dicom-systems/{system['id']}/endpoints",
        json={"name": "MWL", "service": "MWL", "host": "ris.local", "port": 104, "called_ae": "RIS"},
    ).json()
    store = client.post(
        f"/api/dicom-systems/{system['id']}/endpoints",
        json={"name": "Store", "service": "STORE", "host": "pacs.local", "port": 104, "called_ae": "PACS"},
    ).json()
    channel = client.post(
        "/api/worklist-channels",
        json={"name": "CT", "area_id": area["id"], "modality_code": "CT", "mwl_endpoint_id": mwl["id"], "station_ae_mode": "profile", "station_ae_fixed_value": None, "modality_filter_mode": "profile", "modality_filter_fixed_value": None},
    ).json()
    client.post(
        "/api/modality-profiles",
        json={"name": "CT 1", "description": None, "modality": "CT", "calling_ae": "CT01", "area_id": area["id"], "worklist_channel_id": channel["id"], "store_endpoint_id": store["id"]},
    )

    exported = client.get("/api/configuration/export").json()
    assert exported["format_version"] == 2
    assert exported["sites"] == [{"name": "Nord"}]
    assert exported["areas"] == [{"name": "Radiologie", "site_name": "Nord"}]
    assert exported["dicom_systems"][0]["endpoints"][0]["service"] == "MWL"
    assert exported["worklist_channels"][0]["site_name"] == "Nord"
    assert exported["worklist_channels"][0]["mwl_endpoint_name"] == "MWL"
    assert exported["modality_profiles"][0]["site_name"] == "Nord"
    assert exported["modality_profiles"][0]["store_endpoint_name"] == "Store"
    imported = client.post("/api/configuration/import", json=exported)
    assert imported.status_code == 200
    assert imported.json()["updated_systems"] == 1
    assert imported.json()["updated_profiles"] == 1


def _create_structured_profile_targets(client, modality="CT"):
    system = client.post("/api/dicom-systems", json={"name": f"System {modality}"}).json()
    mwl = client.post(
        f"/api/dicom-systems/{system['id']}/endpoints",
        json={"name": "MWL", "service": "MWL", "host": "ris.local", "port": 104, "called_ae": "RIS"},
    ).json()
    store = client.post(
        f"/api/dicom-systems/{system['id']}/endpoints",
        json={"name": "Store", "service": "STORE", "host": "pacs.local", "port": 11112, "called_ae": "PACS"},
    ).json()
    channel = client.post(
        "/api/worklist-channels",
        json={"name": f"Channel {modality}", "area_id": None, "modality_code": modality, "mwl_endpoint_id": mwl["id"], "station_ae_mode": "profile", "station_ae_fixed_value": None, "modality_filter_mode": "profile", "modality_filter_fixed_value": None},
    ).json()
    return channel, store


@pytest.mark.parametrize("active_service", ["MWL", "STORE"])
def test_structured_profile_supports_exactly_one_active_service(client, active_service):
    channel, store = _create_structured_profile_targets(client)
    response = client.post(
        "/api/modality-profiles",
        json={
            "name": f"{active_service} only",
            "description": None,
            "modality": "CT",
            "calling_ae": "CT01",
            "mwl_enabled": active_service == "MWL",
            "mwl_target_id": None,
            "store_enabled": active_service == "STORE",
            "store_target_id": None,
            "area_id": None,
            "worklist_channel_id": channel["id"] if active_service == "MWL" else None,
            "store_endpoint_id": store["id"] if active_service == "STORE" else None,
        },
    )
    assert response.status_code == 201


def test_profile_rejects_no_active_service_even_with_structured_targets(client):
    channel, store = _create_structured_profile_targets(client)
    response = client.post(
        "/api/modality-profiles",
        json={"name": "No checks", "description": None, "modality": "CT", "calling_ae": "CT01", "mwl_enabled": False, "store_enabled": False, "area_id": None, "worklist_channel_id": channel["id"], "store_endpoint_id": store["id"]},
    )
    assert response.status_code == 422


def test_profile_rejects_multiple_references_for_one_active_service(client):
    channel, _ = _create_structured_profile_targets(client)
    legacy = client.post(
        "/api/targets",
        json={"name": "Legacy", "host": "legacy.local", "mwl_enabled": True, "mwl_port": 104, "mwl_called_ae": "LEGACY", "store_enabled": False, "store_port": None, "store_called_ae": None, "default_calling_ae": "DCMSIM"},
    ).json()
    response = client.post(
        "/api/modality-profiles",
        json={"name": "Ambiguous", "description": None, "modality": "CT", "calling_ae": "CT01", "mwl_enabled": True, "mwl_target_id": legacy["id"], "store_enabled": False, "store_target_id": None, "area_id": None, "worklist_channel_id": channel["id"], "store_endpoint_id": None},
    )
    assert response.status_code == 422


def test_profile_modality_must_match_worklist_channel(client):
    channel, _ = _create_structured_profile_targets(client, modality="CT")
    response = client.post(
        "/api/modality-profiles",
        json={"name": "MR mismatch", "description": None, "modality": "MR", "calling_ae": "MR01", "mwl_enabled": True, "mwl_target_id": None, "store_enabled": False, "store_target_id": None, "area_id": None, "worklist_channel_id": channel["id"], "store_endpoint_id": None},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("change", ["area", "modality"])
def test_referenced_channel_cannot_be_updated_inconsistently(client, change):
    first_site = client.post("/api/sites", json={"name": "First"}).json()
    second_site = client.post("/api/sites", json={"name": "Second"}).json()
    first_area = client.post(
        "/api/areas", json={"name": "Radiology", "site_id": first_site["id"]}
    ).json()
    second_area = client.post(
        "/api/areas", json={"name": "Radiology", "site_id": second_site["id"]}
    ).json()
    channel, _ = _create_structured_profile_targets(client)
    channel = client.put(
        f"/api/worklist-channels/{channel['id']}",
        json={**channel, "area_id": first_area["id"]},
    ).json()
    profile = client.post(
        "/api/modality-profiles",
        json={"name": "CT 1", "description": None, "modality": "CT", "calling_ae": "CT01", "mwl_enabled": True, "mwl_target_id": None, "store_enabled": False, "store_target_id": None, "area_id": first_area["id"], "worklist_channel_id": channel["id"], "store_endpoint_id": None},
    )
    assert profile.status_code == 201
    changed = {
        **channel,
        "area_id": second_area["id"] if change == "area" else first_area["id"],
        "modality_code": "MR" if change == "modality" else "CT",
    }

    response = client.put(f"/api/worklist-channels/{channel['id']}", json=changed)

    assert response.status_code == 409
    preserved = client.get(f"/api/worklist-channels/{channel['id']}").json()
    assert preserved["area_id"] == first_area["id"]
    assert preserved["modality_code"] == "CT"


def test_referenced_channel_allows_consistent_non_identity_update(client):
    channel, _ = _create_structured_profile_targets(client)
    assert client.post(
        "/api/modality-profiles",
        json={"name": "CT 1", "description": None, "modality": "CT", "calling_ae": "CT01", "mwl_enabled": True, "mwl_target_id": None, "store_enabled": False, "store_target_id": None, "area_id": None, "worklist_channel_id": channel["id"], "store_endpoint_id": None},
    ).status_code == 201

    response = client.put(
        f"/api/worklist-channels/{channel['id']}",
        json={**channel, "name": "Renamed CT", "modality_filter_mode": "fixed", "modality_filter_fixed_value": "CT"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed CT"
