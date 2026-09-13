import os
import sqlite3
import tempfile
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.names import suffixed_node_name
from app.models import (
    Area,
    DicomEndpoint,
    DicomSystem,
    ModalityProfile,
    Site,
    Target,
    TestRun,
    WorklistChannel,
)
from app.schemas.common import ConfigurationImport
from app.services.topology_validation import (
    validate_endpoint_service_change,
    validate_worklist_channel_identity_change,
)


def export_configuration(db: Session) -> dict:
    sites = db.scalars(select(Site).order_by(Site.name)).all()
    areas = db.scalars(select(Area).order_by(Area.site_id, Area.name)).all()
    systems = db.scalars(select(DicomSystem).order_by(DicomSystem.name)).all()
    endpoints = db.scalars(select(DicomEndpoint).order_by(DicomEndpoint.name)).all()
    channels = db.scalars(select(WorklistChannel).order_by(WorklistChannel.name)).all()
    profiles = db.scalars(select(ModalityProfile).order_by(ModalityProfile.name)).all()
    site_names = {item.id: item.name for item in sites}
    area_names = {item.id: item.name for item in areas}
    area_site_names = {item.id: site_names[item.site_id] for item in areas}
    endpoint_by_id = {item.id: item for item in endpoints}
    system_names = {item.id: item.name for item in systems}
    channel_names = {item.id: item.name for item in channels}
    return {
        "format_version": 2,
        "exported_at": datetime.now(UTC).isoformat(),
        "sites": [{"name": item.name} for item in sites],
        "areas": [
            {"name": item.name, "site_name": site_names[item.site_id]} for item in areas
        ],
        "dicom_systems": [
            {
                "name": system.name,
                "endpoints": [
                    {
                        "name": endpoint.name,
                        "service": endpoint.service,
                        "host": endpoint.host,
                        "port": endpoint.port,
                        "called_ae": endpoint.called_ae,
                    }
                    for endpoint in endpoints
                    if endpoint.system_id == system.id
                ],
            }
            for system in systems
        ],
        "worklist_channels": [
            {
                "name": channel.name,
                "site_name": area_site_names.get(channel.area_id),
                "area_name": area_names.get(channel.area_id),
                "modality_code": channel.modality_code,
                "mwl_system_name": system_names[endpoint_by_id[channel.mwl_endpoint_id].system_id],
                "mwl_endpoint_name": endpoint_by_id[channel.mwl_endpoint_id].name,
                "station_ae_mode": channel.station_ae_mode,
                "station_ae_fixed_value": channel.station_ae_fixed_value,
                "modality_filter_mode": channel.modality_filter_mode,
                "modality_filter_fixed_value": channel.modality_filter_fixed_value,
            }
            for channel in channels
        ],
        "modality_profiles": [
            {
                "name": profile.name,
                "description": profile.description,
                "modality": profile.modality,
                "calling_ae": profile.calling_ae,
                "site_name": area_site_names.get(profile.area_id),
                "area_name": area_names.get(profile.area_id),
                "worklist_channel_name": channel_names.get(profile.worklist_channel_id),
                "store_system_name": (
                    system_names[endpoint_by_id[profile.store_endpoint_id].system_id]
                    if profile.store_endpoint_id else None
                ),
                "store_endpoint_name": (
                    endpoint_by_id[profile.store_endpoint_id].name
                    if profile.store_endpoint_id else None
                ),
            }
            for profile in profiles
        ],
    }


def _upsert_endpoint(
    db: Session,
    system: DicomSystem,
    name: str,
    service: str,
    host: str,
    port: int,
    called_ae: str,
) -> DicomEndpoint:
    endpoint = db.scalar(
        select(DicomEndpoint).where(
            DicomEndpoint.system_id == system.id, DicomEndpoint.name == name
        )
    )
    if endpoint is None:
        endpoint = DicomEndpoint(system_id=system.id, name=name, service=service)
        db.add(endpoint)
    else:
        validate_endpoint_service_change(db, endpoint.id, endpoint.service, service)
    endpoint.host = host
    endpoint.port = port
    endpoint.called_ae = called_ae
    endpoint.service = service
    db.flush()
    return endpoint


