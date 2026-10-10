"""Separate, visibly synthetic demo built from a recorded evaluation injection."""
import csv
import json

from backend.api import create_app
from backend.provider import CSVProvider, ROOT, parse_row
from scripts.evaluate import benchmark_context


class SyntheticDemoProvider:
    def __init__(self):self.contexts={}

    def load(self):
        manifest,_,_=CSVProvider().load()
        report=json.loads((ROOT/'evaluation/results.json').read_text(encoding='utf-8'))
        if report['provenance']['sha256'] != manifest.sha256:
            raise ValueError('Evaluation snapshot differs from current source')
        case=next(c for c in report['cases'] if c['detector']=='FLATLINE' and c['injected'] and c['outcome']=='FLAG')
        selected=set(case['source_rows']);records=[]
        with (ROOT/'data/raw/official.csv').open(encoding='utf-8-sig',newline='') as stream:
            for line,row in enumerate(csv.DictReader(stream),2):
                if line in selected:
                    station,observation=parse_row(row,line,manifest.snapshot_id)
                    records.append(observation)
        changes={m['source_row']:m for m in case['modifications']}
        original=list(records)
        for i,row in enumerate(records):
            if row.source_row in changes:
                change=changes[row.source_row]
                if row.measurement_raw!=change['before']:raise ValueError('Original value mismatch')
                records[i]=row.model_copy(update={'measurement_raw':change['after'],'raw_numeric_value':float(change['after']),'observation_id':row.observation_id+':synthetic'})
        key=station.station_group_key
        self.contexts[key]=benchmark_context(original,report['configuration'])
        manifest=manifest.model_copy(update={'data_mode':'SYNTHETIC_DEMONSTRATION','transformations':manifest.transformations+['SYNTHETIC DEMONSTRATION: controlled flatline injection from evaluation/results.json; not an actual CGWB incident.',json.dumps(case['modifications'])],'exclusions':manifest.exclusions+['Only one synthetic evaluation window is shown. Resolution/operation/publication metadata are benchmark assumptions, not verified official facts.']})
        return manifest,{key:station},{key:records}


provider=SyntheticDemoProvider()
app=create_app(provider,provider.contexts)
