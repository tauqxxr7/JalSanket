"""Experimental low-variation pattern, never a stuck-sensor diagnosis."""
from .eligibility import DetectorContext
from .models import DetectorResult, Observation, Verification

RUN_LENGTH = 8
PRIOR_LENGTH = 20


def detect_flatline(records: list[Observation], index: int, context: DetectorContext) -> DetectorResult:
    base = dict(detector='FLATLINE', config_version='flatline-v0-experimental-8-20-half-resolution')
    if context.resolution_status != Verification.VERIFIED:
        return DetectorResult(**base, eligibility='UNAVAILABLE', reason='Verified measurement resolution and its evidence are unavailable; export decimal places alone are insufficient.')
    if context.cadence_status != Verification.VERIFIED or context.source_clock_status != Verification.VERIFIED:
        return DetectorResult(**base, eligibility='UNAVAILABLE', reason='Verified cadence and internally consistent source-clock basis are required.')
    segment = records[max(0, index + 1 - RUN_LENGTH - PRIOR_LENGTH):index + 1]
    if len(segment) < RUN_LENGTH + PRIOR_LENGTH:
        return DetectorResult(**base, eligibility='INSUFFICIENT_HISTORY', reason='Requires eight consecutive run samples and twenty prior comparable samples.')
    base.update(candidate_id=segment[-1].observation_id)
    if any(row.source_time is None or row.raw_numeric_value is None or row.issues for row in segment) or len({row.station_group_key for row in segment}) != 1:
        return DetectorResult(**base, eligibility='UNAVAILABLE', reason='Invalid input or mixed station grouping in comparison window.')
    if any((b.source_time-a.source_time).total_seconds() != context.cadence_seconds for a,b in zip(segment,segment[1:])):
        return DetectorResult(**base, eligibility='UNAVAILABLE', reason='Gaps, duplicates or inconsistent spacing interrupt the run; missing values are not repetitions.')
    prior, run = segment[:-RUN_LENGTH], segment[-RUN_LENGTH:]
    prior_values, run_values = [r.raw_numeric_value for r in prior], [r.raw_numeric_value for r in run]
    prior_range, run_range = max(prior_values)-min(prior_values), max(run_values)-min(run_values)
    if prior_range <= 5 * context.resolution:
        return DetectorResult(**base, eligibility='UNAVAILABLE', reason='Prior variability does not exceed five verified resolution increments; persistent stability cannot support this comparison.')
    tolerance = context.resolution / 2
    return DetectorResult(**base, eligibility='ELIGIBLE', execution_status='SUCCEEDED', outcome='FLAG' if run_range <= tolerance else 'NO_FLAG', reason='Comparable uninterrupted history and verified resolution support a low-variation comparison; genuine stability remains possible.', baseline_ids=[r.observation_id for r in segment[:-1]], window_start=run[0].source_time, window_end=run[-1].source_time, threshold=tolerance, metrics={'run_range':run_range,'prior_range':prior_range,'resolution':context.resolution}, evidence_refs=context.resolution_refs+context.cadence_refs+context.source_clock_refs)
