import app.api.routes as api_routes
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_study_query_is_returned_but_patient_results_are_not_persisted(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'study-query.db'}", connect_args={"check_same_thread": False}
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def session_override():
        with factory() as database:
            yield database

    def fake_find(_endpoint, query):
        assert query.QueryRetrieveLevel == "STUDY"
        assert query.StudyDate == "20260911"
        return {
            "success": True,
            "status": "0x0000",
            "duration_ms": 12,
            "count": 1,
            "entries": [{"patient_name": "DCMSIM^PRIVATE", "patient_id": "PRIVATE-1"}],
        }

    monkeypatch.setattr(api_routes, "find_studies", fake_find)
    app.dependency_overrides[get_db] = session_override
    payload = {
        "host": "127.0.0.1",
        "port": 11112,
        "called_ae": "PACSQR",
        "calling_ae": "DCMSIM",
        "filters": {"study_date": "2026-09-11"},
    }
    with TestClient(app) as client:
        response = client.post("/api/dicom/studies", json=payload)
        assert response.status_code == 200
        assert response.json()["entries"][0]["patient_id"] == "PRIVATE-1"
        run = client.get("/api/test-runs").json()[0]
        assert run["test_type"] == "qr_find"
        assert "entries" not in run["result_json"]
        assert "PRIVATE-1" not in str(run)
        assert client.post(
            "/api/dicom/studies", json={**payload, "filters": {}}
        ).status_code == 422
    app.dependency_overrides.clear()
