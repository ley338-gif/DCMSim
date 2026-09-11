import app.api.routes as api_routes
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_worklist_results_are_returned_but_patient_data_is_not_persisted(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'history-privacy.db'}",
        connect_args={"check_same_thread": False},
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def session_override():
        with factory() as database:
            yield database

    monkeypatch.setattr(
        api_routes,
        "find_worklist",
        lambda _endpoint, _query: {
            "success": True,
            "status": "0x0000",
            "duration_ms": 12,
            "count": 1,
            "entries": [{"patient_name": "PRIVATE^PATIENT", "patient_id": "PRIVATE-1"}],
        },
    )
    app.dependency_overrides[get_db] = session_override
    payload = {
        "host": "127.0.0.1",
        "port": 11112,
        "called_ae": "MWL",
        "calling_ae": "DCMSIM",
        "broad": False,
        "filters": {"date": "2026-09-12", "patient_id": "PRIVATE-1"},
    }
    try:
        with TestClient(app) as client:
            response = client.post("/api/dicom/mwl", json=payload)
            assert response.status_code == 200
            assert response.json()["entries"][0]["patient_id"] == "PRIVATE-1"
            run = client.get("/api/test-runs").json()[0]
            assert run["result_json"]["count"] == 1
            assert "entries" not in run["result_json"]
            assert "active_filters" not in run["result_json"]
            assert "PRIVATE-1" not in str(run)
    finally:
        app.dependency_overrides.clear()
