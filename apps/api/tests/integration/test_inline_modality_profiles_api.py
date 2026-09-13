import threading
from concurrent.futures import ThreadPoolExecutor

import app.services.modality_profiles as modality_profiles
import pytest
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import ModalityProfile, Target, WorklistChannel
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def configured_client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'inline-profiles.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def session_override():
        with factory() as database:
            yield database

    app.dependency_overrides[get_db] = session_override
    with TestClient(app) as client:
        yield client, factory
    app.dependency_overrides.clear()


def topology(client):
    site = client.post("/api/sites", json={"name": "Nord"}).json()
    area = client.post(
        "/api/areas", json={"name": "Radiologie", "site_id": site["id"]}
    ).json()
    system = client.post("/api/dicom-systems", json={"name": "RIS/PACS"}).json()
    endpoints = {}
    for name, service in (("MWL", "MWL"), ("Store", "STORE"), ("Query", "QR")):
        endpoints[service] = client.post(
            f"/api/dicom-systems/{system['id']}/endpoints",
            json={
                "name": name,
                "service": service,
                "host": "dicom.local",
                "port": 104,
                "called_ae": name.upper(),
            },
        ).json()
    return area, endpoints


def payload(area_id, endpoints, **changes):
    value = {
        "name": "CT 1",
        "description": "Raum 1",
        "modality": "CT",
        "calling_ae": "CT01",
        "area_id": area_id,
        "mwl_enabled": True,
        "mwl_endpoint_id": endpoints["MWL"]["id"],
        "station_ae_mode": "profile",
        "station_ae_fixed_value": None,
        "modality_filter_mode": "fixed",
        "modality_filter_fixed_value": "CT",
        "store_enabled": True,
        "store_endpoint_id": endpoints["STORE"]["id"],
    }
    value.update(changes)
    return value


def test_inline_create_resolves_configuration_and_reuses_complete_semantic_tuple(
    configured_client,
):
    client, factory = configured_client
    area, endpoints = topology(client)

    first = client.post(
        "/api/modality-profiles/inline", json=payload(area["id"], endpoints)
    )
    second = client.post(
        "/api/modality-profiles/inline",
        json=payload(area["id"], endpoints, name="CT 2", calling_ae="CT02"),
    )

    assert first.status_code == second.status_code == 201
    assert first.json()["mwl_endpoint_id"] == endpoints["MWL"]["id"]
    assert first.json()["station_ae_mode"] == "profile"
    assert first.json()["modality_filter_fixed_value"] == "CT"
    assert first.json()["worklist_channel_id"] == second.json()["worklist_channel_id"]
    with factory() as db:
        channels = db.scalars(select(WorklistChannel)).all()
        assert len(channels) == 1
        assert channels[0].is_internal is True
        assert channels[0].name.startswith("__dcmsim_inline_")


def test_inline_update_never_rewires_shared_channel_and_collects_internal_orphan(
    configured_client,
):
    client, factory = configured_client
    area, endpoints = topology(client)
    first = client.post(
        "/api/modality-profiles/inline", json=payload(area["id"], endpoints)
    ).json()
    second = client.post(
        "/api/modality-profiles/inline",
        json=payload(area["id"], endpoints, name="CT 2", calling_ae="CT02"),
    ).json()

    changed = client.put(
        f"/api/modality-profiles/{first['id']}/inline",
        json=payload(
            area["id"],
            endpoints,
            station_ae_mode="fixed",
            station_ae_fixed_value="ROOM_A",
        ),
    )

    assert changed.status_code == 200
    assert changed.json()["worklist_channel_id"] != second["worklist_channel_id"]
    original = client.get(
        f"/api/worklist-channels/{second['worklist_channel_id']}"
    ).json()
    assert original["station_ae_mode"] == "profile"
    assert original["station_ae_fixed_value"] is None

    assert client.delete(f"/api/modality-profiles/{second['id']}").status_code == 204
    with factory() as db:
        assert db.get(WorklistChannel, second["worklist_channel_id"]) is None
        assert db.get(WorklistChannel, changed.json()["worklist_channel_id"]) is not None


