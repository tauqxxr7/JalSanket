"""Deterministic evidence; anomaly scores never become causal confidence."""
from .models import DetectorResult, EvidencePackage, Verification
from .eligibility import DetectorContext
from .flatline import detect_flatline
from .dropout import detect_dropout
from .triage import triage
from .provider import END
from .quality import assess
from .spike import detect


def build_evidence(station, records, provenance, detector_context: DetectorContext | None = None):
    context = detector_context or DetectorContext(cadence_status=Verification.VERIFIED, cadence_seconds=21600, cadence_refs=[provenance.resource_url])
    window_start = context.active_start if context.active_interval_status == Verification.VERIFIED else None
    window_end = context.active_end_exclusive if window_start else END
    quality, clean = assess(records, window_start, window_end) if window_start else assess(records)
    flatline_results = [detect_flatline(clean, i, context) for i in range(len(clean))]
    flatline_flags = [r for r in flatline_results if r.outcome == 'FLAG']
    flatline_eligible = [r for r in flatline_results if r.eligibility == 'ELIGIBLE']
    flatline = (flatline_flags or flatline_eligible or flatline_results or [detect_flatline([], -1, context)])[-1]
    dropout = detect_dropout(records, window_end, context)
    results = [detect(clean, i) for i in range(len(clean))]
    flags = [item for item in results if item.outcome == "FLAG"]
    eligible = [item for item in results if item.eligibility == "ELIGIBLE"]
    # Most recent flag, otherwise most recent eligible observation; deterministic,
    # auditable selection. Network review is a historical-window summary.
    selected = flags[-1] if flags else eligible[-1] if eligible else results[-1] if results else DetectorResult(detector="SPIKE", eligibility="INSUFFICIENT_HISTORY", reason="No valid observations.")
    lookup = {row.observation_id: row for row in clean}
    observation = lookup.get(selected.candidate_id)
    lookup = {row.observation_id: row for row in records}
    cited = list(dict.fromkeys(selected.baseline_ids + flatline.baseline_ids + dropout.baseline_ids + ([flatline.candidate_id] if flatline.candidate_id else [])))
    history = [lookup[key] for key in cited if key in lookup and (observation is None or key != observation.observation_id)]
    support = []
    if selected.outcome == "FLAG":
        support.append(f"Provider-native departure: absolute residual / scaled MAD = {selected.score:.2f}; one-step change / scaled MAD = {selected.step_score:.2f}. Both exceed experimental threshold {selected.threshold:g}; previous reading was within threshold.")
        support.append("Supporting rows and raw tokens are included; no physical sign conversion was applied.")
    elif selected.outcome == "NO_FLAG":
        support.append("No configured spike departure at this evaluated observation. This supplies no affirmative environmental evidence.")
    for result in (flatline, dropout):
        if result.execution_status == 'SUCCEEDED':
            support.append(f"{result.detector}: {result.outcome} over {result.window_start} to {result.window_end}; metrics {result.metrics}. {result.reason}")
    unavailable = ["Independent time-matched manual/reference measurement", "Logger versus portal comparison and maintenance/revision records", "Physical datum/sign interpretation and source timezone", "Provider sentinel-value dictionary"]
    if context.resolution_status != Verification.VERIFIED:
        unavailable.append('Verified instrument resolution')
    unavailable.extend(f'{r.detector}: {r.reason}' for r in (flatline, dropout) if r.execution_status == 'NOT_RUN')
    decision = triage([selected, flatline, dropout])
    return EvidencePackage(evidence_id=f"{provenance.snapshot_id}:{station.station_group_key}:v0", station=station, observation=observation, relevant_history=history, provenance=provenance, quality=quality, detectors=[selected, flatline, dropout], supporting_evidence=support, contradicting_evidence=[], unavailable_evidence=unavailable, limitations=["This is not a diagnosis of physical sensor failure.", "Pumping, genuine movement, well work and data-acquisition problems remain competing explanations, not observed counterevidence.", "An abrupt departure is a spike candidate; isolation/reversion is not established at issue time.", "Experimental 28-reading lookback, 20-reading minimum and six-MAD cutoff are uncalibrated engineering settings, not universal physical limits.", "Controlled synthetic demonstration, not an actual CGWB incident." if provenance.data_mode == "SYNTHETIC_DEMONSTRATION" else "Historical replay of previously inspected Q1 2024 data, not live monitoring or an untouched evaluation holdout.", "No known sentinel dictionary: finite numeric source codes cannot be reliably distinguished from readings."], assessment=decision.assessment, assessment_reason=decision.reason, next_check=decision.next_check, analysis_as_of=window_end, flagged_observations=len(flags), evaluated_observations=len(eligible), unavailable_observations=len(results) - len(eligible))
