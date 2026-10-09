"""Controlled contract examples, not detection-accuracy evaluation."""
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from backend.dropout import detect_dropout
from backend.eligibility import DetectorContext
from backend.flatline import detect_flatline
from backend.models import DetectorResult, Verification
from backend.triage import Corroboration, triage
from backend.evidence import build_evidence
from test_core import records, station, provenance


def context():
    # Explicit synthetic schedule/resolution; never attached to official data.
    return DetectorContext(cadence_status='VERIFIED',cadence_seconds=21600,cadence_refs=['unit:schedule'],source_clock_status='VERIFIED',source_clock_refs=['unit:clock'],resolution_status='VERIFIED',resolution=.01,resolution_refs=['unit:resolution'],active_interval_status='VERIFIED',active_start=datetime(2024,1,1),active_end_exclusive=datetime(2024,1,8,12),active_interval_refs=['unit:active'],publication_allowance_status='VERIFIED',publication_allowance_seconds=3600,publication_allowance_refs=['unit:allowance'])


def result(detector='SPIKE',outcome='NO_FLAG'):
    return DetectorResult(detector=detector,eligibility='ELIGIBLE',reason='Controlled unit fixture',execution_status='SUCCEEDED',outcome=outcome)


def test_verified_metadata_requires_traceable_value():
    with pytest.raises(ValidationError):
        DetectorContext(resolution_status='VERIFIED',resolution=.01)
    with pytest.raises(ValidationError):
        DetectorContext(resolution_status='VERIFIED',resolution=-1,resolution_refs=['unit:bad'])


def test_flatline_repeated_run_is_pattern_not_diagnosis():
    rows=records(28)
    for i in range(20,28):
        rows[i]=rows[i].model_copy(update={'raw_numeric_value':-9.8,'measurement_raw':'-9.8'})
    outcome=detect_flatline(rows,27,context())
    assert outcome.outcome=='FLAG'
    assert outcome.metrics['run_range']==0
    assert outcome.baseline_ids[-1]==rows[26].observation_id
    assert 'stability remains possible' in outcome.reason
    assert triage([outcome]).assessment=='TELEMETRY_EVIDENCE'


def test_flatline_variable_run_and_short_history():
    assert detect_flatline(records(28),27,context()).outcome=='NO_FLAG'
    assert detect_flatline(records(12),11,context()).eligibility=='INSUFFICIENT_HISTORY'


def test_flatline_unknown_resolution_never_normal():
    outcome=detect_flatline(records(),29,DetectorContext())
    assert outcome.eligibility=='UNAVAILABLE' and outcome.outcome is None


def test_flatline_stable_prior_and_gap_withhold_execution():
    rows=[r.model_copy(update={'raw_numeric_value':0.0}) for r in records()]
    assert detect_flatline(rows,29,context()).eligibility=='UNAVAILABLE'
    rows=records(30);del rows[12]
    assert detect_flatline(rows,28,context()).outcome is None


def test_flatline_has_no_lookahead():
    rows=records(40)
    before=detect_flatline(rows,29,context())
    rows[30]=rows[30].model_copy(update={'raw_numeric_value':100000})
    assert detect_flatline(rows,29,context())==before


def test_dropout_missing_slot_and_zero_are_distinct():
    rows=records(30)
    missing=rows.pop(10)
    rows[2]=rows[2].model_copy(update={'raw_numeric_value':0,'measurement_raw':'0'})
    outcome=detect_dropout(rows,datetime(2024,1,8,12),context())
    assert outcome.outcome=='FLAG'
    assert outcome.metrics['expected_slots']==30
    assert outcome.affected_source_times==[missing.source_time.isoformat()]
    assert triage([outcome]).assessment=='TELEMETRY_EVIDENCE'


def test_dropout_invalid_numbers_and_duplicates_are_present_records():
    rows=records(30)
    rows[2]=rows[2].model_copy(update={'raw_numeric_value':None,'issues':['MISSING_NUMERIC']})
    assert detect_dropout(rows+[rows[3]],datetime(2024,1,8,12),context()).outcome=='NO_FLAG'


def test_dropout_allowance_active_end_and_future_records():
    rows=records(2)
    # Noon is not due until 13:00; future data must not establish prior history.
    assert detect_dropout(rows,datetime(2024,1,1,12,30),context()).outcome=='NO_FLAG'
    due=detect_dropout(rows,datetime(2024,1,1,13),context())
    assert due.affected_source_times==['2024-01-01T12:00:00']
    assert detect_dropout(records(30),datetime(2025,1,1),context()).outcome=='NO_FLAG'
    assert detect_dropout(records(30),datetime(2023,12,31),context()).eligibility=='INSUFFICIENT_HISTORY'


