from datetime import UTC, datetime, timedelta, timezone

from app.core.dates import as_utc
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import ModalityProfile, Target
from app.models import TestRun as RunModel
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_utc_timestamp_helper_preserves_instant():
    instant = datetime(2026, 9, 12, 10, 0, tzinfo=UTC)
    assert as_utc(instant.replace(tzinfo=None)) == instant
    assert as_utc(instant.astimezone(timezone(timedelta(hours=2)))) == instant


def test_sqlite_timestamps_are_explicitly_utc_in_api_and_csv(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'timestamps.db'}")
    factory = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    instant = datetime(2026, 9, 12, 10, 0, tzinfo=UTC)
    with factory() as db:
        target = Target(
            name="Test PACS",
            host="127.0.0.1",
            mwl_enabled=True,
            mwl_port=11112,
            mwl_called_ae="TESTMWL",
            store_enabled=False,
            qr_enabled=False,
            default_calling_ae="DCMSIM",
            created_at=instant,
            updated_at=instant,
        )
        db.add(target)
        db.flush()
        db.add_all(
            [
                ModalityProfile(
                    name="Testprofil",
                    modality="CT",
                    calling_ae="DCMSIM",
                    mwl_enabled=True,
                    mwl_target_id=target.id,
                    store_enabled=False,
                    created_at=instant,
                    updated_at=instant,
                ),
                RunModel(
                    test_type="dicom_echo",
                    target_id=target.id,
                    target_snapshot_json={
                        "host": target.host,
                        "port": target.mwl_port,
                        "called_ae": target.mwl_called_ae,
                        "calling_ae": target.default_calling_ae,
                    },
                    started_at=instant,
                    duration_ms=9,
                    success=True,
                    status="0x0000",
                    result_json={"success": True},
                ),
            ]
        )
        db.commit()

    def session_override():
        with factory() as db:
            yield db

    def assert_utc(value: str):
        assert datetime.fromisoformat(value.replace("Z", "+00:00")) == instant
        assert value.endswith(("Z", "+00:00"))

    app.dependency_overrides[get_db] = session_override
    try:
        with TestClient(app) as client:
            target_json = client.get("/api/targets").json()[0]
            profile_json = client.get("/api/modality-profiles").json()[0]
            run_json = client.get("/api/test-runs").json()[0]
            status_json = client.get("/api/targets/test-status").json()[0]
            detail_json = client.get(f"/api/test-runs/{run_json['id']}").json()
            search_json = client.get("/api/test-runs/search").json()["items"][0]
            for value in (
                target_json["created_at"],
                target_json["updated_at"],
                profile_json["created_at"],
                profile_json["updated_at"],
                run_json["started_at"],
                status_json["started_at"],
                detail_json["started_at"],
                search_json["started_at"],
            ):
                assert_utc(value)
            assert instant.isoformat() in client.get("/api/test-runs/export.csv").text
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
