from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Target(Base):
    __tablename__ = "targets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    host: Mapped[str] = mapped_column(String(255))
    mwl_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    mwl_port: Mapped[int | None] = mapped_column(Integer)
    mwl_called_ae: Mapped[str | None] = mapped_column(String(16))
    store_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    store_port: Mapped[int | None] = mapped_column(Integer)
    store_called_ae: Mapped[str | None] = mapped_column(String(16))
    qr_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    qr_port: Mapped[int | None] = mapped_column(Integer)
    qr_called_ae: Mapped[str | None] = mapped_column(String(16))
    default_calling_ae: Mapped[str] = mapped_column(String(16), default="DCMSIM")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    runs: Mapped[list["TestRun"]] = relationship(back_populates="target")


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Area(Base):
    __tablename__ = "areas"
    __table_args__ = (UniqueConstraint("site_id", "name", name="uq_area_site_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class DicomSystem(Base):
    __tablename__ = "dicom_systems"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class DicomEndpoint(Base):
    __tablename__ = "dicom_endpoints"
    __table_args__ = (
        UniqueConstraint("system_id", "name", name="uq_endpoint_system_name"),
        CheckConstraint("service IN ('MWL', 'STORE', 'QR')", name="ck_endpoint_service"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    system_id: Mapped[int] = mapped_column(
        ForeignKey("dicom_systems.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    service: Mapped[str] = mapped_column(String(8), index=True)
    host: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer)
    called_ae: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class WorklistChannel(Base):
    __tablename__ = "worklist_channels"
    __table_args__ = (
        CheckConstraint(
            "station_ae_mode IN ('profile', 'fixed', 'omit')",
            name="ck_channel_station_ae_mode",
        ),
        CheckConstraint(
            "(station_ae_mode = 'fixed' AND station_ae_fixed_value IS NOT NULL AND "
            "length(trim(station_ae_fixed_value)) BETWEEN 1 AND 16) OR "
            "(station_ae_mode IN ('profile', 'omit') AND station_ae_fixed_value IS NULL)",
            name="ck_channel_station_ae_fixed_value",
        ),
        CheckConstraint(
            "modality_filter_mode IN ('profile', 'fixed', 'omit')",
            name="ck_channel_modality_filter_mode",
        ),
        CheckConstraint(
            "(modality_filter_mode = 'fixed' AND modality_filter_fixed_value IS NOT NULL AND "
            "modality_filter_fixed_value IN "
            "('CT','MR','US','CR','DX','OT','XA','MG','NM','PT')) OR "
            "(modality_filter_mode IN ('profile', 'omit') AND modality_filter_fixed_value IS NULL)",
            name="ck_channel_modality_filter_fixed_value",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    area_id: Mapped[int | None] = mapped_column(
        ForeignKey("areas.id", ondelete="SET NULL"), index=True
    )
    modality_code: Mapped[str] = mapped_column(String(8))
    mwl_endpoint_id: Mapped[int] = mapped_column(
        ForeignKey("dicom_endpoints.id", ondelete="RESTRICT"), index=True
    )
    station_ae_mode: Mapped[str] = mapped_column(String(8))
    station_ae_fixed_value: Mapped[str | None] = mapped_column(String(16))
    modality_filter_mode: Mapped[str] = mapped_column(String(8))
    modality_filter_fixed_value: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    mwl_endpoint: Mapped[DicomEndpoint] = relationship(foreign_keys=[mwl_endpoint_id])


class ModalityProfile(Base):
    __tablename__ = "modality_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))
    modality: Mapped[str] = mapped_column(String(8))
    calling_ae: Mapped[str] = mapped_column(String(16))
    mwl_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    mwl_target_id: Mapped[int | None] = mapped_column(
        ForeignKey("targets.id", ondelete="SET NULL"), index=True
    )
    store_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    store_target_id: Mapped[int | None] = mapped_column(
        ForeignKey("targets.id", ondelete="SET NULL"), index=True
    )
    area_id: Mapped[int | None] = mapped_column(ForeignKey("areas.id", ondelete="SET NULL"), index=True)
    worklist_channel_id: Mapped[int | None] = mapped_column(
        ForeignKey("worklist_channels.id", ondelete="SET NULL"), index=True
    )
    store_endpoint_id: Mapped[int | None] = mapped_column(
        ForeignKey("dicom_endpoints.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    mwl_target: Mapped[Target | None] = relationship(foreign_keys=[mwl_target_id])
    store_target: Mapped[Target | None] = relationship(foreign_keys=[store_target_id])
    worklist_channel: Mapped[WorklistChannel | None] = relationship(
        foreign_keys=[worklist_channel_id]
    )
    store_endpoint: Mapped[DicomEndpoint | None] = relationship(foreign_keys=[store_endpoint_id])


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_type: Mapped[str] = mapped_column(String(32), index=True)
    target_id: Mapped[int | None] = mapped_column(ForeignKey("targets.id", ondelete="SET NULL"))
    manual_target_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    target_snapshot_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    duration_ms: Mapped[int] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String(64))
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    target: Mapped[Target | None] = relationship(back_populates="runs")
