"""Test-only server: real pinned rows with an explicitly labelled history cut.

Run with uvicorn scripts.short_history_app:app on a separate localhost port.
It is never imported by the production application.
"""
from backend.api import create_app
from backend.provider import CSVProvider


class ShortHistoryProvider:
    def load(self):
        provenance, stations, records = CSVProvider().load()
        key = next(key for key, station in stations.items() if station.label == 'Ambhasi')
        provenance = provenance.model_copy(update={
            'data_mode': 'OFFICIAL_HISTORICAL_TEST_SUBSET',
            'transformations': provenance.transformations + [
                'TEST ONLY: retained the first three real Ambhasi source rows to exercise insufficient history; no values or timestamps changed.'
            ],
            'exclusions': provenance.exclusions + ['All other records deliberately withheld for this test-only history subset.'],
        })
        return provenance, {key:stations[key]}, {key:records[key][:3]}


app = create_app(ShortHistoryProvider())
