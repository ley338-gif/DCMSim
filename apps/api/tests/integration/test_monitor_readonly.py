import sqlite3

from app import monitor
from app.core.config import settings
from app.db.base import Base
from app.models import DicomEndpoint, DicomSystem
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_monitor_selects_endpoints_read_only_and_reports_all(tmp_path, monkeypatch, capsys):
    path = tmp_path / "monitor.db"
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        system = DicomSystem(name="RIS")
        db.add(system)
        db.flush()
        db.add_all([
            DicomEndpoint(system_id=system.id, name="Radiologie", service="MWL", host="127.0.0.1", port=104, called_ae="RIS", monitored=True, monitor_calling_ae="DCMSIM", monitor_min_count=1),
            DicomEndpoint(system_id=system.id, name="Nicht überwacht", service="STORE", host="127.0.0.1", port=105, called_ae="PACS", monitored=False),
        ])
        db.commit()
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{path}")
    selected = monitor.load_endpoints(include_all=False, system=None, service=None)
    assert len(selected) == 1 and selected[0]["name"] == "Radiologie"
    assert len(monitor.load_endpoints(include_all=True, system="RIS", service="STORE")) == 1
    monkeypatch.setattr(monitor, "run_checks", lambda endpoints, **_kwargs: [{"state": 0, "count": 0, "duration_ms": 1, "message": "OK"} for _ in endpoints])
    assert monitor.main(["--all", "--report"]) == 0
    assert "2 von 2 OK" in capsys.readouterr().out
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM test_runs").fetchone() == (0,)
        assert db.execute("SELECT count(*) FROM dicom_endpoints").fetchone() == (2,)
