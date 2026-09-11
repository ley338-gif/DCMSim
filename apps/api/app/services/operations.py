import os
import sqlite3
import tempfile
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import ModalityProfile, Target, TestRun
from app.schemas.common import ConfigurationImport


def export_configuration(db: Session) -> dict:
    targets = db.scalars(select(Target).order_by(Target.name)).all()
    profiles = db.scalars(select(ModalityProfile).order_by(ModalityProfile.name)).all()
    return {
        "format_version": 1,
        "exported_at": datetime.now(UTC).isoformat(),
        "targets": [
            {
                key: getattr(target, key)
                for key in (
                    "name", "host", "mwl_enabled", "mwl_port", "mwl_called_ae",
                    "store_enabled", "store_port", "store_called_ae", "default_calling_ae",
                )
            }
            for target in targets
        ],
        "modality_profiles": [
            {
                "name": profile.name,
                "description": profile.description,
                "modality": profile.modality,
                "calling_ae": profile.calling_ae,
                "mwl_enabled": profile.mwl_enabled,
                "mwl_target_name": profile.mwl_target.name if profile.mwl_target else None,
                "store_enabled": profile.store_enabled,
                "store_target_name": profile.store_target.name if profile.store_target else None,
            }
            for profile in profiles
        ],
    }


def import_configuration(db: Session, payload: ConfigurationImport) -> dict:
    target_by_name = {target.name: target for target in db.scalars(select(Target)).all()}
    created_targets = updated_targets = 0
    for item in payload.targets:
        values = item.model_dump()
        target = target_by_name.get(item.name)
        if target is None:
            target = Target(**values)
            db.add(target)
            target_by_name[item.name] = target
            created_targets += 1
        else:
            for key, value in values.items():
                setattr(target, key, value)
            updated_targets += 1
    db.flush()

    profile_by_name = {
        profile.name: profile for profile in db.scalars(select(ModalityProfile)).all()
    }
    created_profiles = updated_profiles = 0
    for item in payload.modality_profiles:
        mwl_target = target_by_name.get(item.mwl_target_name or "")
        store_target = target_by_name.get(item.store_target_name or "")
        if item.mwl_enabled and (mwl_target is None or not mwl_target.mwl_enabled):
            raise HTTPException(422, f"MWL target '{item.mwl_target_name}' is missing or disabled")
        if item.store_enabled and (store_target is None or not store_target.store_enabled):
            raise HTTPException(422, f"Store target '{item.store_target_name}' is missing or disabled")
        values = {
            "name": item.name,
            "description": item.description,
            "modality": item.modality,
            "calling_ae": item.calling_ae,
            "mwl_enabled": item.mwl_enabled,
            "mwl_target_id": mwl_target.id if mwl_target else None,
            "store_enabled": item.store_enabled,
            "store_target_id": store_target.id if store_target else None,
        }
        profile = profile_by_name.get(item.name)
        if profile is None:
            db.add(ModalityProfile(**values))
            created_profiles += 1
        else:
            for key, value in values.items():
                setattr(profile, key, value)
            updated_profiles += 1
    db.commit()
    return {
        "created_targets": created_targets,
        "updated_targets": updated_targets,
        "created_profiles": created_profiles,
        "updated_profiles": updated_profiles,
    }


def purge_history(db: Session, days: int) -> dict:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    result = db.execute(delete(TestRun).where(TestRun.started_at < cutoff))
    db.commit()
    return {"deleted_count": result.rowcount or 0, "cutoff": cutoff.isoformat()}


def create_sqlite_backup(db: Session) -> str:
    driver_connection = db.connection().connection.driver_connection
    if not isinstance(driver_connection, sqlite3.Connection):
        raise HTTPException(501, "Database backup is only available for SQLite")
    handle = tempfile.NamedTemporaryFile(prefix="dcmsim-backup-", suffix=".sqlite3", delete=False)
    path = handle.name
    handle.close()
    destination = sqlite3.connect(path)
    try:
        driver_connection.backup(destination)
    except Exception:
        destination.close()
        os.unlink(path)
        raise
    destination.close()
    return path
