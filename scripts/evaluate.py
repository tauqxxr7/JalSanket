"""Reproducible paired controlled injections; no field failure labels or tuning."""
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median

from backend.dropout import detect_dropout
from backend.eligibility import DetectorContext
from backend.flatline import detect_flatline
from backend.provider import CSVProvider, COHORT, ROOT, parse_row
from backend.spike import detect

CONFIG_PATH = ROOT / 'scripts/evaluation_config.json'
LIMITATION = 'This evaluates detection of controlled synthetic anomaly patterns. It does not establish accuracy for diagnosing real physical sensor failures.'


def windows(config, manifest):
    start,end=map(datetime.fromisoformat,config['evaluation_window'])
    groups=defaultdict(list); exclusions=Counter()
    with (ROOT/'data/raw/official.csv').open(encoding='utf-8-sig',newline='') as stream:
        for line,row in enumerate(csv.DictReader(stream),2):
            if row['Station'] not in COHORT:
                continue
            station,record=parse_row(row,line,manifest.snapshot_id)
            if record.source_time is None:
                exclusions['unparseable_time_cannot_assign_to_split']+=1
            elif start <= record.source_time < end:
                groups[station.station_group_key].append(record)
    result=[];length=config['window_samples']
    for key,rows in sorted(groups.items()):
        counts=Counter(r.source_time for r in rows)
        segment=[]
        for row in sorted(rows,key=lambda r:r.source_time):
            if row.issues or counts[row.source_time]>1:
                exclusions['invalid_or_duplicate_rows']+=1
                exclusions['incomplete_segment_rows']+=len(segment);segment=[]
                continue
            if segment and (row.source_time-segment[-1].source_time).total_seconds()!=21600:
                exclusions['incomplete_segment_rows']+=len(segment);segment=[]
            segment.append(row)
            if len(segment)==length:
                result.append(segment);segment=[]
        exclusions['incomplete_segment_rows']+=len(segment)
    return result,dict(exclusions)


def benchmark_context(rows,config):
    return DetectorContext(cadence_status='VERIFIED',cadence_seconds=21600,cadence_refs=['synthetic-benchmark:six-hour-grid'],source_clock_status='VERIFIED',source_clock_refs=['synthetic-benchmark:contiguous-source-clock-window'],resolution_status='VERIFIED',resolution=config['synthetic_resolution'],resolution_refs=['synthetic-benchmark:assumed-resolution-not-official'],active_interval_status='VERIFIED',active_start=rows[0].source_time,active_end_exclusive=rows[-1].source_time+timedelta(hours=6),active_interval_refs=['synthetic-benchmark:declared-active-window'],publication_allowance_status='VERIFIED',publication_allowance_seconds=config['synthetic_publication_allowance_seconds'],publication_allowance_refs=['synthetic-benchmark:declared-allowance-not-official'])


def summarize(cases):
    counts=Counter();latencies=[]
    for case in cases:
        positive=case['injected'];flag=case['outcome']=='FLAG'
        if case['outcome'] is None:
            counts['abstained_positive' if positive else 'abstained_negative']+=1
            if positive: counts['fn']+=1
        else:
            counts['tp' if positive and flag else 'fn' if positive else 'fp' if flag else 'tn']+=1
        if positive and flag and case['latency_hours'] is not None:latencies.append(case['latency_hours'])
    tp,fp,fn,tn=[counts[k] for k in ('tp','fp','fn','tn')]
    ratio=lambda a,b:a/b if b else None
    return dict(counts) | {'precision':ratio(tp,tp+fp),'recall':ratio(tp,tp+fn),'f1':ratio(2*tp,2*tp+fp+fn),'false_positive_rate_on_executed_unmodified_controls':ratio(fp,fp+tn),'execution_coverage':ratio(len(cases)-counts['abstained_positive']-counts['abstained_negative'],len(cases)),'median_detection_latency_source_hours':median(latencies) if latencies else None,'detected_latency_count':len(latencies),'cases':len(cases)}