def _normalize_v1_import(db: Session, payload, targets: dict[str, Target]) -> None:
    systems = {item.name: item for item in db.scalars(select(DicomSystem)).all()}
    normalized: dict[tuple[str, str], DicomEndpoint] = {}
    for item in payload.targets:
        target = targets[item.name]
        system = systems.get(item.name)
        if system is None:
            system = DicomSystem(name=item.name)
            db.add(system)
            db.flush()
            systems[item.name] = system
        for service, enabled, port, called_ae in (
            ("MWL", target.mwl_enabled, target.mwl_port, target.mwl_called_ae),
            ("STORE", target.store_enabled, target.store_port, target.store_called_ae),
            ("QR", target.qr_enabled, target.qr_port, target.qr_called_ae),
        ):
            if enabled and port is not None and called_ae is not None:
                normalized[(item.name, service)] = _upsert_endpoint(
                    db,
                    system,
                    suffixed_node_name(item.name, service),
                    service,
                    target.host,
                    port,
                    called_ae,
                )

    profiles = {item.name: item for item in db.scalars(select(ModalityProfile)).all()}
    channels = {item.name: item for item in db.scalars(select(WorklistChannel)).all()}
    for item in payload.modality_profiles:
        profile = profiles[item.name]
        channel = None
        if item.mwl_enabled and item.mwl_target_name:
            endpoint = normalized[(item.mwl_target_name, "MWL")]
            channel_name = suffixed_node_name(item.name, "Worklist")
            channel = channels.get(channel_name)
            if channel is None:
                channel = WorklistChannel(name=channel_name, is_internal=True)
                db.add(channel)
                channels[channel_name] = channel
            else:
                desired = (
                    None,
                    item.modality,
                    endpoint.id,
                    "profile",
                    None,
                    "profile",
                    None,
                )
                current = (
                    channel.area_id,
                    channel.modality_code,
                    channel.mwl_endpoint_id,
                    channel.station_ae_mode,
                    channel.station_ae_fixed_value,
                    channel.modality_filter_mode,
                    channel.modality_filter_fixed_value,
                )
                other_profile = db.scalar(
                    select(ModalityProfile.id).where(
                        ModalityProfile.worklist_channel_id == channel.id,
                        ModalityProfile.id != profile.id,
                    )
                )
                if current != desired and other_profile is not None:
                    raise HTTPException(
                        409,
                        f"Worklist channel '{channel_name}' is used by another profile",
                    )
            channel.area_id = None
            channel.modality_code = item.modality
            channel.mwl_endpoint_id = endpoint.id
            channel.station_ae_mode = "profile"
            channel.station_ae_fixed_value = None
            channel.modality_filter_mode = "profile"
            channel.modality_filter_fixed_value = None
            db.flush()
        profile.area_id = None
        profile.worklist_channel_id = channel.id if channel else None
        profile.store_endpoint_id = (
            normalized.get((item.store_target_name, "STORE")).id
            if item.store_enabled and item.store_target_name
            else None
        )
        if channel is not None:
            profile.mwl_target_id = None
        if profile.store_endpoint_id is not None:
            profile.store_target_id = None


def import_configuration(db: Session, payload: ConfigurationImport) -> dict:
    if payload.format_version == 2:
        return _import_configuration_v2(db, payload)
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
    db.flush()
    _normalize_v1_import(db, payload, target_by_name)
    db.commit()
    return {
        "created_targets": created_targets,
        "updated_targets": updated_targets,
        "created_profiles": created_profiles,
        "updated_profiles": updated_profiles,
    }