def test_inline_update_and_delete_never_collect_manual_channel(configured_client):
    client, factory = configured_client
    area, endpoints = topology(client)
    manual = client.post(
        "/api/worklist-channels",
        json={
            "name": "Manuell verwaltet",
            "area_id": area["id"],
            "modality_code": "CT",
            "mwl_endpoint_id": endpoints["MWL"]["id"],
            "station_ae_mode": "profile",
            "station_ae_fixed_value": None,
            "modality_filter_mode": "fixed",
            "modality_filter_fixed_value": "CT",
        },
    ).json()
    profile = client.post(
        "/api/modality-profiles/inline", json=payload(area["id"], endpoints)
    ).json()
    assert profile["worklist_channel_id"] == manual["id"]

    assert client.delete(f"/api/modality-profiles/{profile['id']}").status_code == 204
    with factory() as db:
        channel = db.get(WorklistChannel, manual["id"])
        assert channel is not None
        assert channel.is_internal is False


def test_inline_validation_is_transactional(configured_client):
    client, factory = configured_client
    area, endpoints = topology(client)
    invalid = (
        payload(area["id"], endpoints, mwl_endpoint_id=endpoints["STORE"]["id"]),
        payload(area["id"], endpoints, store_endpoint_id=endpoints["MWL"]["id"]),
        payload(area["id"], endpoints, mwl_enabled=False, mwl_endpoint_id=None,
                store_enabled=False, store_endpoint_id=None),
        payload(area["id"], endpoints, station_ae_mode="fixed", station_ae_fixed_value=None),

        payload(area["id"], endpoints, modality_filter_mode="fixed", modality_filter_fixed_value="BAD"),
    )
    for item in invalid:
        assert client.post("/api/modality-profiles/inline", json=item).status_code == 422
    with factory() as db:
        assert db.scalar(select(ModalityProfile.id)) is None
        assert db.scalar(select(WorklistChannel.id)) is None


def test_inline_profile_requires_channel_area_and_modality_identity(configured_client):
    client, factory = configured_client
    area, endpoints = topology(client)
    second_site = client.post("/api/sites", json={"name": "Süd"}).json()
    second_area = client.post(
        "/api/areas", json={"name": "Radiologie", "site_id": second_site["id"]}
    ).json()
    manual = client.post(
        "/api/worklist-channels",
        json={
            "name": "Andere Zuordnung",
            "area_id": second_area["id"],
            "modality_code": "MR",
            "mwl_endpoint_id": endpoints["MWL"]["id"],
            "station_ae_mode": "profile",
            "station_ae_fixed_value": None,
            "modality_filter_mode": "profile",
            "modality_filter_fixed_value": None,
        },
    )
    assert manual.status_code == 201
    response = client.post(
        "/api/modality-profiles",
        json={
            "name": "Mismatch",
            "description": None,
            "modality": "CT",
            "calling_ae": "CT01",
            "mwl_enabled": True,
            "mwl_target_id": None,
            "store_enabled": False,
            "store_target_id": None,
            "area_id": area["id"],
            "worklist_channel_id": manual.json()["id"],
            "store_endpoint_id": None,
        },
    )
    assert response.status_code == 422
    with factory() as db:
        assert db.scalar(select(ModalityProfile.id)) is None


