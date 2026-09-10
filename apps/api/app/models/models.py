from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
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
    default_calling_ae: Mapped[str] = mapped_column(String(16), default="DCMSIM")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    runs: Mapped[list["TestRun"]] = relationship(back_populates="target")


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_type: Mapped[str] = mapped_column(String(32), index=True)
    target_id: Mapped[int | None] = mapped_column(ForeignKey("targets.id", ondelete="SET NULL"))
    manual_target_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    duration_ms: Mapped[int] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String(64))
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    target: Mapped[Target | None] = relationship(back_populates="runs")

