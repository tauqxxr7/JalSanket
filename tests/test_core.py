"""Controlled unit examples, created during the event; not evaluation results."""
from datetime import datetime, timedelta, timezone
import csv
import hashlib

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.api import create_app
from backend.evidence import build_evidence
from backend.models import DetectorResult, Observation, Provenance, Station
from backend.provider import CSVProvider, GROUP_FIELDS, MEASUREMENT, SourceUnavailable, parse_row
from backend.quality import assess
from backend.spike import detect


def records(count=30):
    return [Observation(observation_id=f"unit:{i}", station_group_key="unit-group", source_row=i+2, snapshot_id="unit", measurement_raw=str(-10 + (i % 5) * .1), raw_numeric_value=-10 + (i % 5) * .1, raw_timestamp=(datetime(2024, 1, 1) + timedelta(hours=6*i)).strftime('%d-%m-%Y %H:%M'), source_time=datetime(2024, 1, 1) + timedelta(hours=6*i)) for i in range(count)]


def provenance(digest="a" * 64, size=1):
    return Provenance(snapshot_id="unit", resource_id="unit", source_url="https://example.org/unit", resource_url="https://example.org/unit", retrieved_at_utc=datetime(2026,10,8,tzinfo=timezone.utc), sha256=digest, byte_count=size, full_file=True, terms_url="https://example.org/terms", transformations=["Controlled unit fixture; not real telemetry"], exclusions=[])


def station():
    return Station(station_group_key="unit-group", label="Controlled unit fixture", district="Test", agency="Test", state="Test", grouping_basis={"fixture":"synthetic unit example"})


@pytest.mark.parametrize('value', ['-9.31', '0', '9.31', '9999'])
def test_raw_tokens_preserved_without_sign_or_sentinel_guess(value):
    row = {key: 'Test' for key in GROUP_FIELDS} | {MEASUREMENT:value,'Data Acquisition Time':'01-01-2024 06:00'}
    _, parsed = parse_row(row, 2, 'unit')
    assert parsed.measurement_raw == value
    assert parsed.raw_numeric_value == float(value)
    assert parsed.observed_at_utc is None
    assert parsed.normalization_status == 'UNVERIFIED'


@pytest.mark.parametrize('value, issue', [('', 'MISSING_NUMERIC'), ('NaN','NONFINITE_NUMERIC'), ('inf','NONFINITE_NUMERIC'), ('abc','UNPARSEABLE_NUMERIC')])
def test_bad_numeric_is_not_zero(value, issue):
    row = {key:'Test' for key in GROUP_FIELDS} | {MEASUREMENT:value, 'Data Acquisition Time':'invalid'}
    _, parsed = parse_row(row, 2, 'unit')
    assert parsed.raw_numeric_value is None
    assert issue in parsed.issues
    assert parsed.source_time is None


def test_models_reject_nonfinite_unknown_fields_and_invented_timezone():
    row = records()[0].model_dump()
    for change in [{'raw_numeric_value':float('nan')}, {'unexpected':'field'}, {'source_time':datetime.now(timezone.utc)}]:
        with pytest.raises(ValidationError):
            Observation(**(row | change))


def test_no_false_normality_contract():
    with pytest.raises(ValidationError):
        DetectorResult(detector='SPIKE', eligibility='UNAVAILABLE', reason='missing', outcome='NO_FLAG')


def test_spike_positive_and_negative_departures():
    for value in [-30, 10]:
        rows = records()
        rows[-1] = rows[-1].model_copy(update={'raw_numeric_value':value, 'measurement_raw':str(value)})
        result = detect(rows, 29)
        assert result.outcome == 'FLAG'
        assert result.reference_median < 0
        assert rows[-1].observation_id not in result.baseline_ids


def test_clean_pattern_is_no_flag_not_environmental():
    evidence = build_evidence(station(), records(), provenance())
    assert evidence.detectors[0].outcome == 'NO_FLAG'
    assert evidence.assessment == 'UNCERTAIN'
    assert 'ABSTAIN' in evidence.assessment_reason
    assert evidence.next_check.evidence_gap_addressed


def test_flag_without_independent_evidence_abstains():
    rows = records()
    rows[-1] = rows[-1].model_copy(update={'raw_numeric_value':-40})
    evidence = build_evidence(station(), rows, provenance())
    assert evidence.flagged_observations == 1
    assert evidence.assessment == 'UNCERTAIN'
    assert evidence.contradicting_evidence == []
    assert evidence.unavailable_evidence


def test_short_history_and_zero_scale_abstain():
    assert detect(records(10),9).eligibility == 'INSUFFICIENT_HISTORY'
    rows = [row.model_copy(update={'raw_numeric_value':-10}) for row in records()]
    assert detect(rows,29).eligibility == 'UNAVAILABLE'
    assert detect(rows,29).outcome is None


def test_gap_does_not_get_compressed_into_valid_history():
    rows = records()
    del rows[15]
    result = detect(rows,len(rows)-1)
    assert result.eligibility == 'UNAVAILABLE'
    assert 'interrupted' in result.reason


