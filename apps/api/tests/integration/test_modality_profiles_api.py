import app.api.routes as api_routes
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
        f"sqlite:///{tmp_path / 'profiles.db'}", connect_args={"check_same_thread": False}
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


def target_payload(name="JiveX Produktion", **overrides):
    return {
        "name": name,
        "host": "127.0.0.1",
        "mwl_enabled": True,
        "mwl_port": 11112,
        "mwl_called_ae": "JIVEXWL",
        "store_enabled": True,
        "store_port": 11113,
        "store_called_ae": "JIVEX",
        "default_calling_ae": "DCMSIM",
        **overrides,
    }


def profile_payload(target_id, **overrides):
    return {
        "name": "Aplio 300 – Sono 2",
        "description": "Ultrasound room 2",
        "modality": "US",
        "calling_ae": "APLIO02",
        "mwl_enabled": True,
        "mwl_target_id": target_id,
        "store_enabled": True,
        "store_target_id": target_id,
        **overrides,
    }


def test_modality_profile_crud(client):
    target_id = client.post("/api/targets", json=target_payload()).json()["id"]
    created = client.post("/api/modality-profiles", json=profile_payload(target_id))
    assert created.status_code == 201
    profile_id = created.json()["id"]
    assert client.get("/api/modality-profiles").json()[0]["calling_ae"] == "APLIO02"

    updated = client.put(
        f"/api/modality-profiles/{profile_id}",
        json=profile_payload(target_id, name="Aplio 300 – Sono 3", calling_ae="APLIO03"),
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Aplio 300 – Sono 3"
    assert client.delete(f"/api/modality-profiles/{profile_id}").status_code == 204
    assert client.get(f"/api/modality-profiles/{profile_id}").status_code == 404


def test_target_delete_sets_profile_references_to_null(client):
    target_id = client.post("/api/targets", json=target_payload()).json()["id"]
    profile = client.post("/api/modality-profiles", json=profile_payload(target_id)).json()

    assert client.delete(f"/api/targets/{target_id}").status_code == 204
    stored = client.get(f"/api/modality-profiles/{profile['id']}").json()
    assert stored["mwl_target_id"] is None
    assert stored["store_target_id"] is None


@pytest.mark.parametrize(
    ("field", "value"),
    [("calling_ae", "AE/TITLE"), ("calling_ae", "A" * 17), ("modality", "ECG")],
)
def test_profile_rejects_invalid_calling_ae_and_modality(client, field, value):
    target_id = client.post("/api/targets", json=target_payload()).json()["id"]
    response = client.post(
        "/api/modality-profiles", json=profile_payload(target_id, **{field: value})
    )
    assert response.status_code == 422


def test_profile_requires_existing_service_targets(client):
    missing = client.post("/api/modality-profiles", json=profile_payload(9999))
    assert missing.status_code == 422

    target_id = client.post(
        "/api/targets",
        json=target_payload(
            "MWL only",
            store_enabled=False,
            store_port=None,
            store_called_ae=None,
        ),
    ).json()["id"]
    unsupported = client.post("/api/modality-profiles", json=profile_payload(target_id))
    assert unsupported.status_code == 422


def test_profile_requires_target_for_each_enabled_service(client):
    target_id = client.post("/api/targets", json=target_payload()).json()["id"]
    payload = profile_payload(target_id)
    payload["mwl_target_id"] = None
    response = client.post("/api/modality-profiles", json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize("active_service", ["mwl", "store"])
def test_legacy_profile_supports_exactly_one_active_service(client, active_service):
    target_id = client.post("/api/targets", json=target_payload()).json()["id"]
    payload = profile_payload(
        target_id,
        name=f"{active_service} only",
        mwl_enabled=active_service == "mwl",
        mwl_target_id=target_id if active_service == "mwl" else None,
        store_enabled=active_service == "store",
        store_target_id=target_id if active_service == "store" else None,
    )
    assert client.post("/api/modality-profiles", json=payload).status_code == 201


def test_modality_check_endpoint_uses_profile_and_transfer_syntax(client, monkeypatch):
    target_id = client.post("/api/targets", json=target_payload()).json()["id"]
    profile_id = client.post(
        "/api/modality-profiles", json=profile_payload(target_id)
    ).json()["id"]

    def check(_database, profile, transfer_syntax):
        return {
            "success": True,
            "status": "PASS",
            "profile_id": profile.id,
            "transfer_syntax": transfer_syntax,
        }

    monkeypatch.setattr(api_routes, "run_modality_check", check)
    response = client.post(
        f"/api/modality-profiles/{profile_id}/check",
        json={"transfer_syntax": "implicit_vr_little_endian"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "status": "PASS",
        "profile_id": profile_id,
        "transfer_syntax": "implicit_vr_little_endian",
    }
