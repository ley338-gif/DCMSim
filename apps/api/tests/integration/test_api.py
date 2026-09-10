from app.db.base import Base
from app.db.session import get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_target_crud_and_history(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)
    app.dependency_overrides[get_db] = lambda: (yield from _session(session))
    with TestClient(app) as client:
        payload = {"name": "Test PACS", "host": "127.0.0.1", "mwl_enabled": True, "mwl_port": 11112, "mwl_called_ae": "MWL", "store_enabled": True, "store_port": 11113, "store_called_ae": "PACS", "default_calling_ae": "DCMSIM"}
        created = client.post("/api/targets", json=payload)
        assert created.status_code == 201
        target_id = created.json()["id"]
        assert client.get(f"/api/targets/{target_id}").json()["name"] == "Test PACS"
        payload["name"] = "Updated PACS"
        assert client.put(f"/api/targets/{target_id}", json=payload).json()["name"] == "Updated PACS"
        assert client.delete(f"/api/targets/{target_id}").status_code == 204
        assert client.get(f"/api/targets/{target_id}").status_code == 404
    app.dependency_overrides.clear()


def _session(factory):
    with factory() as db:
        yield db


def test_rejects_bad_target_request():
    with TestClient(app) as client:
        response = client.post("/api/targets", json={"name": "Bad", "host": "bad host", "mwl_enabled": False, "store_enabled": False, "default_calling_ae": "TOO-LONG-AE-TITLE"})
        assert response.status_code == 422

