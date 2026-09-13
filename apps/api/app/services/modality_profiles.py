import hashlib
import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models import Area, DicomEndpoint, ModalityProfile, Target, WorklistChannel
from app.schemas.common import InlineModalityProfileCreate


def _semantic_tuple(payload: InlineModalityProfileCreate) -> tuple:
    return (
        payload.area_id,
        payload.modality,
        payload.mwl_endpoint_id,
        payload.station_ae_mode,
        payload.station_ae_fixed_value,
        payload.modality_filter_mode,
        payload.modality_filter_fixed_value,
    )


def _channel_tuple(channel: WorklistChannel) -> tuple:
    return (
        channel.area_id,
        channel.modality_code,
        channel.mwl_endpoint_id,
        channel.station_ae_mode,
        channel.station_ae_fixed_value,
        channel.modality_filter_mode,
        channel.modality_filter_fixed_value,
    )


def validate_inline_profile(payload: InlineModalityProfileCreate, db: Session) -> None:
    if payload.area_id is not None and db.get(Area, payload.area_id) is None:
        raise HTTPException(422, "Configured area does not exist")
    if payload.mwl_enabled:
        if payload.mwl_endpoint_id is not None:
            endpoint = db.get(DicomEndpoint, payload.mwl_endpoint_id)
            if endpoint is None or endpoint.service != "MWL":
                raise HTTPException(422, "Profile requires an MWL endpoint")
        else:
            target = db.get(Target, payload.mwl_target_id)
            if target is None or not target.mwl_enabled:
                raise HTTPException(422, "Profile requires an enabled Legacy MWL target")
    if payload.store_enabled:
        if payload.store_endpoint_id is not None:
            endpoint = db.get(DicomEndpoint, payload.store_endpoint_id)
            if endpoint is None or endpoint.service != "STORE":
                raise HTTPException(422, "Profile requires a STORE endpoint")
        else:
            target = db.get(Target, payload.store_target_id)
            if target is None or not target.store_enabled:
                raise HTTPException(422, "Profile requires an enabled Legacy STORE target")


def _internal_name(db: Session, semantic: tuple) -> str:
    del db
    encoded = json.dumps(semantic, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(encoded.encode()).hexdigest()[:20]
    return f"__dcmsim_inline_{digest}"


def resolve_channel(
    db: Session, payload: InlineModalityProfileCreate
) -> WorklistChannel | None:
    if not payload.mwl_enabled or payload.mwl_endpoint_id is None:
        return None
    semantic = _semantic_tuple(payload)
    candidates = db.scalars(
        select(WorklistChannel).where(
            WorklistChannel.area_id == payload.area_id,
            WorklistChannel.modality_code == payload.modality,
            WorklistChannel.mwl_endpoint_id == payload.mwl_endpoint_id,
        )
    ).all()
    for channel in candidates:
        if _channel_tuple(channel) == semantic:
            return channel
    values = dict(
        name=_internal_name(db, semantic),
        is_internal=True,
        area_id=payload.area_id,
        modality_code=payload.modality,
        mwl_endpoint_id=payload.mwl_endpoint_id,
        station_ae_mode=payload.station_ae_mode,
        station_ae_fixed_value=payload.station_ae_fixed_value,
        modality_filter_mode=payload.modality_filter_mode,
        modality_filter_fixed_value=payload.modality_filter_fixed_value,
    )
    if db.bind is not None and db.bind.dialect.name == "sqlite":
        db.execute(
            sqlite_insert(WorklistChannel)
            .values(**values)
            .on_conflict_do_nothing(index_elements=["name"])
        )
        channel = db.scalar(
            select(WorklistChannel).where(WorklistChannel.name == values["name"])
        )
        if channel is None or _channel_tuple(channel) != semantic:
            raise HTTPException(409, "Internal worklist channel name collision")
    else:
        channel = WorklistChannel(**values)
        db.add(channel)
        db.flush()
    return channel


def collect_internal_channel(db: Session, channel_id: int | None) -> None:
    if channel_id is None:
        return
    channel = db.get(WorklistChannel, channel_id)
    if channel is None or not channel.is_internal:
        return
    reference = db.scalar(
        select(ModalityProfile.id).where(
            ModalityProfile.worklist_channel_id == channel_id
        )
    )
    if reference is None:
        db.delete(channel)


def apply_inline_profile(
    db: Session,
    payload: InlineModalityProfileCreate,
    profile: ModalityProfile | None = None,
) -> ModalityProfile:
    validate_inline_profile(payload, db)
    old_channel_id = profile.worklist_channel_id if profile else None
    channel = resolve_channel(db, payload)
    mwl_target_id = None
    store_target_id = None
    if payload.mwl_enabled:
        mwl_target_id = payload.mwl_target_id
        if mwl_target_id is None and profile is not None:
            mwl_target_id = profile.mwl_target_id
    if payload.store_enabled:
        store_target_id = payload.store_target_id
        if store_target_id is None and profile is not None:
            store_target_id = profile.store_target_id
    values = {
        "name": payload.name,
        "description": payload.description,
        "modality": payload.modality,
        "calling_ae": payload.calling_ae,
        "area_id": payload.area_id,
        "mwl_enabled": payload.mwl_enabled,
        "mwl_target_id": mwl_target_id,
        "worklist_channel_id": channel.id if channel else None,
        "store_enabled": payload.store_enabled,
        "store_target_id": store_target_id,
        "store_endpoint_id": payload.store_endpoint_id,
    }
    if profile is None:
        profile = ModalityProfile(**values)
        db.add(profile)
    else:
        for key, value in values.items():
            setattr(profile, key, value)
    db.flush()
    if old_channel_id != profile.worklist_channel_id:
        collect_internal_channel(db, old_channel_id)
    return profile


def resolved_profile(profile: ModalityProfile) -> dict:
    channel = profile.worklist_channel
    return {
        "id": profile.id,
        "name": profile.name,
        "description": profile.description,
        "modality": profile.modality,
        "calling_ae": profile.calling_ae,
        "mwl_enabled": profile.mwl_enabled,
        "mwl_target_id": profile.mwl_target_id,
        "store_enabled": profile.store_enabled,
        "store_target_id": profile.store_target_id,
        "area_id": profile.area_id,
        "worklist_channel_id": profile.worklist_channel_id,
        "store_endpoint_id": profile.store_endpoint_id,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
        "mwl_endpoint_id": channel.mwl_endpoint_id if channel else None,
        "station_ae_mode": channel.station_ae_mode if channel else None,
        "station_ae_fixed_value": channel.station_ae_fixed_value if channel else None,
        "modality_filter_mode": channel.modality_filter_mode if channel else None,
        "modality_filter_fixed_value": channel.modality_filter_fixed_value if channel else None,
    }
