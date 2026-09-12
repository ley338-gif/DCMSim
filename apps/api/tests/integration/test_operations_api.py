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
    assert exported["format_version"] == 1
    assert exported["targets"][0]["host"] == "pacs.local"
    assert exported["modality_profiles"][0]["mwl_target_name"] == "JiveX"


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
    assert after["targets"] == before["targets"]
    assert after["modality_profiles"] == before["modality_profiles"]


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