def test_inline_update_preserves_enabled_legacy_fallbacks_and_clears_disabled_ones(
    configured_client,
):
    client, factory = configured_client
    area, endpoints = topology(client)
    with factory() as db:
        target = Target(
            name="Legacy PACS", host="legacy.local", mwl_enabled=True,
            mwl_port=104, mwl_called_ae="LEGACY_MWL", store_enabled=True,
            store_port=11112, store_called_ae="LEGACY_STORE", qr_enabled=False,
            qr_port=None, qr_called_ae=None, default_calling_ae="DCMSIM",
        )
        db.add(target)
        db.flush()
        profile = ModalityProfile(
            name="Fallback", description=None, modality="CT", calling_ae="CT01",
            mwl_enabled=True, mwl_target_id=target.id, store_enabled=True,
            store_target_id=target.id,
        )
        db.add(profile)
        db.commit()
        profile_id, target_id = profile.id, target.id

    response = client.put(
        f"/api/modality-profiles/{profile_id}/inline",
        json=payload(area["id"], endpoints),
    )
    assert response.status_code == 200
    with factory() as db:
        updated = db.get(ModalityProfile, profile_id)
        assert updated.mwl_target_id == target_id
        assert updated.store_target_id == target_id

    disabled = client.put(
        f"/api/modality-profiles/{profile_id}/inline",
        json=payload(area["id"], endpoints, mwl_enabled=False, mwl_endpoint_id=None),
    )
    assert disabled.status_code == 200
    with factory() as db:
        updated = db.get(ModalityProfile, profile_id)
        assert updated.mwl_target_id is None
        assert updated.store_target_id == target_id


@pytest.mark.parametrize("legacy_service", ["MWL", "STORE"])
def test_inline_update_handles_legacy_and_structured_sources_per_service(
    configured_client, legacy_service
):
    client, factory = configured_client
    area, endpoints = topology(client)
    with factory() as db:
        target = Target(
            name=f"Legacy {legacy_service}", host="legacy.local", mwl_enabled=True,
            mwl_port=104, mwl_called_ae="LEGACY_MWL", store_enabled=True,
            store_port=11112, store_called_ae="LEGACY_STORE", qr_enabled=False,
            qr_port=None, qr_called_ae=None, default_calling_ae="DCMSIM",
        )
        db.add(target)
        db.commit()
        target_id = target.id

    mixed = payload(area["id"], endpoints)
    if legacy_service == "MWL":
        mixed.update(mwl_endpoint_id=None, mwl_target_id=target_id)
    else:
        mixed.update(store_endpoint_id=None, store_target_id=target_id)
    created = client.post("/api/modality-profiles/inline", json=mixed)

    assert created.status_code == 201, created.text
    body = created.json()
    if legacy_service == "MWL":
        assert body["mwl_target_id"] == target_id
        assert body["mwl_endpoint_id"] is None
        assert body["store_endpoint_id"] == endpoints["STORE"]["id"]
    else:
        assert body["store_target_id"] == target_id
        assert body["store_endpoint_id"] is None
        assert body["mwl_endpoint_id"] == endpoints["MWL"]["id"]


@pytest.mark.parametrize(
    "changes",
    [
        {"mwl_target_id": 99},
        {"mwl_endpoint_id": None, "mwl_target_id": None},
        {"store_target_id": 99},
        {"store_endpoint_id": None, "store_target_id": None},
    ],
)
def test_inline_payload_requires_exactly_one_source_per_enabled_service(
    configured_client, changes
):
    client, _ = configured_client
    area, endpoints = topology(client)
    response = client.post(
        "/api/modality-profiles/inline", json=payload(area["id"], endpoints, **changes)
    )
    assert response.status_code == 422


def test_concurrent_inline_profiles_atomically_reuse_one_internal_channel(
    configured_client, monkeypatch
):
    client, factory = configured_client
    area, endpoints = topology(client)
    barrier = threading.Barrier(2)
    original_name = modality_profiles._internal_name

    def synchronized_name(db, semantic):
        name = original_name(db, semantic)
        barrier.wait(timeout=5)
        return name

    monkeypatch.setattr(modality_profiles, "_internal_name", synchronized_name)

    def create(index):
        return client.post(
            "/api/modality-profiles/inline",
            json=payload(
                area["id"], endpoints, name=f"CT {index}", calling_ae=f"CT{index:02d}"
            ),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(create, (1, 2)))

    assert [response.status_code for response in responses] == [201, 201]
    assert responses[0].json()["worklist_channel_id"] == responses[1].json()[
        "worklist_channel_id"
    ]
    with factory() as db:
        assert len(db.scalars(select(WorklistChannel)).all()) == 1
