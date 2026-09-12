from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Target
from app.services.history import record_run
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_history_search_paginates_and_filters_server_side(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'history-query.db'}",
        connect_args={"check_same_thread": False},
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    with factory() as db:
        target = Target(
            name="PACS Radiologie",
            host="127.0.0.1",
            mwl_enabled=False,
            store_enabled=True,
            store_port=11112,
            store_called_ae="PACS",
            qr_enabled=False,
            default_calling_ae="DCMSIM",
        )
        db.add(target)
        db.commit()
        record_run(
            db,
            "dicom_store",
            {"target_id": target.id},
            {"success": True, "status": "0x0000", "duration_ms": 12},
        )
        record_run(
            db,
            "dicom_echo",
            {"host": "10.20.30.40", "port": 104, "called_ae": "ARCHIVE", "calling_ae": "DCMSIM"},
            {"success": False, "code": "DICOM_TIMEOUT", "duration_ms": 25},
        )

    def session_override():
        with factory() as database:
            yield database

    app.dependency_overrides[get_db] = session_override
    try:
        with TestClient(app) as client:
            page = client.get("/api/test-runs/search?limit=1&offset=0").json()
            assert page["total"] == 2
            assert len(page["items"]) == 1
            assert page["limit"] == 1

            failed = client.get("/api/test-runs/search?success=false").json()
            assert failed["total"] == 1
            assert failed["items"][0]["status"] == "DICOM_TIMEOUT"

            target_match = client.get("/api/test-runs/search?search=Radiologie").json()
            assert target_match["total"] == 1
            assert target_match["items"][0]["test_type"] == "dicom_store"

            host_match = client.get("/api/test-runs/search?search=10.20.30.40").json()
            assert host_match["total"] == 1
            assert host_match["items"][0]["test_type"] == "dicom_echo"
    finally:
        app.dependency_overrides.clear()


def test_history_csv_exports_only_sanitized_technical_fields(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'history-export.db'}",
        connect_args={"check_same_thread": False},
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    with factory() as db:
        record_run(
            db,
            "mwl_find",
            {"host": "127.0.0.1", "port": 11112, "called_ae": "MWL", "calling_ae": "DCMSIM"},
            {
                "success": True,
                "status": "0x0000",
                "duration_ms": 9,
                "count": 1,
                "entries": [{"patient_name": "PRIVATE^PATIENT", "patient_id": "PRIVATE-1"}],
                "active_filters": {"patient_id": "PRIVATE-1"},
            },
        )
        record_run(
            db,
            "modality_check",
            {},
            {"success": True, "status": "success", "duration_ms": 4, "profile_name": "=2+2"},
        )

    def session_override():
        with factory() as database:
            yield database

    app.dependency_overrides[get_db] = session_override
    try:
        with TestClient(app) as client:
            response = client.get("/api/test-runs/export.csv")
            assert response.status_code == 200
            assert response.content.startswith(b"\xef\xbb\xbf")
            assert "PRIVATE" not in response.text
            assert "'=2+2" in response.text
            assert "Dauer ms" in response.text
            assert response.headers["content-disposition"].endswith('.csv"')
    finally:
        app.dependency_overrides.clear()