@pytest.mark.parametrize('field',['cadence_status','source_clock_status','active_interval_status','publication_allowance_status'])
def test_dropout_each_unknown_prerequisite_abstains(field):
    ctx=context().model_copy(update={field:Verification.UNVERIFIED})
    outcome=detect_dropout(records(),datetime(2024,1,8,12),ctx)
    assert outcome.eligibility=='UNAVAILABLE' and outcome.outcome is None


def test_dropout_off_grid_and_ambiguous_clock_abstain():
    rows=records()
    rows[3]=rows[3].model_copy(update={'source_time':rows[3].source_time+timedelta(minutes=1)})
    assert detect_dropout(rows,datetime(2024,1,8,12),context()).eligibility=='UNAVAILABLE'
    rows[3]=rows[3].model_copy(update={'source_time':None})
    assert detect_dropout(rows,datetime(2024,1,8,12),context()).outcome is None


def test_triage_no_flag_or_spike_alone_is_not_environmental():
    for outcome in ['FLAG','NO_FLAG']:
        decision=triage([result(outcome=outcome)])
        assert decision.assessment=='UNCERTAIN'
        assert decision.next_check.evidence_gap_addressed
    assert triage([]).assessment=='INSUFFICIENT_EVIDENCE'


def test_environment_requires_verified_meaning_and_independent_affirmative_evidence():
    facts=Corroboration(supports_environmental_change=True,evidence_refs=['unit:reference'])
    assert triage([result()],facts).assessment=='UNCERTAIN'
    facts=facts.model_copy(update={'physical_semantics':Verification.VERIFIED,'comparable_independent_reference':Verification.VERIFIED})
    assert triage([result()],facts).assessment=='ENVIRONMENTAL_CHANGE_POSSIBLE'
    assert triage([result('DROPOUT','FLAG')],facts).assessment=='UNCERTAIN'
    facts=facts.model_copy(update={'conflicting_evidence':True})
    assert triage([result()],facts).assessment=='UNCERTAIN'


def test_corroboration_claim_needs_reference():
    with pytest.raises(ValidationError):
        Corroboration(supports_environmental_change=True)


def test_acquisition_diagnostics_must_be_verified():
    facts=Corroboration(supports_acquisition_problem=True,evidence_refs=['unit:logger'])
    assert triage([result()],facts).assessment=='UNCERTAIN'
    facts=facts.model_copy(update={'acquisition_diagnostics':Verification.VERIFIED})
    assert triage([result()],facts).assessment=='TELEMETRY_EVIDENCE'


def test_evidence_integrates_verified_pattern_context_and_row_citations():
    rows=records(30)
    for i in range(22,30):
        rows[i]=rows[i].model_copy(update={'raw_numeric_value':-9.8,'measurement_raw':'-9.8'})
    package=build_evidence(station(),rows,provenance(),context())
    assert package.detectors[1].outcome=='FLAG'
    assert package.assessment=='TELEMETRY_EVIDENCE'
    assert any('FLATLINE: FLAG' in item for item in package.supporting_evidence)
    cited={row.observation_id for row in package.relevant_history} | {package.observation.observation_id}
    assert set(package.detectors[1].baseline_ids).issubset(cited)
    assert 'logger' in package.next_check.action.lower()


def test_real_short_history_api_abstains_with_honest_subset_provenance():
    from fastapi.testclient import TestClient
    from scripts.short_history_app import app
    with TestClient(app) as client:
        network=client.get('/api/network').json()
        assert network['provenance']['data_mode']=='OFFICIAL_HISTORICAL_TEST_SUBSET'
        key=network['stations'][0]['station_group_key']
        detail=client.get('/api/stations/'+key).json()
        evidence=client.get('/api/stations/'+key+'/evidence').json()
        assert len(detail['observations'])==3
        assert detail['observations'][0]['measurement_raw']=='-10.54'
        assert evidence['assessment']=='INSUFFICIENT_EVIDENCE'
        assert evidence['detectors'][0]['eligibility']=='INSUFFICIENT_HISTORY'
        assert evidence['detectors'][0]['outcome'] is None
        assert len(evidence['relevant_history'])==2
        assert evidence['next_check']['evidence_gap_addressed']


def test_dropout_evidence_contains_missing_slot_and_acquisition_next_check():
    rows=records(30)
    missing=rows.pop(10)
    package=build_evidence(station(),rows,provenance(),context())
    assert package.detectors[2].affected_source_times==[missing.source_time.isoformat()]
    assert package.assessment=='TELEMETRY_EVIDENCE'
    assert any('DROPOUT: FLAG' in item for item in package.supporting_evidence)
    assert 'published portal record' in package.next_check.action
