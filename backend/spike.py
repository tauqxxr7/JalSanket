"""Causal robust departure screening; experimental thresholds, not field validation."""
from statistics import median

from .models import DetectorResult, Observation
from .quality import CADENCE

LOOKBACK = 28
MIN_HISTORY = 20
THRESHOLD = 6.0


def detect(records: list[Observation], index: int) -> DetectorResult:
    candidate = records[index]
    history = records[max(0, index - LOOKBACK):index]
    base = dict(detector="SPIKE", candidate_id=candidate.observation_id)
    if len(history) < MIN_HISTORY:
        return DetectorResult(**base, eligibility="INSUFFICIENT_HISTORY", reason="At least 20 prior comparable acquisitions required by experimental configuration.", baseline_ids=[row.observation_id for row in history])
    segment = history + [candidate]
    if any(row.source_time is None or row.raw_numeric_value is None or row.issues for row in segment):
        return DetectorResult(**base, eligibility="UNAVAILABLE", reason="Invalid or suspect input in local reference segment.")
    if len({row.station_group_key for row in segment}) != 1:
        return DetectorResult(**base, eligibility="UNAVAILABLE", reason="Mixed station grouping is unsupported.")
    if any((b.source_time - a.source_time).total_seconds() != CADENCE for a, b in zip(segment, segment[1:])):
        return DetectorResult(**base, eligibility="UNAVAILABLE", reason="Local reference is interrupted or off the six-hour source-clock cadence.")
    values = [row.raw_numeric_value for row in history]
    center = median(values)
    scale = 1.4826 * median(abs(value - center) for value in values)
    # abs here measures deviations, never normalizes physical measurement signs.
    if scale == 0:
        return DetectorResult(**base, eligibility="UNAVAILABLE", reason="Zero robust dispersion; no verified resolution-based fallback.")
    score = abs(candidate.raw_numeric_value - center) / scale
    prior_score = abs(values[-1] - center) / scale
    step_score = abs(candidate.raw_numeric_value - values[-1]) / scale
    flagged = score > THRESHOLD and step_score > THRESHOLD and prior_score <= THRESHOLD
    return DetectorResult(**base, eligibility="ELIGIBLE", reason="Finite same-group prior history with uninterrupted source-clock cadence and nonzero MAD.", execution_status="SUCCEEDED", outcome="FLAG" if flagged else "NO_FLAG", baseline_ids=[row.observation_id for row in history], reference_median=center, robust_scale=scale, score=score, step_score=step_score, threshold=THRESHOLD)
