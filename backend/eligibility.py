"""Facts required by optional P0 executions, with explicit evidence references.

Unknown source timezone does not prohibit internally consistent source-clock
analysis. No resolution, active interval or publication allowance is inferred.
"""
from datetime import datetime

from pydantic import Field, model_validator

from .models import Contract, Verification


class DetectorContext(Contract):
    cadence_status: Verification = Verification.UNVERIFIED
    cadence_seconds: int | None = Field(default=None, gt=0)
    cadence_refs: list[str] = Field(default_factory=list)
    source_clock_status: Verification = Verification.UNVERIFIED
    source_clock_refs: list[str] = Field(default_factory=list)
    resolution_status: Verification = Verification.UNVERIFIED
    resolution: float | None = Field(default=None, gt=0)
    resolution_refs: list[str] = Field(default_factory=list)
    active_interval_status: Verification = Verification.UNVERIFIED
    active_start: datetime | None = None
    active_end_exclusive: datetime | None = None
    active_interval_refs: list[str] = Field(default_factory=list)
    publication_allowance_status: Verification = Verification.UNVERIFIED
    publication_allowance_seconds: int | None = Field(default=None, ge=0)
    publication_allowance_refs: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def require_evidence_for_verified_facts(self):
        facts = [
            (self.cadence_status, self.cadence_seconds is not None, self.cadence_refs),
            (self.source_clock_status, True, self.source_clock_refs),
            (self.resolution_status, self.resolution is not None, self.resolution_refs),
            (self.active_interval_status, self.active_start is not None and self.active_end_exclusive is not None, self.active_interval_refs),
            (self.publication_allowance_status, self.publication_allowance_seconds is not None, self.publication_allowance_refs),
        ]
        for status, present, refs in facts:
            if status == Verification.VERIFIED and (not present or not refs or any(not ref.strip() for ref in refs)):
                raise ValueError('Verified prerequisite needs a value and nonempty evidence reference')
        for value in (self.active_start, self.active_end_exclusive):
            if value and value.utcoffset() is not None:
                raise ValueError('Use the same naive source-clock basis as observations')
        if self.active_start and self.active_end_exclusive and self.active_start >= self.active_end_exclusive:
            raise ValueError('Active interval must have positive duration')
        return self
