from datetime import UTC, datetime, timedelta, timezone

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import TestRun as RunModel
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_dashboard_summary_counts_full_history_with_local_day_boundaries(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'dashboard.db'}")
    factory = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    start = datetime(2026, 9, 11, 22, tzinfo=UTC)
    end = start + timedelta(days=1)

    def run(test_type: str, success: bool, started_at: datetime) -> RunModel:
        return RunModel(
            test_type=test_type,
            started_at=started_at,
            duration_ms=10,
            success=success,
            status="0x0000" if success else "DICOM_TIMEOUT",
            result_json={"success": success},
        )

    with factory() as db:
        db.add_all(
            [run("mwl_find", True, start) for _ in range(101)]
            + [run("dicom_store", False, end - timedelta(seconds=1)) for _ in range(9)]
            + [run("qr_find", True, start - timedelta(seconds=1))]
            + [run("dicom_echo", True, end)]
        )
        db.commit()

    def session_override():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = session_override
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/dashboard/summary",
                params={"day_start": start.isoformat(), "day_end": end.isoformat()},
            )
            assert response.status_code == 200
            assert response.json() == {
                "today_total": 110,
                "today_success": 101,
                "by_type": {
                    "mwl_find": 101,
                    "dicom_store": 9,
                    "qr_find": 1,
                    "dicom_echo": 1,
                },
            }
            berlin = timezone(timedelta(hours=2))
            local_response = client.get(
                "/api/dashboard/summary",
                params={
                    "day_start": start.astimezone(berlin).isoformat(),
                    "day_end": end.astimezone(berlin).isoformat(),
                },
            )
            assert local_response.json() == response.json()
            assert len(client.get("/api/test-runs").json()) == 100
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_dashboard_summary_rejects_ambiguous_or_invalid_day_ranges():
    with TestClient(app) as client:
        for start, end in (
            ("2026-09-12T00:00:00", "2026-09-13T00:00:00"),
            ("2026-09-13T00:00:00Z", "2026-09-12T00:00:00Z"),
            ("2026-09-12T00:00:00Z", "2026-09-14T00:00:00Z"),
        ):
            response = client.get(
                "/api/dashboard/summary", params={"day_start": start, "day_end": end}
            )
            assert response.status_code == 422
