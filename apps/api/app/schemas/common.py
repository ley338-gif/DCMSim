from __future__ import annotations

import re
from datetime import date as Date
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.dates import as_utc

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

    _utc_timestamps = field_validator("created_at", "updated_at")(as_utc)


ModalityCode = Literal["CT", "MR", "US", "CR", "DX", "OT", "XA", "MG", "NM", "PT"]


class NamedNodeBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class SiteCreate(NamedNodeBase):
    pass


class SiteRead(NamedNodeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class AreaCreate(NamedNodeBase):
    site_id: int


class AreaRead(AreaCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class DicomSystemCreate(NamedNodeBase):
    pass


class DicomSystemRead(DicomSystemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class DicomEndpointCreate(NamedNodeBase):
    service: Literal["MWL", "STORE", "QR"]
    host: str
    port: int = Field(ge=1, le=65535)
    called_ae: str

    _host = field_validator("host")(validate_host)
    _called = field_validator("called_ae")(validate_ae)


class DicomEndpointRead(DicomEndpointCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    system_id: int
    created_at: datetime
    updated_at: datetime


FilterMode = Literal["profile", "fixed", "omit"]


def validate_worklist_filter_configuration(value):
    station_value = value.station_ae_fixed_value.strip() if value.station_ae_fixed_value else None
    modality_value = (
        value.modality_filter_fixed_value.strip().upper()
        if value.modality_filter_fixed_value
        else None
    )
    if value.station_ae_mode != "fixed":
        station_value = None
    if value.modality_filter_mode != "fixed":
        modality_value = None
    if value.station_ae_mode == "fixed" and not station_value:
        raise ValueError("Fixed station AE mode needs a value")
    if value.modality_filter_mode == "fixed" and not modality_value:
        raise ValueError("Fixed modality filter mode needs a value")

    if modality_value and modality_value not in ModalityCode.__args__:
        raise ValueError("Fixed modality filter must be a supported modality code")
    value.station_ae_fixed_value = validate_ae(station_value) if station_value else None
    value.modality_filter_fixed_value = modality_value
    return value


class WorklistChannelCreate(NamedNodeBase):
    area_id: int | None
    modality_code: ModalityCode
    mwl_endpoint_id: int
    station_ae_mode: FilterMode = "profile"
    station_ae_fixed_value: str | None = None
    modality_filter_mode: FilterMode = "profile"
    modality_filter_fixed_value: str | None = None

    @model_validator(mode="after")
    def fixed_modes_have_values(self):
        return validate_worklist_filter_configuration(self)


class WorklistChannelRead(WorklistChannelCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_internal: bool = False
    created_at: datetime
    updated_at: datetime


class ModalityProfileBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    modality: ModalityCode
    calling_ae: str
    mwl_enabled: bool = True
    mwl_target_id: int | None = None
    store_enabled: bool = True
    store_target_id: int | None = None
    area_id: int | None = None
    worklist_channel_id: int | None = None
    store_endpoint_id: int | None = None

    _calling = field_validator("calling_ae")(validate_ae)


class ModalityProfileCreate(ModalityProfileBase):
    @model_validator(mode="after")
    def enabled_services_have_targets(self):
        if not self.mwl_enabled and not self.store_enabled:
            raise ValueError("At least one DICOM service must be enabled")
        service_references = (
            (
                self.mwl_enabled,
                (self.mwl_target_id, self.worklist_channel_id),
                "worklist",
            ),
            (
                self.store_enabled,
                (self.store_target_id, self.store_endpoint_id),
                "store",
            ),
        )
        for enabled, references, label in service_references:
            reference_count = sum(reference is not None for reference in references)
            if enabled and reference_count != 1:
                raise ValueError(
                    f"Enabled {label} check needs exactly one Legacy or structured target"
                )
            if not enabled and reference_count:
                raise ValueError(f"Disabled {label} check cannot have a target")
        return self


class ModalityProfileRead(ModalityProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime

    _utc_timestamps = field_validator("created_at", "updated_at")(as_utc)


class InlineModalityProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    modality: ModalityCode
    calling_ae: str
    area_id: int | None = None
    mwl_enabled: bool = True
    mwl_endpoint_id: int | None = None
    mwl_target_id: int | None = None
    station_ae_mode: FilterMode = "profile"
    station_ae_fixed_value: str | None = None
    modality_filter_mode: FilterMode = "profile"
    modality_filter_fixed_value: str | None = None
    store_enabled: bool = True
    store_endpoint_id: int | None = None
    store_target_id: int | None = None

    _calling = field_validator("calling_ae")(validate_ae)

    @model_validator(mode="after")
    def validate_services_and_filters(self):
        if not self.mwl_enabled and not self.store_enabled:
            raise ValueError("At least one DICOM service must be enabled")
        for enabled, sources, service in (
            (self.mwl_enabled, (self.mwl_endpoint_id, self.mwl_target_id), "worklist"),
            (self.store_enabled, (self.store_endpoint_id, self.store_target_id), "store"),
        ):
            source_count = sum(source is not None for source in sources)
            if enabled and source_count != 1:
                raise ValueError(f"Enabled {service} service needs exactly one source")
            if not enabled and source_count:
                raise ValueError(f"Disabled {service} service cannot have a source")
        validate_worklist_filter_configuration(self)
        return self


class InlineModalityProfileRead(ModalityProfileRead):
    mwl_endpoint_id: int | None = None
    station_ae_mode: FilterMode | None = None
    station_ae_fixed_value: str | None = None
    modality_filter_mode: FilterMode | None = None
    modality_filter_fixed_value: str | None = None


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


class ConfigurationImportV1(BaseModel):
    format_version: Literal[1]
    targets: list[TargetCreate]
    modality_profiles: list[ModalityProfileImport]

    @model_validator(mode="after")
    def unique_names(self):
        for kind, items in (("target", self.targets), ("modality profile", self.modality_profiles)):
            names = [item.name for item in items]
            if len(names) != len(set(names)):
                raise ValueError(f"Duplicate {kind} names in configuration")
        return self


class AreaImport(NamedNodeBase):
    site_name: str


class DicomSystemImport(NamedNodeBase):
    endpoints: list[DicomEndpointCreate]


class WorklistChannelImport(NamedNodeBase):
    site_name: str | None
    area_name: str | None
    modality_code: ModalityCode
    mwl_system_name: str
    mwl_endpoint_name: str
    station_ae_mode: FilterMode
    station_ae_fixed_value: str | None = None
    modality_filter_mode: FilterMode
    modality_filter_fixed_value: str | None = None

    @model_validator(mode="after")
    def fixed_modes_have_values(self):
        return validate_worklist_filter_configuration(self)


class ModalityProfileImportV2(NamedNodeBase):
    description: str | None = Field(default=None, max_length=500)
    modality: ModalityCode
    calling_ae: str
    site_name: str | None
    area_name: str | None
    worklist_channel_name: str | None
    store_system_name: str | None
    store_endpoint_name: str | None

    _calling = field_validator("calling_ae")(validate_ae)

    @model_validator(mode="after")
    def has_active_services(self):
        if (self.store_system_name is None) != (self.store_endpoint_name is None):
            raise ValueError("Store references require both system and endpoint names")
        if self.worklist_channel_name is None and self.store_endpoint_name is None:
            raise ValueError("At least one DICOM service must be enabled")
        return self


class ConfigurationImportV2(BaseModel):
    format_version: Literal[2]
    sites: list[SiteCreate]
    areas: list[AreaImport]
    dicom_systems: list[DicomSystemImport]
    worklist_channels: list[WorklistChannelImport]
    modality_profiles: list[ModalityProfileImportV2]

    @model_validator(mode="after")
    def unique_names(self):
        groups = (
            ("site", self.sites),
            ("DICOM system", self.dicom_systems),
            ("worklist channel", self.worklist_channels),
            ("modality profile", self.modality_profiles),
        )
        for kind, items in groups:
            names = [item.name for item in items]
            if len(names) != len(set(names)):
                raise ValueError(f"Duplicate {kind} names in configuration")
        area_keys = [(item.site_name, item.name) for item in self.areas]
        if len(area_keys) != len(set(area_keys)):
            raise ValueError("Duplicate area names at the same site in configuration")
        for system in self.dicom_systems:
            names = [endpoint.name for endpoint in system.endpoints]
            if len(names) != len(set(names)):
                raise ValueError(f"Duplicate endpoint names in DICOM system {system.name}")
        for item in (*self.worklist_channels, *self.modality_profiles):
            if (item.site_name is None) != (item.area_name is None):
                raise ValueError("Area references require both site_name and area_name")
        return self


ConfigurationImport = ConfigurationImportV1 | ConfigurationImportV2


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
    diagnostic_broad: bool = False


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
    target_snapshot_json: dict[str, Any] | None
    started_at: datetime
    duration_ms: int
    success: bool
    status: str
    result_json: dict[str, Any]

    _utc_timestamp = field_validator("started_at")(as_utc)


class TestRunPage(BaseModel):
    items: list[TestRunRead]
    total: int
    limit: int
    offset: int


class TargetTestStatusRead(BaseModel):
    target_id: int
    run_id: int
    test_type: str
    started_at: datetime
    duration_ms: int
    success: bool
    status: str
    configuration_state: Literal["current", "changed", "unknown"]

    _utc_timestamp = field_validator("started_at")(as_utc)
