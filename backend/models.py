"""Explicit domain contracts: source measurements are never physical diagnoses."""
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Verification(StrEnum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    UNAVAILABLE = "UNAVAILABLE"


class Provenance(Contract):
    snapshot_id: str
    resource_id: str
    source_url: str
    resource_url: str
    producer: str = "Central Ground Water Board (CGWB)"
    publisher: str = "NWIC / National Water Data Portal"
    retrieved_at_utc: datetime
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_count: int = Field(gt=0)
    full_file: Literal[True]
    terms_url: str
    transformations: list[str]
    exclusions: list[str]
    data_mode: Literal["OFFICIAL_HISTORICAL", "OFFICIAL_HISTORICAL_TEST_SUBSET", "SYNTHETIC_DEMONSTRATION"] = "OFFICIAL_HISTORICAL"

    @model_validator(mode="after")
    def known_retrieval_instant(self):
        if self.retrieved_at_utc.utcoffset() is None:
            raise ValueError("Retrieval time must have a verified timezone")
        return self


class Observation(Contract):
    observation_id: str
    station_group_key: str
    source_station_id: None = None
    source_row: int = Field(ge=2)
    snapshot_id: str
    measurement_raw: str
    raw_timestamp: str
    raw_numeric_value: float | None
    source_time: datetime | None
    observed_at_utc: None = None
    measurement_semantics: Literal["PROVIDER_NATIVE_UNKNOWN"] = "PROVIDER_NATIVE_UNKNOWN"
    normalization_status: Literal["UNVERIFIED"] = "UNVERIFIED"
    timestamp_timezone: Literal["UNVERIFIED"] = "UNVERIFIED"
    declared_unit: Literal["meter"] = "meter"
    issues: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def preserve_source_clock(self):
        if self.source_time and self.source_time.utcoffset() is not None:
            raise ValueError("This adapter has no verified source timezone")
        return self


class Station(Contract):
    station_group_key: str
    label: str
    district: str
    agency: str
    state: str
    grouping_basis: dict[str, str]
    identity_status: Literal["UNVERIFIED"] = "UNVERIFIED"
    identity_reason: str = "Internal label/agency/district/coordinate grouping; physical continuity unverified."


class Quality(Contract):
    window_start: datetime
    window_end_exclusive: datetime
    state: Literal["LIMITED", "POOR", "INSUFFICIENT"]
    intended_use: str = "Provider-native same-station spike screening"
    raw_rows: int
    valid_unique_observations: int
    numeric_invalid: int
    timestamp_invalid: int
    duplicate_timestamps: int
    conflicting_timestamps: int
    out_of_order: int
    expected_cadence_seconds: int = 21600
    cadence_basis: str = "Official resource title/header: six-hourly; source-clock grid assessed separately"
    expected_slots: int
    occupied_slots: int
    completeness: float = Field(ge=0, le=1)
    off_grid_count: int
    longest_gap_seconds: float | None
    available_history_seconds: float
    reasons: list[str]


class DetectorResult(Contract):
    detector: Literal["SPIKE", "FLATLINE", "DROPOUT"]
    eligibility: Literal["ELIGIBLE", "UNAVAILABLE", "INSUFFICIENT_HISTORY"]
    reason: str
    execution_status: Literal["NOT_RUN", "SUCCEEDED"] = "NOT_RUN"
    outcome: Literal["FLAG", "NO_FLAG"] | None = None
    candidate_id: str | None = None
    baseline_ids: list[str] = Field(default_factory=list)
    reference_median: float | None = None
    robust_scale: float | None = None
    score: float | None = None
    step_score: float | None = None
    threshold: float | None = None
    config_version: str = "spike-v1-experimental-28-20-6-step"
    window_start: datetime | None = None
    window_end: datetime | None = None
    affected_source_times: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def no_false_normality(self):
        if self.execution_status == "SUCCEEDED":
            if self.eligibility != "ELIGIBLE" or self.outcome is None:
                raise ValueError("Only eligible successful execution has an outcome")
        elif self.outcome is not None:
            raise ValueError("Not-run is not NO_FLAG")
        return self


class NextCheck(Contract):
    action: str
    rationale: str
    evidence_gap_addressed: str
    priority: str = "Review suggestion; no calibrated urgency"


class EvidencePackage(Contract):
    evidence_id: str
    station: Station
    observation: Observation | None
    relevant_history: list[Observation]
    provenance: Provenance
    quality: Quality
    detectors: list[DetectorResult]
    supporting_evidence: list[str]
    contradicting_evidence: list[str]
    unavailable_evidence: list[str]
    limitations: list[str]
    assessment: Literal["TELEMETRY_EVIDENCE", "ENVIRONMENTAL_CHANGE_POSSIBLE", "UNCERTAIN", "INSUFFICIENT_EVIDENCE"]
    assessment_reason: str
    next_check: NextCheck
    analysis_as_of: datetime
    clock_basis: Literal["SOURCE_CLOCK_TIMEZONE_UNVERIFIED"] = "SOURCE_CLOCK_TIMEZONE_UNVERIFIED"
    flagged_observations: int
    evaluated_observations: int
    unavailable_observations: int
    analysis_version: str = "p0-patterns-v1"
