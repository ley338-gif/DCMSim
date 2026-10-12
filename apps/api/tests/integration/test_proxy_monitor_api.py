from unittest.mock import patch

import httpx
import pytest
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.mark.asyncio
async def test_proxy_identity_requires_trusted_source_and_attaches_user_to_history(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'auth.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    def get_test_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = get_test_db
    monkeypatch.setattr(settings, "proxy_auth_enabled", True)
    monkeypatch.setattr(settings, "proxy_auth_required", False)
    monkeypatch.setattr(settings, "trusted_proxies", "127.0.0.1")
    monkeypatch.setattr(settings, "proxy_user_header", "X-Forwarded-User")
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=("192.0.2.10", 1234)), base_url="http://test") as client:
            assert (await client.get("/api/session", headers={"X-Forwarded-User": "alice"})).json() == {"username": None}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=("127.0.0.1", 1234)), base_url="http://test") as client:
            assert (await client.get("/api/session", headers={"X-Forwarded-User": "alice"})).json() == {"username": "alice"}
            with patch("app.api.routes.echo", return_value={"success": True, "status": "0x0000", "duration_ms": 1}):
                response = await client.post("/api/dicom/echo", headers={"X-Forwarded-User": "alice"}, json={"host": "127.0.0.1", "port": 104, "called_ae": "PACS", "calling_ae": "DCMSIM"})
            assert response.status_code == 200
            history = (await client.get("/api/test-runs/search", headers={"X-Forwarded-User": "alice"}, params={"username": "alice"})).json()
            assert history["total"] == 1
            assert history["items"][0]["username"] == "alice"
            assert "alice" in (await client.get("/api/test-runs/export.csv", headers={"X-Forwarded-User": "alice"}, params={"username": "alice"})).text
            assert (await client.get("/api/test-runs/search", params={"username": "bob"})).json()["total"] == 0
        monkeypatch.setattr(settings, "proxy_auth_required", True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=("127.0.0.1", 1234)), base_url="http://test") as client:
            assert (await client.get("/api/session")).status_code == 401
            assert (await client.get("/api/session", headers={"X-Forwarded-User": "alice"})).status_code == 200
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=("192.0.2.10", 1234)), base_url="http://test") as client:
            assert (await client.get("/api/session", headers={"X-Forwarded-User": "alice"})).status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_monitor_export_import_and_old_v2_preserves_new_fields(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'monitor.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    def get_test_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = get_test_db
    monkeypatch.setattr(settings, "proxy_auth_required", False)
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            system = (await client.post("/api/dicom-systems", json={"name": "RIS"})).json()
            endpoint = (await client.post(f"/api/dicom-systems/{system['id']}/endpoints", json={"name": "MWL Radiologie", "service": "MWL", "host": "ris.local", "port": 11112, "called_ae": "RIS", "monitored": True, "monitor_calling_ae": "DCMSIM", "monitor_window": "07:00-18:00", "monitor_min_count": 1})).json()
            assert endpoint["monitored"] is True
            exported = (await client.get("/api/configuration/export")).json()
            assert exported["format_version"] == 3
            assert exported["dicom_systems"][0]["endpoints"][0]["monitor_window"] == "07:00-18:00"
            assert (await client.post("/api/configuration/import", json=exported)).status_code == 200
            old = {**exported, "format_version": 2}
            for value in old["dicom_systems"][0]["endpoints"]:
                for key in ("monitored", "monitor_calling_ae", "monitor_window", "monitor_min_count"):
                    value.pop(key)
            assert (await client.post("/api/configuration/import", json=old)).status_code == 200
            current = (await client.get(f"/api/dicom-endpoints/{endpoint['id']}")).json()
            assert current["monitored"] is True
            assert current["monitor_min_count"] == 1
    finally:
        app.dependency_overrides.clear()
