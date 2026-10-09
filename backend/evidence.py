"""Deterministic evidence; anomaly scores never become causal confidence."""
from .models import DetectorResult, EvidencePackage, Verification
from .eligibility import DetectorContext
from .flatline import detect_flatline
from .dropout import detect_dropout
from .triage import triage
from .provider import END
from .quality import assess
from .spike import detect


def build_evidence(station, records, provenance):
    quality, clean = assess(records)
    context = DetectorContext(cadence_status=Verification.VERIFIED, cadence_seconds=21600, cadence_refs=[provenance.resource_url])
    flatline = detect_flatline(clean, len(clean)-1, context)
    dropout = detect_dropout(records, END, context)
    results = [detect(clean, i) for i in range(len(clean))]
    flags = [item for item in results if item.outcome == "FLAG"]
    eligible = [item for item in results if item.eligibility == "ELIGIBLE"]
    # Most recent flag, otherwise most recent eligible observation; deterministic,
    # auditable selection. Network review is a historical-window summary.
    selected = flags[-1] if flags else eligible[-1] if eligible else results[-1] if results else DetectorResult(detector="SPIKE", eligibility="INSUFFICIENT_HISTORY", reason="No valid observations.")
    lookup = {row.observation_id: row for row in clean}
    observation = lookup.get(selected.candidate_id)
    history = [lookup[key] for key in selected.baseline_ids]
    support = []
    if selected.outcome == "FLAG":
        support.append(f"Provider-native departure: absolute residual / scaled MAD = {selected.score:.2f}; one-step change / scaled MAD = {selected.step_score:.2f}. Both exceed experimental threshold {selected.threshold:g}; previous reading was within threshold.")
        support.append("Supporting rows and raw tokens are included; no physical sign conversion was applied.")
    elif selected.outcome == "NO_FLAG":
        support.append("No configured spike departure at this evaluated observation. This supplies no affirmative environmental evidence.")
    unavailable = ["Independent time-matched manual/reference measurement", "Logger versus portal comparison and maintenance/revision records", "Physical datum/sign interpretation and source timezone", "Verified instrument resolution and provider sentinel-value dictionary"]
    decision = triage([selected, flatline, dropout])
    return EvidencePackage(evidence_id=f"{provenance.snapshot_id}:{station.station_group_key}:v0", station=station, observation=observation, relevant_history=history, provenance=provenance, quality=quality, detectors=[selected, flatline, dropout], supporting_evidence=support, contradicting_evidence=[], unavailable_evidence=unavailable, limitations=["This is not a diagnosis of physical sensor failure.", "Pumping, genuine movement, well work and data-acquisition problems remain competing explanations, not observed counterevidence.", "An abrupt departure is a spike candidate; isolation/reversion is not established at issue time.", "Experimental 28-reading lookback, 20-reading minimum and six-MAD cutoff are uncalibrated engineering settings, not universal physical limits.", "Historical replay of previously inspected Q1 2024 data, not live monitoring or an untouched evaluation holdout.", "No known sentinel dictionary: finite numeric source codes cannot be reliably distinguished from readings."], assessment=decision.assessment, assessment_reason=decision.reason, next_check=decision.next_check, analysis_as_of=END, flagged_observations=len(flags), evaluated_observations=len(eligible), unavailable_observations=len(results) - len(eligible))
