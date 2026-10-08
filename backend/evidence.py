"""Deterministic evidence; anomaly scores never become causal confidence."""
from .models import DetectorResult, EvidencePackage, NextCheck
from .provider import END
from .quality import assess
from .spike import detect


def build_evidence(station, records, provenance):
    quality, clean = assess(records)
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
    assessment = "UNCERTAIN" if eligible else "INSUFFICIENT_EVIDENCE"
    next_check = NextCheck(action="Compare the original logger record and an independent reference measurement for this source time.", rationale="Agreement or disagreement can help distinguish a recording/transmission issue from genuine movement; verify timestamp and measurement reference before comparing.", evidence_gap_addressed="No independent measurement or device diagnostics establishes the cause.") if eligible else NextCheck(action="Recover a continuous comparable local history and resolve the stated eligibility reason.", rationale="A detector result cannot be interpreted before its prerequisites are satisfied.", evidence_gap_addressed=selected.reason)
    return EvidencePackage(evidence_id=f"{provenance.snapshot_id}:{station.station_group_key}:v0", station=station, observation=observation, relevant_history=history, provenance=provenance, quality=quality, detectors=[selected, DetectorResult(detector="FLATLINE", eligibility="UNAVAILABLE", reason="Not implemented in the first vertical slice."), DetectorResult(detector="DROPOUT", eligibility="UNAVAILABLE", reason="Not implemented in the first vertical slice; completeness is a separate quality measure.")], supporting_evidence=support, contradicting_evidence=[], unavailable_evidence=unavailable, limitations=["This is not a diagnosis of physical sensor failure.", "Pumping, genuine movement, well work and data-acquisition problems remain competing explanations, not observed counterevidence.", "An abrupt departure is a spike candidate; isolation/reversion is not established at issue time.", "Experimental 28-reading lookback, 20-reading minimum and six-MAD cutoff are uncalibrated engineering settings, not universal physical limits.", "Historical replay of previously inspected Q1 2024 data, not live monitoring or an untouched evaluation holdout.", "No known sentinel dictionary: finite numeric source codes cannot be reliably distinguished from readings."], assessment=assessment, assessment_reason="ABSTAIN: the available telemetry cannot distinguish physical movement from a telemetry problem." if eligible else "Required usable local history or detector prerequisites are unavailable.", next_check=next_check, analysis_as_of=END, flagged_observations=len(flags), evaluated_observations=len(eligible), unavailable_observations=len(results) - len(eligible))
