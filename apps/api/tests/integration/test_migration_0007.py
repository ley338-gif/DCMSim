import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def alembic(db_path: Path, command: str, revision: str):
    env = {**os.environ, "DCMSIM_DATABASE_URL": f"sqlite:///{db_path.as_posix()}"}
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "apps/api/alembic.ini", command, revision],
        cwd=Path(__file__).parents[4],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def test_0007_adds_explicit_safe_channel_ownership_marker(tmp_path):
    database = tmp_path / "ownership.db"
    alembic(database, "upgrade", "0006")
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO dicom_systems VALUES (1,'RIS','2026-09-12','2026-09-12')"
    )
    connection.execute(
        "INSERT INTO dicom_endpoints VALUES (1,1,'MWL','MWL','ris.local',104,'RIS','2026-09-12','2026-09-12')"
    )
    connection.execute(
        "INSERT INTO worklist_channels VALUES (1,'Existing',NULL,'CT',1,'profile',NULL,'profile',NULL,'2026-09-12','2026-09-12')"
    )
    connection.commit()
    connection.close()

    alembic(database, "upgrade", "head")
    connection = sqlite3.connect(database)
    columns = {row[1]: row for row in connection.execute("PRAGMA table_info(worklist_channels)")}
    assert columns["is_internal"][3] == 1
    assert connection.execute(
        "SELECT is_internal FROM worklist_channels WHERE id=1"
    ).fetchone() == (0,)
    connection.execute(
        "INSERT INTO worklist_channels (id,name,area_id,modality_code,mwl_endpoint_id,station_ae_mode,station_ae_fixed_value,modality_filter_mode,modality_filter_fixed_value,created_at,updated_at) VALUES (2,'Manual default',NULL,'CT',1,'profile',NULL,'profile',NULL,'2026-09-12','2026-09-12')"
    )
    assert connection.execute(
        "SELECT is_internal FROM worklist_channels WHERE id=2"
    ).fetchone() == (0,)
    connection.close()


def test_0007_downgrade_removes_only_marker(tmp_path):
    database = tmp_path / "downgrade.db"
    alembic(database, "upgrade", "head")
    alembic(database, "downgrade", "0006")
    connection = sqlite3.connect(database)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(worklist_channels)")}
    assert "is_internal" not in columns
    assert "station_ae_mode" in columns
    connection.close()
