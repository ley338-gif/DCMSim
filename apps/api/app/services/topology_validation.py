from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ModalityProfile, WorklistChannel


def validate_endpoint_service_change(
    db: Session, endpoint_id: int, current_service: str, new_service: str
) -> None:
    if current_service == new_service:
        return
    channel_id = db.scalar(
        select(WorklistChannel.id).where(WorklistChannel.mwl_endpoint_id == endpoint_id)
    )
    profile_id = db.scalar(
        select(ModalityProfile.id).where(
            ModalityProfile.store_endpoint_id == endpoint_id
        )
    )
    if channel_id is not None or profile_id is not None:
        raise HTTPException(409, "Referenced endpoint service cannot be changed")


def validate_worklist_channel_identity_change(
    db: Session, channel_id: int, area_id: int | None, modality_code: str
) -> None:
    profiles = db.scalars(
        select(ModalityProfile).where(
            ModalityProfile.worklist_channel_id == channel_id
        )
    ).all()
    if any(profile.modality != modality_code for profile in profiles):
        raise HTTPException(409, "Channel modality would conflict with a profile")
    if any(profile.area_id != area_id for profile in profiles):
        raise HTTPException(409, "Channel area would conflict with a profile")