def _import_configuration_v2(db: Session, payload) -> dict:
    counters = {
        "created_sites": 0, "updated_sites": 0, "created_areas": 0, "updated_areas": 0,
        "created_systems": 0, "updated_systems": 0, "created_endpoints": 0,
        "updated_endpoints": 0, "created_channels": 0, "updated_channels": 0,
        "created_profiles": 0, "updated_profiles": 0,
    }
    sites = {item.name: item for item in db.scalars(select(Site)).all()}
    for value in payload.sites:
        item = sites.get(value.name)
        if item is None:
            item = Site(name=value.name)
            db.add(item)
            sites[value.name] = item
            counters["created_sites"] += 1
        else:
            counters["updated_sites"] += 1
    db.flush()
    site_names_by_id = {item.id: item.name for item in sites.values()}
    areas = {
        (site_names_by_id[item.site_id], item.name): item
        for item in db.scalars(select(Area)).all()
    }
    for value in payload.areas:
        site = sites.get(value.site_name)
        if site is None:
            raise HTTPException(422, f"Site '{value.site_name}' is missing")
        key = (value.site_name, value.name)
        item = areas.get(key)
        if item is None:
            item = Area(name=value.name, site_id=site.id)
            db.add(item)
            areas[key] = item
            counters["created_areas"] += 1
        else:
            counters["updated_areas"] += 1
    db.flush()
    systems = {item.name: item for item in db.scalars(select(DicomSystem)).all()}
    system_names_by_id = {item.id: item.name for item in systems.values()}
    endpoints = {
        (system_names_by_id[item.system_id], item.name): item
        for item in db.scalars(select(DicomEndpoint)).all()
    }
    for value in payload.dicom_systems:
        system = systems.get(value.name)
        if system is None:
            system = DicomSystem(name=value.name)
            db.add(system)
            systems[value.name] = system
            counters["created_systems"] += 1
        else:
            counters["updated_systems"] += 1
        db.flush()
        existing = {item.name: item for item in db.scalars(select(DicomEndpoint).where(DicomEndpoint.system_id == system.id)).all()}
        for endpoint_value in value.endpoints:
            endpoint = existing.get(endpoint_value.name)
            values = endpoint_value.model_dump()
            if endpoint is None:
                endpoint = DicomEndpoint(system_id=system.id, **values)
                db.add(endpoint)
                counters["created_endpoints"] += 1
            else:
                validate_endpoint_service_change(
                    db, endpoint.id, endpoint.service, endpoint_value.service
                )
                for key, field_value in values.items():
                    setattr(endpoint, key, field_value)
                counters["updated_endpoints"] += 1
            db.flush()
            endpoints[(value.name, endpoint.name)] = endpoint
    channels = {item.name: item for item in db.scalars(select(WorklistChannel)).all()}
    for value in payload.worklist_channels:
        endpoint = endpoints.get((value.mwl_system_name, value.mwl_endpoint_name))
        area = areas.get((value.site_name, value.area_name))
        if endpoint is None or endpoint.service != "MWL":
            raise HTTPException(
                422,
                f"MWL endpoint '{value.mwl_system_name}/{value.mwl_endpoint_name}' is missing",
            )
        if value.area_name is not None and area is None:
            raise HTTPException(
                422, f"Area '{value.site_name}/{value.area_name}' is missing"
            )
        values = {
            "area_id": area.id if area else None, "modality_code": value.modality_code,
            "mwl_endpoint_id": endpoint.id, "station_ae_mode": value.station_ae_mode,
            "station_ae_fixed_value": value.station_ae_fixed_value,
            "modality_filter_mode": value.modality_filter_mode,
            "modality_filter_fixed_value": value.modality_filter_fixed_value,
        }
        channel = channels.get(value.name)
        if channel is None:
            channel = WorklistChannel(name=value.name, is_internal=False, **values)
            db.add(channel)
            channels[value.name] = channel
            counters["created_channels"] += 1
        else:
            validate_worklist_channel_identity_change(
                db, channel.id, values["area_id"], values["modality_code"]
            )
            channel.is_internal = False
            for key, field_value in values.items():
                setattr(channel, key, field_value)
            counters["updated_channels"] += 1
    db.flush()
    profiles = {item.name: item for item in db.scalars(select(ModalityProfile)).all()}
    for value in payload.modality_profiles:
        channel = channels.get(value.worklist_channel_name or "")
        endpoint = endpoints.get((value.store_system_name, value.store_endpoint_name))
        area = areas.get((value.site_name, value.area_name))
        if value.worklist_channel_name is not None and channel is None:
            raise HTTPException(
                422, f"Worklist channel '{value.worklist_channel_name}' is missing"
            )
        if value.store_endpoint_name is not None and endpoint is None:
            raise HTTPException(
                422,
                f"Store endpoint '{value.store_system_name}/{value.store_endpoint_name}' is missing",
            )
        if endpoint is not None and endpoint.service != "STORE":
            raise HTTPException(422, f"Store endpoint '{value.store_endpoint_name}' has wrong service")
        if value.area_name is not None and area is None:
            raise HTTPException(
                422, f"Area '{value.site_name}/{value.area_name}' is missing"
            )
        if channel is not None and channel.area_id != (area.id if area else None):
            raise HTTPException(422, "Worklist channel belongs to a different area")
        if channel is not None and channel.modality_code != value.modality:
            raise HTTPException(422, "Profile modality does not match worklist channel")
        values = {
            "description": value.description, "modality": value.modality,
            "calling_ae": value.calling_ae, "mwl_enabled": channel is not None,
            "store_enabled": endpoint is not None, "mwl_target_id": None,
            "store_target_id": None, "area_id": area.id if area else None,
            "worklist_channel_id": channel.id if channel else None,
            "store_endpoint_id": endpoint.id if endpoint else None,
        }
        profile = profiles.get(value.name)
        if profile is None:
            db.add(ModalityProfile(name=value.name, **values))
            counters["created_profiles"] += 1
        else:
            for key, field_value in values.items():
                setattr(profile, key, field_value)
            counters["updated_profiles"] += 1
    db.commit()
    return counters


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
