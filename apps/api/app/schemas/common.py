from __future__ import annotations

import re
from datetime import date as Date
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AE_RE = re.compile(r"^[A-Z0-9 _.-]{1,16}$", re.IGNORECASE)
HOST_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,253}$")


def validate_ae(value: str) -> str:
    value = value.strip().upper()
    if not AE_RE.fullmatch(value):
        raise ValueError("AE Title must contain 1-16 DICOM-safe characters")
    return value


def validate_host(value: str) -> str:
    value = value.strip()
    if not HOST_RE.fullmatch(value):
        raise ValueError("Enter a valid hostname or IP address")
    return value


class Endpoint(BaseModel):
    host: str
    port: int = Field(ge=1, le=65535)
    called_ae: str
    calling_ae: str = "DCMSIM"
    target_id: int | None = None

    _host = field_validator("host")(validate_host)
    _called = field_validator("called_ae")(validate_ae)
    _calling = field_validator("calling_ae")(validate_ae)


class TargetBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    host: str
    mwl_enabled: bool = True
    mwl_port: int | None = Field(default=104, ge=1, le=65535)
    mwl_called_ae: str | None = None
    store_enabled: bool = True
    store_port: int | None = Field(default=104, ge=1, le=65535)
    store_called_ae: str | None = None
    qr_enabled: bool = False
    qr_port: int | None = Field(default=104, ge=1, le=65535)
    qr_called_ae: str | None = None
    default_calling_ae: str = "DCMSIM"

    _host = field_validator("host")(validate_host)
    _calling = field_validator("default_calling_ae")(validate_ae)

    @field_validator("mwl_called_ae", "store_called_ae", "qr_called_ae")
    @classmethod
    def optional_ae(cls, value: str | None) -> str | None:
        return validate_ae(value) if value else None

    @model_validator(mode="after")
    def enabled_services_have_endpoint(self):
        if self.mwl_enabled and (not self.mwl_port or not self.mwl_called_ae):
            raise ValueError("Enabled worklist service needs port and Called AE")
        if self.store_enabled and (not self.store_port or not self.store_called_ae):
            raise ValueError("Enabled store service needs port and Called AE")
        if self.qr_enabled and (not self.qr_port or not self.qr_called_ae):
            raise ValueError("Enabled query/retrieve service needs port and Called AE")
        return self


class TargetCreate(TargetBase):
    pass


class TargetRead(TargetBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


ModalityCode = Literal["CT", "MR", "US", "CR", "DX", "OT", "XA", "MG", "NM", "PT"]


class ModalityProfileBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    modality: ModalityCode
    calling_ae: str
    mwl_enabled: bool = True
    mwl_target_id: int | None = None
    store_enabled: bool = True
    store_target_id: int | None = None

    _calling = field_validator("calling_ae")(validate_ae)


class ModalityProfileCreate(ModalityProfileBase):
    @model_validator(mode="after")
    def enabled_services_have_targets(self):
        if not self.mwl_enabled and not self.store_enabled:
            raise ValueError("At least one DICOM service must be enabled")
        if self.mwl_enabled and self.mwl_target_id is None:
            raise ValueError("Enabled worklist check needs a target")
        if self.store_enabled and self.store_target_id is None:
            raise ValueError("Enabled store check needs a target")
        return self


class ModalityProfileRead(ModalityProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class ModalityProfileImport(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    modality: ModalityCode
    calling_ae: str
    mwl_enabled: bool = True
    mwl_target_name: str | None = None
    store_enabled: bool = True
    store_target_name: str | None = None

    _calling = field_validator("calling_ae")(validate_ae)

    @model_validator(mode="after")
    def enabled_services_have_target_names(self):
        if not self.mwl_enabled and not self.store_enabled:
            raise ValueError("At least one DICOM service must be enabled")
        if self.mwl_enabled and not self.mwl_target_name:
            raise ValueError("Enabled worklist check needs a target name")
        if self.store_enabled and not self.store_target_name:
            raise ValueError("Enabled store check needs a target name")
        return self


class ConfigurationImport(BaseModel):
    format_version: Literal[1]
    targets: list[TargetCreate]
    modality_profiles: list[ModalityProfileImport]


class HistoryRetentionRequest(BaseModel):
    days: int = Field(ge=1, le=3650)


class WorklistFilters(BaseModel):
    date: Date | None = Field(default_factory=Date.today)
    modality: str | None = Field(default=None, max_length=16)
    station_ae: str | None = Field(default=None, max_length=16)
    patient_id: str | None = Field(default=None, max_length=64)
    accession_number: str | None = Field(default=None, max_length=64)
    patient_name: str | None = Field(default=None, max_length=64)


class WorklistRequest(Endpoint):
    broad: bool = False
    filters: WorklistFilters = Field(default_factory=WorklistFilters)


class StudyQueryFilters(BaseModel):
    patient_name: str | None = Field(default=None, max_length=64)
    patient_id: str | None = Field(default=None, max_length=64)
    accession_number: str | None = Field(default=None, max_length=64)
    study_date: Date | None = None
    modality: str | None = Field(default=None, max_length=16)

    @model_validator(mode="after")
    def require_safe_filter(self):
        if not any((self.patient_name, self.patient_id, self.accession_number, self.study_date, self.modality)):
            raise ValueError("At least one study query filter is required")
        return self


class StudyQueryRequest(Endpoint):
    filters: StudyQueryFilters = Field(default_factory=StudyQueryFilters)


SopClassKey = Literal["secondary_capture", "ct", "mr", "ultrasound", "cr", "dx"]
TransferSyntaxKey = Literal["explicit_vr_little_endian", "implicit_vr_little_endian"]


class ModalityCheckRequest(BaseModel):
    transfer_syntax: TransferSyntaxKey = "explicit_vr_little_endian"


class StoreRequest(Endpoint):
    sop_class: SopClassKey = "secondary_capture"
    transfer_syntax: TransferSyntaxKey = "explicit_vr_little_endian"


class EchoRequest(Endpoint):
    pass


class TestRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    test_type: str
    target_id: int | None
    manual_target_json: dict[str, Any] | None
    started_at: datetime
    duration_ms: int
    success: bool
    status: str
    result_json: dict[str, Any]
