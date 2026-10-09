"""Four-state policy. Inputs describe evidence, never causal probabilities.

External corroboration is a typed policy input only; no reference-provider
integration is claimed. Production defaults contain no corroboration.
"""
from typing import Literal
from pydantic import Field, model_validator

from .models import Contract, DetectorResult, NextCheck, Verification


class Corroboration(Contract):
    physical_semantics: Verification = Verification.UNVERIFIED
    comparable_independent_reference: Verification = Verification.UNAVAILABLE
    acquisition_diagnostics: Verification = Verification.UNAVAILABLE
    supports_environmental_change: bool = False
    supports_acquisition_problem: bool = False
    conflicting_evidence: bool = False
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def affirmative_claims_need_references(self):
        if (self.supports_environmental_change or self.supports_acquisition_problem or self.conflicting_evidence) and (not self.evidence_refs or any(not ref.strip() for ref in self.evidence_refs)):
            raise ValueError('Affirmative or conflicting evidence needs traceable references')
        return self


class TriageResult(Contract):
    assessment: Literal['TELEMETRY_EVIDENCE','ENVIRONMENTAL_CHANGE_POSSIBLE','UNCERTAIN','INSUFFICIENT_EVIDENCE']
    reason: str
    next_check: NextCheck


def triage(detectors: list[DetectorResult], corroboration: Corroboration | None = None) -> TriageResult:
    facts=corroboration or Corroboration()
    eligible=[r for r in detectors if r.execution_status=='SUCCEEDED' and r.eligibility=='ELIGIBLE']
    telemetry=(facts.acquisition_diagnostics==Verification.VERIFIED and facts.supports_acquisition_problem) or any(r.outcome=='FLAG' and r.detector in ('FLATLINE','DROPOUT') for r in eligible)
    environmental=(facts.physical_semantics==Verification.VERIFIED and facts.comparable_independent_reference==Verification.VERIFIED and facts.supports_environmental_change)
    if facts.conflicting_evidence or (telemetry and environmental):
        state, reason='UNCERTAIN','ABSTAIN: available evidence conflicts; do not force a single explanation.'
    elif environmental:
        state, reason='ENVIRONMENTAL_CHANGE_POSSIBLE','Verified physical meaning and a comparable independent reference affirm possible environmental movement; cause remains unestablished.'
    elif telemetry:
        state, reason='TELEMETRY_EVIDENCE','Evidence supports investigating data acquisition or availability; it does not establish a physical sensor failure.'
    elif eligible:
        state, reason='UNCERTAIN','ABSTAIN: the available telemetry cannot distinguish physical movement from a telemetry problem.'
    else:
        state, reason='INSUFFICIENT_EVIDENCE','Required usable local history or detector prerequisites are unavailable.'
    if state=='INSUFFICIENT_EVIDENCE':
        next_check=NextCheck(action='Recover comparable local history and verify the missing detector prerequisites.',rationale='No configured result is interpretable before its prerequisites are satisfied.',evidence_gap_addressed='; '.join(r.reason for r in detectors))
    elif state=='TELEMETRY_EVIDENCE':
        next_check=NextCheck(action='Compare the original logger record with the published portal record and check the operating schedule.',rationale='A record present locally but absent or different in the portal can distinguish publication/transmission issues from acquisition issues; unchanged values can also be real stability.',evidence_gap_addressed='Logger, transmission, publication and maintenance records are not yet compared.')
    else:
        next_check=NextCheck(action='Compare the original logger record and an independent reference measurement for this source time.',rationale='Agreement or disagreement can help distinguish a recording/transmission issue from genuine movement; verify timestamp and measurement reference before comparing.',evidence_gap_addressed='No independently established cause; reconcile time, reference and any conflicting observations.')
    return TriageResult(assessment=state,reason=reason,next_check=next_check)
