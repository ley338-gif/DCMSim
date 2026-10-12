import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def alembic(db_path: Path, revision: str) -> None:
    env = {**os.environ, "DCMSIM_DATABASE_URL": f"sqlite:///{db_path.as_posix()}"}
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "apps/api/alembic.ini", "upgrade", revision],
        cwd=Path(__file__).parents[4], env=env, check=True, capture_output=True, text=True,
    )


def test_0008_preserves_existing_endpoints_and_history(tmp_path):
    path = tmp_path / "existing.db"
    alembic(path, "0007")
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO dicom_systems VALUES (1,'RIS','2026-09-12','2026-09-12')")
        db.execute("INSERT INTO dicom_endpoints VALUES (1,1,'MWL','MWL','ris.local',104,'RIS','2026-09-12','2026-09-12')")
        db.execute(
            "INSERT INTO test_runs (id,test_type,started_at,duration_ms,success,status,result_json) "
            "VALUES (1,'mwl_find','2026-09-12',12,1,'0x0000','{\"count\":0}')"
        )
    alembic(path, "head")
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT host,port,called_ae,monitored,monitor_calling_ae,monitor_window,monitor_min_count FROM dicom_endpoints").fetchone() == ("ris.local", 104, "RIS", 0, "DCMSIM", None, 0)
        assert db.execute("SELECT result_json,username FROM test_runs").fetchone() == ('{"count":0}', None)
