import sqlite3
from datetime import UTC, datetime, timedelta

import pytest
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import TestRun as RunModel
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def client(tmp_path):
    database_path = tmp_path / "operations.db"
    engine = create_engine(
        f"sqlite:///{database_path}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def session_override():
        with factory() as database:
            yield database

    app.dependency_overrides[get_db] = session_override
    with TestClient(app) as test_client:
        yield test_client, factory, tmp_path
    app.dependency_overrides.clear()


def configuration():
    return {
        "format_version": 1,
        "targets": [
            {
                "name": "JiveX",
                "host": "127.0.0.1",
                "mwl_enabled": True,
                "mwl_port": 11112,
                "mwl_called_ae": "JIVEXWL",
                "store_enabled": True,
                "store_port": 11113,
                "store_called_ae": "JIVEX",
                "default_calling_ae": "DCMSIM",
            }
        ],
        "modality_profiles": [
            {
                "name": "CT 1",
                "description": None,
                "modality": "CT",
                "calling_ae": "CT01",
                "mwl_enabled": True,
                "mwl_target_name": "JiveX",
                "store_enabled": True,
                "store_target_name": "JiveX",
            }
        ],
    }


def test_configuration_import_is_non_destructive_upsert_and_exports_names(client):
    test_client, _, _ = client
    first = test_client.post("/api/configuration/import", json=configuration())
    assert first.status_code == 200
    assert first.json()["created_targets"] == 1
    assert first.json()["created_profiles"] == 1

    changed = configuration()
    changed["targets"][0]["host"] = "pacs.local"
    second = test_client.post("/api/configuration/import", json=changed)
    assert second.json()["updated_targets"] == 1
    assert second.json()["updated_profiles"] == 1

    exported = test_client.get("/api/configuration/export").json()
    assert exported["format_version"] == 2
    assert exported["dicom_systems"][0]["name"] == "JiveX"
    assert {endpoint["host"] for endpoint in exported["dicom_systems"][0]["endpoints"]} == {
        "pacs.local"
    }
    assert exported["modality_profiles"][0]["worklist_channel_name"] == "CT 1 – Worklist"
    assert exported["modality_profiles"][0]["store_system_name"] == "JiveX"


def test_v1_normalization_bounds_generated_names_and_avoids_truncation_collisions(client):
    test_client, _, _ = client
    payload = configuration()
    target_name = "T" * 120
    payload["targets"][0]["name"] = target_name
    first_profile = {**payload["modality_profiles"][0]}
    first_profile.update(
        name="P" * 119 + "A",
        mwl_target_name=target_name,
        store_target_name=target_name,
    )
    second_profile = {**first_profile, "name": "P" * 119 + "B", "calling_ae": "CT02"}
    payload["modality_profiles"] = [first_profile, second_profile]

    assert test_client.post("/api/configuration/import", json=payload).status_code == 200
    exported = test_client.get("/api/configuration/export").json()
    generated_names = [
        exported["dicom_systems"][0]["name"],
        *(item["name"] for item in exported["dicom_systems"][0]["endpoints"]),
        *(item["name"] for item in exported["worklist_channels"]),
    ]
    assert all(len(name) <= 120 for name in generated_names)
    assert len({item["name"] for item in exported["worklist_channels"]}) == 2

    assert test_client.post("/api/configuration/import", json=payload).status_code == 200
    repeated = test_client.get("/api/configuration/export").json()
    assert [item["name"] for item in repeated["worklist_channels"]] == [
        item["name"] for item in exported["worklist_channels"]
    ]


def test_import_rejects_unknown_referenced_target(client):
    test_client, _, _ = client
    payload = configuration()
    payload["modality_profiles"][0]["store_target_name"] = "Missing"
    assert test_client.post("/api/configuration/import", json=payload).status_code == 422
    assert test_client.get("/api/targets").json() == []


@pytest.mark.parametrize("collection", ["targets", "modality_profiles"])
def test_import_rejects_duplicate_names_without_changing_existing_configuration(client, collection):
    test_client, _, _ = client
    assert test_client.post("/api/configuration/import", json=configuration()).status_code == 200
    before = test_client.get("/api/configuration/export").json()
    payload = configuration()
    payload["targets"][0]["host"] = "changed.local"
    payload[collection].append(payload[collection][0].copy())
    response = test_client.post("/api/configuration/import", json=payload)
    assert response.status_code == 422
    after = test_client.get("/api/configuration/export").json()
    before.pop("exported_at")
    after.pop("exported_at")
    assert after == before


def configuration_v2():
    return {
        "format_version": 2,
        "sites": [{"name": "Nord"}, {"name": "Süd"}],
        "areas": [
            {"name": "Radiologie", "site_name": "Nord"},
            {"name": "Radiologie", "site_name": "Süd"},
        ],
        "dicom_systems": [
            {
                "name": "RIS/PACS",
                "endpoints": [
                    {"name": "MWL", "service": "MWL", "host": "ris.local", "port": 104, "called_ae": "RIS"},
                    {"name": "Store", "service": "STORE", "host": "pacs.local", "port": 11112, "called_ae": "PACS"},
                ],
            }
        ],
        "worklist_channels": [
            {
                "name": "Nord CT",
                "site_name": "Nord",
                "area_name": "Radiologie",
                "modality_code": "CT",
                "mwl_system_name": "RIS/PACS",
                "mwl_endpoint_name": "MWL",
                "station_ae_mode": "profile",
                "station_ae_fixed_value": None,
                "modality_filter_mode": "fixed",
                "modality_filter_fixed_value": "CT",
            }
        ],
        "modality_profiles": [
            {
                "name": "CT 1",
                "description": None,
                "modality": "CT",
                "calling_ae": "CT01",
                "site_name": "Nord",
                "area_name": "Radiologie",
                "worklist_channel_name": "Nord CT",
                "store_system_name": "RIS/PACS",
                "store_endpoint_name": "Store",
            }
        ],
    }


def test_v2_import_resolves_scoped_names_and_rolls_back_on_missing_reference(client):
    test_client, _, _ = client
    payload = configuration_v2()
    assert test_client.post("/api/configuration/import", json=payload).status_code == 200
    before = test_client.get("/api/configuration/export").json()
    before.pop("exported_at")
    assert before["areas"] == [
        {"name": "Radiologie", "site_name": "Nord"},
        {"name": "Radiologie", "site_name": "Süd"},
    ]

    broken = configuration_v2()
    broken["dicom_systems"][0]["endpoints"][0]["host"] = "changed.local"
    broken["sites"].append({"name": "Darf nicht bleiben"})
    broken["modality_profiles"][0]["store_endpoint_name"] = "Fehlt"
    response = test_client.post("/api/configuration/import", json=broken)
    assert response.status_code == 422
    after = test_client.get("/api/configuration/export").json()
    after.pop("exported_at")
    assert after == before


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("station_ae_fixed_value", None),
        ("station_ae_fixed_value", "INVALID/AE"),
        ("modality_filter_fixed_value", None),
    ],
)
def test_v2_import_rejects_invalid_fixed_worklist_filters(client, field, value):
    test_client, _, _ = client
    payload = configuration_v2()
    channel = payload["worklist_channels"][0]
    if field.startswith("station_ae"):
        channel["station_ae_mode"] = "fixed"
    else:
        channel["modality_filter_mode"] = "fixed"
    channel[field] = value

    response = test_client.post("/api/configuration/import", json=payload)

    assert response.status_code == 422
    assert test_client.get("/api/dicom-systems").json() == []


