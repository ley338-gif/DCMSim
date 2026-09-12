from datetime import UTC, datetime

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Target
from app.models import TestRun as RunModel
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
            {"target_id": target.id, "host": "127.0.0.1", "port": 11112, "called_ae": "PACS", "calling_ae": "DCMSIM"},
            {"success": True, "status": "0x0000", "duration_ms": 12, "target_name": "PACS Radiologie"},
        )
        record_run(
            db,
            "dicom_echo",
            {"host": "10.20.30.40", "port": 104, "called_ae": "ARCHIVE", "calling_ae": "DCMSIM"},
            {"success": False, "code": "DICOM_TIMEOUT", "duration_ms": 25},
        )
        target.name = "Umbenanntes Ziel"
        target.host = "192.0.2.2"
        db.commit()

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
            snapshot = target_match["items"][0]["target_snapshot_json"]
            assert snapshot == {"name": "PACS Radiologie", "host": "127.0.0.1", "port": 11112, "called_ae": "PACS", "calling_ae": "DCMSIM"}
            assert client.get(f"/api/test-runs/{target_match['items'][0]['id']}").json()["target_snapshot_json"] == snapshot
            csv = client.get("/api/test-runs/export.csv").text
            assert "PACS Radiologie;127.0.0.1;DCMSIM;PACS" in csv
            assert "Umbenanntes Ziel" not in csv
            assert client.delete(f"/api/targets/{target.id}").status_code == 204
            deleted_target_run = client.get(f"/api/test-runs/{target_match['items'][0]['id']}").json()
            assert deleted_target_run["target_id"] is None
            assert deleted_target_run["target_snapshot_json"] == snapshot

            host_match = client.get("/api/test-runs/search?search=10.20.30.40").json()
            assert host_match["total"] == 1
            assert host_match["items"][0]["test_type"] == "dicom_echo"
    finally:
        app.dependency_overrides.clear()


def test_history_date_range_uses_timezone_aware_half_open_bounds_for_list_and_csv(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'history-dates.db'}")
    factory = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    with factory() as db:
        for status, instant in (
            ("BEFORE", datetime(2026, 9, 11, 21, 59, tzinfo=UTC)),
            ("START", datetime(2026, 9, 11, 22, 0, tzinfo=UTC)),
            ("END", datetime(2026, 9, 12, 21, 59, tzinfo=UTC)),
            ("AFTER", datetime(2026, 9, 12, 22, 0, tzinfo=UTC)),
        ):
            db.add(RunModel(test_type="dicom_echo", started_at=instant, duration_ms=1, success=True, status=status, result_json={"success": True}))
        db.commit()

    def session_override():
        with factory() as database:
            yield database

    app.dependency_overrides[get_db] = session_override
    try:
        with TestClient(app) as client:
            bounds = {"started_from": "2026-09-12T00:00:00+02:00", "started_before": "2026-09-13T00:00:00+02:00"}
            page = client.get("/api/test-runs/search", params=bounds)
            assert page.status_code == 200
            assert page.json()["total"] == 2
            assert {item["status"] for item in page.json()["items"]} == {"START", "END"}
            csv = client.get("/api/test-runs/export.csv", params=bounds)
            assert csv.status_code == 200
            assert "START" in csv.text and "END" in csv.text
            assert "BEFORE" not in csv.text and "AFTER" not in csv.text
            for path in ("/api/test-runs/search", "/api/test-runs/export.csv"):
                assert client.get(path, params={"started_from": "2026-09-12T00:00:00"}).status_code == 422
                assert client.get(path, params={"started_from": bounds["started_before"], "started_before": bounds["started_from"]}).status_code == 422
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


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
