from datetime import UTC, datetime, timedelta

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Target
from app.models import TestRun as RunModel
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_target_status_returns_only_the_latest_attributed_test(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'target-status.db'}",
        connect_args={"check_same_thread": False},
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    with factory() as db:
        target = Target(
            name="PACS",
            host="127.0.0.1",
            mwl_enabled=False,
            store_enabled=True,
            store_port=104,
            store_called_ae="PACS",
            qr_enabled=False,
            default_calling_ae="DCMSIM",
        )
        untested = Target(
            name="Noch ungeprüft",
            host="127.0.0.2",
            mwl_enabled=False,
            store_enabled=True,
            store_port=104,
            store_called_ae="PACS2",
            qr_enabled=False,
            default_calling_ae="DCMSIM",
        )
        db.add_all([target, untested])
        db.flush()
        older = datetime.now(UTC) - timedelta(minutes=2)
        db.add_all(
            [
                RunModel(target_id=target.id, test_type="dicom_echo", manual_target_json=None, started_at=older, duration_ms=10, success=True, status="0x0000", result_json={}),
                RunModel(target_id=target.id, test_type="dicom_store", manual_target_json=None, duration_ms=25, success=False, status="DICOM_TIMEOUT", result_json={}),
                RunModel(target_id=None, test_type="dicom_echo", manual_target_json={"host": "127.0.0.3"}, duration_ms=4, success=True, status="0x0000", result_json={}),
            ]
        )
        db.commit()

    def session_override():
        with factory() as database:
            yield database

    app.dependency_overrides[get_db] = session_override
    try:
        with TestClient(app) as client:
            response = client.get("/api/targets/test-status")
            assert response.status_code == 200
            assert response.json() == [
                {
                    "target_id": target.id,
                    "run_id": 2,
                    "test_type": "dicom_store",
                    "started_at": response.json()[0]["started_at"],
                    "duration_ms": 25,
                    "success": False,
                    "status": "DICOM_TIMEOUT",
                }
            ]
    finally:
        app.dependency_overrides.clear()
