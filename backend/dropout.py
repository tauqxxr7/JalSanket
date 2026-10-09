"""Missing expected records in a verified active source-clock schedule."""
from datetime import datetime, timedelta

from .eligibility import DetectorContext
from .models import DetectorResult, Observation, Verification


def detect_dropout(records: list[Observation], as_of: datetime, context: DetectorContext) -> DetectorResult:
    base = dict(detector='DROPOUT', config_version='dropout-v0-explicit-active-schedule')
    facts = [('cadence',context.cadence_status),('source-clock consistency',context.source_clock_status),('active interval',context.active_interval_status),('publication allowance',context.publication_allowance_status)]
    missing = [name for name,status in facts if status != Verification.VERIFIED]
    if missing:
        return DetectorResult(**base, eligibility='UNAVAILABLE', reason='Unverified prerequisites: '+', '.join(missing)+'. Historical file end is not a current outage.')
    if as_of.utcoffset() is not None:
        return DetectorResult(**base, eligibility='UNAVAILABLE', reason='Analysis as-of and schedule must use the same source-clock basis.')
    if len({row.station_group_key for row in records}) > 1 or any(row.source_time is None for row in records):
        return DetectorResult(**base, eligibility='UNAVAILABLE', reason='Ambiguous acquisition times or mixed station grouping prevent missing-record analysis.')
    start, end = context.active_start, context.active_end_exclusive
    cutoff = min(end, as_of-timedelta(seconds=context.publication_allowance_seconds))
    # A slot is due at its acquisition time plus the explicit allowance.
    times = {r.source_time for r in records if start <= r.source_time < end and r.source_time <= as_of}
    if len(times) < 2:
        return DetectorResult(**base, eligibility='INSUFFICIENT_HISTORY', reason='At least two prior acquisitions in the verified active interval are required.')
    cadence = context.cadence_seconds
    if any((t-start).total_seconds() % cadence for t in times):
        return DetectorResult(**base, eligibility='UNAVAILABLE', reason='Observed acquisition times conflict with the verified schedule phase.')
    if (end-start).total_seconds()/cadence > 100000:
        return DetectorResult(**base, eligibility='UNAVAILABLE', reason='Requested active schedule exceeds the bounded 100000-slot prototype limit.')
    expected=[]
    cursor=start
    while cursor < end and cursor <= cutoff:
        expected.append(cursor)
        cursor += timedelta(seconds=cadence)
    if not expected:
        return DetectorResult(**base, eligibility='INSUFFICIENT_HISTORY', reason='No scheduled acquisitions are due at this analysis time.')
    absent=[time for time in expected if time not in times]
    refs=context.cadence_refs+context.source_clock_refs+context.active_interval_refs+context.publication_allowance_refs
    return DetectorResult(**base, eligibility='ELIGIBLE', execution_status='SUCCEEDED', outcome='FLAG' if absent else 'NO_FLAG', reason='Missing expected records after the verified publication allowance; acquisition, transmission, publication and scheduled-operation explanations require checking.', window_start=start, window_end=expected[-1], affected_source_times=[t.isoformat() for t in absent], baseline_ids=[r.observation_id for r in records if r.source_time in times], metrics={'expected_slots':len(expected),'missing_slots':len(absent),'publication_allowance_seconds':context.publication_allowance_seconds}, evidence_refs=refs)
