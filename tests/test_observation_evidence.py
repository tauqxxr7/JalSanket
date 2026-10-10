from fastapi.testclient import TestClient
from backend.api import create_app
from backend.evidence import build_evidence
from test_core import records, station, provenance
from test_p0 import context

def test_selection_is_exact_and_does_not_reuse_a_later_flag():
    rows=records(35)
    rows[-1]=rows[-1].model_copy(update={'raw_numeric_value':-100,'measurement_raw':'-100'})
    first=build_evidence(station(),rows,provenance(),observation_id=rows[0].observation_id)
    later=build_evidence(station(),rows,provenance(),observation_id=rows[-1].observation_id)
    assert first.observation==rows[0]
    assert first.assessment=='INSUFFICIENT_EVIDENCE'
    assert later.observation==rows[-1]
    assert later.detectors[0].outcome=='FLAG'
    assert first.evidence_id!=later.evidence_id
    assert all(r.source_time<=first.observation.source_time for r in first.relevant_history)

def test_selected_flatline_matches_candidate_and_recommendation():
    rows=records(28)
    for i in range(20,28):rows[i]=rows[i].model_copy(update={'raw_numeric_value':-9.8,'measurement_raw':'-9.8'})
    result=build_evidence(station(),rows,provenance(),context(),rows[-1].observation_id)
    assert result.observation==rows[-1]
    assert result.detectors[1].candidate_id==rows[-1].observation_id
    assert result.assessment=='TELEMETRY_EVIDENCE'
    assert 'logger' in result.next_check.action

def test_observation_api_preserves_old_endpoint_and_rejects_unknown():
    rows=records()
    class Provider:
        def load(self):return provenance(),{'unit-group':station()},{'unit-group':rows}
    with TestClient(create_app(Provider())) as client:
        assert client.get('/api/stations/unit-group/evidence').status_code==200
        response=client.get('/api/stations/unit-group/observations/unit:2/evidence')
        assert response.status_code==200
        assert response.json()['observation']['observation_id']=='unit:2'
        assert client.get('/api/stations/unit-group/observations/missing/evidence').status_code==404
        assert client.get('/api/stations/missing/observations/unit:2/evidence').status_code==404
