import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


def alembic(db_path: Path, revision: str):
    alembic_command(db_path, "upgrade", revision)


def alembic_command(db_path: Path, command: str, revision: str):
    env = {**os.environ, "DCMSIM_DATABASE_URL": f"sqlite:///{db_path.as_posix()}"}
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "apps/api/alembic.ini", command, revision],
        cwd=Path(__file__).parents[4],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def test_legacy_targets_are_normalized_without_reinterpreting_history(tmp_path):
    database = tmp_path / "migration.db"
    alembic(database, "0005")
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO targets VALUES (1,'Legacy PACS','pacs.local',1,104,'MWL',1,11112,'STORE','DCMSIM','2026-09-12','2026-09-12',1,11113,'QR')"
    )
    connection.execute(
        "INSERT INTO modality_profiles VALUES (1,'CT 1',NULL,'CT','CT01',1,1,1,1,'2026-09-12','2026-09-12')"
    )
    history = {"name": "Legacy PACS", "host": "pacs.local", "called_ae": "OLD"}
    connection.execute(
        "INSERT INTO test_runs VALUES (1,'dicom_echo',1,NULL,'2026-09-12',1,1,'0x0000',?,?)",
        (json.dumps({"success": True}), json.dumps(history)),
    )
    connection.commit()
    connection.close()

    alembic(database, "head")
    connection = sqlite3.connect(database)
    assert connection.execute("SELECT name FROM dicom_systems").fetchall() == [("Legacy PACS",)]
    assert connection.execute("SELECT service,host,port,called_ae FROM dicom_endpoints ORDER BY service").fetchall() == [
        ("MWL", "pacs.local", 104, "MWL"),
        ("QR", "pacs.local", 11113, "QR"),
        ("STORE", "pacs.local", 11112, "STORE"),
    ]
    profile = connection.execute(
        "SELECT area_id,worklist_channel_id,store_endpoint_id FROM modality_profiles"
    ).fetchone()
    assert profile[0] is None
    assert profile[1] is not None and profile[2] is not None
    channel = connection.execute(
        "SELECT station_ae_mode,modality_filter_mode,modality_filter_fixed_value FROM worklist_channels"
    ).fetchone()
    assert channel == ("profile", "profile", None)
    target_id, snapshot = connection.execute(
        "SELECT target_id,target_snapshot_json FROM test_runs WHERE id=1"
    ).fetchone()
    assert target_id == 1
    assert json.loads(snapshot) == history
    connection.close()


def test_migration_bounds_generated_names_and_avoids_channel_collisions(tmp_path):
    database = tmp_path / "long-names.db"
    alembic(database, "0005")
    connection = sqlite3.connect(database)
    target_name = "T" * 120
    connection.execute(
        "INSERT INTO targets (id,name,host,mwl_enabled,mwl_port,mwl_called_ae,store_enabled,store_port,store_called_ae,default_calling_ae,created_at,updated_at,qr_enabled,qr_port,qr_called_ae) VALUES (1,?,'pacs.local',1,104,'MWL',1,11112,'STORE','DCMSIM','2026-09-12','2026-09-12',1,11113,'QR')",
        (target_name,),
    )
    for profile_id, suffix in ((1, "A"), (2, "B")):
        connection.execute(
            "INSERT INTO modality_profiles (id,name,description,modality,calling_ae,mwl_enabled,mwl_target_id,store_enabled,store_target_id,created_at,updated_at) VALUES (?,?,NULL,'CT',?,1,1,1,1,'2026-09-12','2026-09-12')",
            (profile_id, "P" * 119 + suffix, f"CT0{profile_id}"),
        )
    connection.commit()
    connection.close()

    alembic(database, "head")

    connection = sqlite3.connect(database)
    names = [
        row[0]
        for table in ("dicom_systems", "dicom_endpoints", "worklist_channels")
        for row in connection.execute(f"SELECT name FROM {table}").fetchall()
    ]
    channel_names = connection.execute(
        "SELECT name FROM worklist_channels ORDER BY name"
    ).fetchall()
    assert all(len(name) <= 120 for name in names)
    assert len(set(channel_names)) == 2
    connection.close()


def test_migration_adds_topology_check_constraints(tmp_path):
    database = tmp_path / "constraints.db"
    alembic(database, "head")
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO dicom_systems (id,name,created_at,updated_at) VALUES (1,'RIS','2026-09-12','2026-09-12')"
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO dicom_endpoints (id,system_id,name,service,host,port,called_ae,created_at,updated_at) VALUES (1,1,'Bad','PRINT','ris.local',104,'RIS','2026-09-12','2026-09-12')"
        )
    connection.execute(
        "INSERT INTO dicom_endpoints (id,system_id,name,service,host,port,called_ae,created_at,updated_at) VALUES (1,1,'MWL','MWL','ris.local',104,'RIS','2026-09-12','2026-09-12')"
    )
    invalid_channels = (
        ("invalid", None, "profile", None),
        ("fixed", None, "profile", None),
        ("profile", "UNEXPECTED", "profile", None),
        ("profile", None, "fixed", None),
    )
    for index, filters in enumerate(invalid_channels, start=1):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO worklist_channels (id,name,area_id,modality_code,mwl_endpoint_id,station_ae_mode,station_ae_fixed_value,modality_filter_mode,modality_filter_fixed_value,created_at,updated_at) VALUES (?, ?, NULL, 'CT', 1, ?, ?, ?, ?, '2026-09-12', '2026-09-12')",
                (index, f"Bad {index}", *filters),
            )
    connection.close()


def test_migration_downgrade_preserves_legacy_tables_and_data(tmp_path):
    database = tmp_path / "downgrade.db"
    alembic(database, "0005")
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO targets VALUES (1,'Legacy','pacs.local',1,104,'MWL',0,NULL,NULL,'DCMSIM','2026-09-12','2026-09-12',0,NULL,NULL)"
    )
    connection.execute(
        "INSERT INTO modality_profiles VALUES (1,'CT 1',NULL,'CT','CT01',1,1,0,NULL,'2026-09-12','2026-09-12')"
    )
    connection.commit()
    connection.close()

    alembic(database, "head")
    alembic_command(database, "downgrade", "0005")

    connection = sqlite3.connect(database)
    assert connection.execute("SELECT name FROM targets").fetchall() == [("Legacy",)]
    assert connection.execute("SELECT name FROM modality_profiles").fetchall() == [("CT 1",)]
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(modality_profiles)")
    }
    assert "worklist_channel_id" not in columns
    connection.close()