def test_no_lookahead():
    rows = records(35)
    before = detect(rows,29)
    rows[30] = rows[30].model_copy(update={'raw_numeric_value':99999})
    assert detect(rows,29) == before


def test_gradual_threshold_crossing_is_not_an_abrupt_spike():
    rows = records()
    # Stable low-amplitude history followed by incremental movement. The last
    # point can leave the local envelope without an isolated one-step jump.
    values = [-10 + .01 * (i % 3) for i in range(22)] + [-10.03,-10.04,-10.05,-10.06,-10.07,-10.08,-10.09,-10.10]
    rows = [row.model_copy(update={'raw_numeric_value':value}) for row,value in zip(rows,values)]
    assert detect(rows,29).outcome == 'NO_FLAG'


def test_pinned_real_gradual_departure_is_not_spike():
    _, stations, rows = CSVProvider().load()
    key = next(key for key, value in stations.items() if value.label == 'Bharosa_1')
    _, clean = assess(rows[key])
    index = next(i for i,row in enumerate(clean) if row.raw_timestamp == '19-01-2024 06:00')
    result = detect(clean,index)
    assert result.score > result.threshold
    assert result.step_score < result.threshold
    assert result.outcome == 'NO_FLAG'


def test_quality_counts_conflicting_duplicates_and_missing_slots():
    rows = records()
    conflict = rows[10].model_copy(update={'raw_numeric_value':-900, 'observation_id':'conflict'})
    quality, clean = assess(rows + [conflict])
    assert quality.raw_rows == 31
    assert quality.duplicate_timestamps == 1
    assert quality.conflicting_timestamps == 1
    assert quality.valid_unique_observations == 29
    assert quality.expected_slots == 364
    assert quality.completeness == 29 / 364
    assert rows[10].source_time not in [row.source_time for row in clean]


def test_exact_duplicate_collapses_with_audit_count():
    rows = records()
    quality, clean = assess(rows + [rows[0]])
    assert len(clean) == 30
    assert quality.duplicate_timestamps == 1
    assert quality.conflicting_timestamps == 0


def test_unimplemented_detectors_have_no_normal_result():
    evidence = build_evidence(station(), records(), provenance())
    for detector in evidence.detectors[1:]:
        assert detector.eligibility == 'UNAVAILABLE'
        assert detector.outcome is None


def test_provider_validates_custody_and_actual_csv(tmp_path):
    raw = tmp_path/'raw'
    raw.mkdir()
    path = raw/'official.csv'
    with path.open('w',newline='',encoding='utf-8') as stream:
        writer = csv.DictWriter(stream,fieldnames=GROUP_FIELDS+[MEASUREMENT,'Data Acquisition Time'])
        writer.writeheader()
        writer.writerow({key:'Test' for key in GROUP_FIELDS} | {'Station':'Ambhasi',MEASUREMENT:'-4.2','Data Acquisition Time':'01-01-2024 00:00'})
    manifest = provenance(hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_size)
    (tmp_path/'manifest.json').write_text(manifest.model_dump_json(),encoding='utf-8')
    _, stations, rows = CSVProvider(tmp_path).load()
    assert len(stations) == 1
    assert next(iter(rows.values()))[0].measurement_raw == '-4.2'
    path.write_bytes(path.read_bytes()+b'altered')
    with pytest.raises(SourceUnavailable,match='checksum'):
        CSVProvider(tmp_path).load()


class UnitProvider:
    def load(self):
        return provenance(), {'unit-group':station()}, {'unit-group':records()}


def test_api_network_evidence_bounds_headers():
    with TestClient(create_app(UnitProvider())) as client:
        response = client.get('/api/network')
        assert response.status_code == 200
        assert response.json()['stations'][0]['assessment'] == 'UNCERTAIN'
        assert response.headers['x-request-id']
        assert "frame-ancestors 'none'" in response.headers['content-security-policy']
        assert client.get('/api/stations/unit-group/evidence').status_code == 200
        assert client.get('/api/stations/unknown/evidence').status_code == 404
        assert client.get('/api/network?url=https://evil.example').status_code == 422
        assert client.post('/api/network').status_code == 405
        assert 'access-control-allow-origin' not in client.get('/api/network',headers={'Origin':'https://evil.example'}).headers


def test_missing_source_returns_503(tmp_path):
    with TestClient(create_app(CSVProvider(tmp_path))) as client:
        assert client.get('/api/health').status_code == 503
        assert client.get('/api/network').status_code == 503
        assert client.get('/').status_code == 200


def test_real_pinned_official_provider_integration():
    manifest, stations, rows = CSVProvider().load()
    assert manifest.full_file
    assert len(stations) == 5
    assert sum(map(len,rows.values())) == 1776
    for key, value in stations.items():
        result = build_evidence(value,rows[key],manifest)
        assert result.evaluated_observations > 0
        assert result.observation.snapshot_id == manifest.snapshot_id
        assert result.assessment in ['UNCERTAIN','INSUFFICIENT_EVIDENCE']