def run():
    config=json.loads(CONFIG_PATH.read_text())
    manifest,_,_=CSVProvider().load() # Verify full pinned bytes before split selection.
    samples,exclusions=windows(config,manifest)
    if not samples:raise RuntimeError('No usable evaluation windows; no metrics generated')
    rng=random.Random(config['seed']);cases=[];target=config['injection_index']
    for number,original in enumerate(samples):
        context=benchmark_context(original,config)
        scale_values=[r.raw_numeric_value for r in original[:target]]
        center=median(scale_values);scale=1.4826*median(abs(v-center) for v in scale_values)
        multiplier=rng.choice(config['spike_scale_multipliers']);direction=rng.choice([-1,1])
        flat_length=rng.choice(config['flatline_lengths']);drop_length=rng.choice(config['dropout_lengths'])
        for detector in ['SPIKE','FLATLINE','DROPOUT']:
            for injected in [False,True]:
                rows=list(original);modifications=[];latency=None
                if detector=='SPIKE':
                    if injected:
                        value=rows[target].raw_numeric_value+direction*multiplier*(scale or config['synthetic_resolution'])
                        modifications=[{'source_row':rows[target].source_row,'before':rows[target].measurement_raw,'after':repr(value)}]
                        rows[target]=rows[target].model_copy(update={'raw_numeric_value':value,'measurement_raw':repr(value)})
                    output=detect(rows,target)
                    if output.outcome=='FLAG':latency=0.0
                    severity={'scaled_amplitude':multiplier,'direction':direction}
                elif detector=='FLATLINE':
                    stop=target+flat_length
                    if injected:
                        for i in range(target,stop):
                            modifications.append({'source_row':rows[i].source_row,'before':rows[i].measurement_raw,'after':original[target-1].measurement_raw})
                            rows[i]=rows[i].model_copy(update={'raw_numeric_value':original[target-1].raw_numeric_value,'measurement_raw':original[target-1].measurement_raw})
                    outputs=[detect_flatline(rows,i,context) for i in range(target,stop)]
                    flagged=[(i,r) for i,r in enumerate(outputs) if r.outcome=='FLAG']
                    output=flagged[0][1] if flagged else next((r for r in reversed(outputs) if r.outcome is not None),outputs[-1])
                    if flagged:latency=flagged[0][0]*6.0
                    severity={'repeated_samples':flat_length}
                else:
                    if injected:
                        modifications=[{'source_row':r.source_row,'removed_timestamp':r.raw_timestamp} for r in rows[target:target+drop_length]]
                        del rows[target:target+drop_length]
                    allowance=context.publication_allowance_seconds
                    output=detect_dropout(rows,original[-1].source_time+timedelta(seconds=allowance),context)
                    if output.outcome=='FLAG':
                        for i in range(target,target+drop_length):
                            issue=original[i].source_time+timedelta(seconds=allowance)
                            prefix=[r for r in rows if r.source_time<=issue]
                            if detect_dropout(prefix,issue,context).outcome=='FLAG':
                                latency=(issue-original[target].source_time).total_seconds()/3600;break
                    severity={'removed_samples':drop_length}
                cases.append({'window':number,'detector':detector,'injected':injected,'station_group_key':original[0].station_group_key,'source_rows':[r.source_row for r in original],'window_start':original[0].raw_timestamp,'window_end':original[-1].raw_timestamp,'severity':severity,'modifications':modifications,'eligibility':output.eligibility,'reason':output.reason,'outcome':output.outcome,'latency_hours':latency if injected else None,'config_version':output.config_version})
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'backend/spike.py',ROOT/'backend/flatline.py',ROOT/'backend/dropout.py',CONFIG_PATH]}
    report={'limitation':LIMITATION,'generated_at_utc':datetime.now(timezone.utc).isoformat(),'provenance':manifest.model_dump(mode='json'),'configuration':config,'implementation_hashes':hashes,'split_note':'Q1 used for development; Q2 first evaluated after config was saved. No tuning was performed on Q2 results. Same stations, separate source-time windows; this is not spatial generalization.','windows':len(samples),'exclusions':exclusions,'metrics':{d:summarize([c for c in cases if c['detector']==d]) for d in ['SPIKE','FLATLINE','DROPOUT']},'cases':cases}
    output=ROOT/'evaluation';output.mkdir(exist_ok=True)
    (output/'results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'windows':len(samples),'metrics':report['metrics'],'limitation':LIMITATION},indent=2))
    return report


if __name__=='__main__':run()