def test_v2_import_normalizes_fixed_worklist_filters_like_crud(client):
    test_client, _, _ = client
    payload = configuration_v2()
    channel = payload["worklist_channels"][0]
    channel.update(
        station_ae_mode="fixed",
        station_ae_fixed_value=" ct-room ",
        modality_filter_mode="fixed",
        modality_filter_fixed_value=" ct ",
    )

    response = test_client.post("/api/configuration/import", json=payload)

    assert response.status_code == 200
    imported = test_client.get("/api/worklist-channels").json()[0]
    assert imported["station_ae_fixed_value"] == "CT-ROOM"
    assert imported["modality_filter_fixed_value"] == "CT"


@pytest.mark.parametrize(("endpoint_index", "service"), [(0, "STORE"), (1, "QR")])
def test_v2_import_cannot_change_service_of_referenced_endpoint(
    client, endpoint_index, service
):
    test_client, _, _ = client
    assert test_client.post("/api/configuration/import", json=configuration_v2()).status_code == 200
    before = test_client.get("/api/configuration/export").json()
    before.pop("exported_at")
    changed = configuration_v2()
    changed["dicom_systems"][0]["endpoints"][endpoint_index]["service"] = service

    response = test_client.post("/api/configuration/import", json=changed)

    assert response.status_code == 409
    after = test_client.get("/api/configuration/export").json()
    after.pop("exported_at")
    assert after == before


@pytest.mark.parametrize("invalid_profile", ["no_service", "modality_mismatch"])
def test_v2_import_rejects_invalid_profile_service_configuration(client, invalid_profile):
    test_client, _, _ = client
    payload = configuration_v2()
    profile = payload["modality_profiles"][0]
    if invalid_profile == "no_service":
        profile.update(
            worklist_channel_name=None,
            store_system_name=None,
            store_endpoint_name=None,
        )
    else:
        profile["modality"] = "MR"

    response = test_client.post("/api/configuration/import", json=payload)

    assert response.status_code == 422
    assert test_client.get("/api/modality-profiles").json() == []


def test_history_retention_only_removes_old_runs(client):
    test_client, factory, _ = client
    with factory() as database:
        database.add_all(
            [
                RunModel(
                    test_type="dicom_echo", duration_ms=1, success=True, status="0x0000",
                    result_json={}, started_at=datetime.now(UTC) - timedelta(days=100),
                ),
                RunModel(
                    test_type="dicom_echo", duration_ms=1, success=True, status="0x0000",
                    result_json={}, started_at=datetime.now(UTC),
                ),
            ]
        )
        database.commit()
    response = test_client.post("/api/maintenance/history-retention", json={"days": 90})
    assert response.json()["deleted_count"] == 1
    assert len(test_client.get("/api/test-runs").json()) == 1


def test_database_backup_is_a_readable_sqlite_copy(client, tmp_path):
    test_client, _, _ = client
    test_client.post("/api/configuration/import", json=configuration())
    response = test_client.get("/api/maintenance/database-backup")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.sqlite3"
    backup_path = tmp_path / "download.sqlite3"
    backup_path.write_bytes(response.content)
    with sqlite3.connect(backup_path) as connection:
        assert connection.execute("select count(*) from targets").fetchone()[0] == 1
