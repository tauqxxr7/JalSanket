"use strict";
// Chart geometry uses source-clock components as an ordinal scale. It does
// not assign UTC/IST to source records or make absolute-time joins.
function sourceTick(text) {
  const parts = text.split(/[-T:]/).map(Number);
  return Date.UTC(parts[0],parts[1]-1,parts[2],parts[3],parts[4],parts[5] || 0);
}
function drawHistory(rows, flaggedIds, onSelect) {
  const svgNS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNS,"svg");
  svg.setAttribute("viewBox","0 0 760 300"); svg.setAttribute("role","img");
  svg.setAttribute("aria-label","Provider-native observed values over source-clock time; gaps are not joined. Exact raw readings are available in the table below.");
  svg.classList.add("history-chart");
  if (!rows.length) return svg;
  const times = rows.map(row=>sourceTick(row.source_time)), values=rows.map(row=>row.raw_numeric_value);
  const minT=Math.min(...times),maxT=Math.max(...times),minV=Math.min(...values),maxV=Math.max(...values),span=maxV-minV || 1;
  const x=t=>58+(t-minT)/(maxT-minT || 1)*678, y=v=>245-(v-minV)/span*210;
  const add=(tag,attrs,text)=>{const n=document.createElementNS(svgNS,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;svg.append(n);return n;};
  for(let i=0;i<5;i++){const value=minV+span*i/4;add('line',{x1:58,x2:736,y1:y(value),y2:y(value),class:'chart-grid'});add('text',{x:50,y:y(value)+4,'text-anchor':'end',class:'chart-label'},value.toFixed(2));}
  let segment=[];
  const flush=()=>{if(segment.length>1)add('polyline',{points:segment.join(' '),class:'chart-line'});segment=[];};
  rows.forEach((row,i)=>{
    if(i && times[i]-times[i-1]!==21600000)flush();
    segment.push(`${x(times[i])},${y(values[i])}`);
    const point=add('circle',{cx:x(times[i]),cy:y(values[i]),r:flaggedIds.includes(row.observation_id)?4:1.8,class:flaggedIds.includes(row.observation_id)?'chart-flag':'chart-point'});
    point.dataset.observation=row.observation_id;
    point.setAttribute('tabindex','0');point.setAttribute('role','button');
    point.setAttribute('aria-label',`${flaggedIds.includes(row.observation_id)?'Flagged pattern':'Observation'} ${row.raw_timestamp}: ${row.measurement_raw}`);
    point.addEventListener('click',()=>onSelect?.(row));
    point.addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();onSelect?.(row);}});
    const title=document.createElementNS(svgNS,'title');title.textContent=`${row.raw_timestamp}: ${row.measurement_raw} (source row ${row.source_row})`;point.append(title);
  });flush();
  add('text',{x:58,y:275,class:'chart-label'},rows[0].raw_timestamp);
  add('text',{x:736,y:275,'text-anchor':'end',class:'chart-label'},rows.at(-1).raw_timestamp);
  return svg;
}
function renderStation(data, evidence) {
  const view=byId('station-view');view.replaceChildren();
  const back=element('a','← NETWORK OVERVIEW');back.href='#/network';
  const header=element('header');const title=element('div');title.append(back,element('h1',`${data.station.label} · ${data.station.district}, Maharashtra`),element('p','What is happening at this station? · Historical telemetry review'));
  header.append(title,element('span',evidence.assessment.replaceAll('_',' '),'chip uncertain'));view.append(header);
  const layout=element('div',undefined,'station-layout'),primary=element('div',undefined,'station-primary'),rail=element('aside',undefined,'rail');
  const flagged=[...new Set([...data.flagged_ids,...evidence.detectors.filter(d=>d.outcome==='FLAG' && d.candidate_id).map(d=>d.candidate_id)])];
  const inspection=element('section',undefined,'panel chart-panel');inspection.id='selection-panel';inspection.setAttribute('aria-live','polite');
  let chosen=0;
  async function inspect(row){
    const request=++chosen;
    chart.querySelectorAll('circle').forEach(point=>point.classList.toggle('chart-selected',point.dataset.observation===row.observation_id));
    picker.value=row.observation_id;
    inspection.replaceChildren(element('p','Loading selected observation evidence…'));
    try{
      const selected=await get(`/api/stations/${data.station.station_group_key}/observations/${encodeURIComponent(row.observation_id)}/evidence`);
      if(request!==chosen)return;
      inspection.replaceChildren(element('p','3 · OBSERVATION → EVIDENCE → NEXT CHECK','eyebrow'),element('h2',`${row.raw_timestamp} · ${row.measurement_raw}`),element('p',unitLabel(row)));
      const names=selected.detectors.filter(d=>d.outcome==='FLAG').map(d=>d.detector);
      inspection.append(element('p',names.length?`Flagged pattern: ${names.join(', ')}`:'No flagged pattern at this selected observation.'),listBlock('Supporting evidence',selected.supporting_evidence,'No eligible pattern result.'),element('h3',selected.assessment==='UNCERTAIN'?'UNCERTAIN — ABSTAIN':selected.assessment.replaceAll('_',' ')),element('p',selected.assessment_reason),element('h3','Next discriminating check'),element('p',selected.next_check.action));
      inspection.append(element('h3','Evidence quality'),element('p',`Historical, not live. ${selected.quality.state}; ${selected.quality.occupied_slots}/${selected.quality.expected_slots} nominal slots in the review window. Datum and source timezone unverified.`));
      const link=element('a','INSPECT SELECTED EVIDENCE →','primary-action');link.href=`#/evidence/${data.station.station_group_key}?observation=${encodeURIComponent(row.observation_id)}`;inspection.append(link);
    }catch(error){if(request===chosen)inspection.replaceChildren(element('h3','Selected evidence unavailable'),element('p',error.message));}
  }
  const picker=element('select');picker.id='observation-picker';
  for(const row of data.plot_observations){const option=element('option',`${flagged.includes(row.observation_id)?'FLAG · ':''}${row.raw_timestamp} · ${row.measurement_raw}`);option.value=row.observation_id;picker.append(option);}
  picker.addEventListener('change',()=>inspect(data.plot_observations.find(row=>row.observation_id===picker.value)));
  const pickerLabel=element('label','Select an observation or flagged pattern');pickerLabel.htmlFor=picker.id;
  const chart=element('section',undefined,'panel chart-panel');chart.append(element('p','OBSERVATION HISTORY','eyebrow'),element('h2',data.provenance.data_mode==='SYNTHETIC_DEMONSTRATION'?'SYNTHETIC demonstration observations':'Provider-native observations'),element('p',unitLabel(data.plot_observations[0])),drawHistory(data.plot_observations,flagged,inspect),element('p',data.provenance.data_mode==='SYNTHETIC_DEMONSTRATION'?'SYNTHETIC modifications with benchmark-only metadata; not an actual CGWB incident. Gaps remain open.':'Source clock — timezone unverified. Original signs preserved; gaps remain open. No physical depth interpretation.','chart-caption'));
  chart.append(element('p','Blue: observed value · red: detected pattern · outlined: selected observation. Open line segments indicate missing observations.','chart-caption'),pickerLabel,picker);
  for(const detector of evidence.detectors.filter(d=>d.outcome==='FLAG')){
    const button=element('button',`Inspect ${detector.detector} pattern`,'event-button');button.type='button';
    const candidate=data.plot_observations.find(row=>row.observation_id===detector.candidate_id);
    if(candidate)button.addEventListener('click',()=>inspect(candidate));
    else button.addEventListener('click',()=>{location.hash=`#/evidence/${data.station.station_group_key}`;});
    chart.append(button);
  }
  primary.append(chart,inspection);
  const initial=data.plot_observations.find(row=>row.observation_id===evidence.detectors.find(d=>d.outcome==='FLAG'&&d.candidate_id)?.candidate_id) || data.plot_observations.find(row=>row.observation_id===evidence.observation?.observation_id) || data.plot_observations.at(-1);
  if(initial)inspect(initial);else inspection.append(element('p','No validated observation available for inspection.'));

  const signal=element('section',undefined,'guidance');signal.append(element('p','CURRENT ASSESSMENT','eyebrow blue'),element('h2',evidence.assessment==='UNCERTAIN'?'UNCERTAIN — ABSTAIN':evidence.assessment.replaceAll('_',' ')),element('p',evidence.assessment_reason),element('p','This is not a diagnosis of physical sensor failure.'));
  const action=element('a','VIEW EVIDENCE →','primary-action');action.href=`#/evidence/${data.station.station_group_key}`;signal.append(action);primary.append(signal);
  const recent=element('section',undefined,'panel chart-panel');recent.append(element('p','SPIKE SCREENING','eyebrow'),element('h2','What changed?'),element('p',`${evidence.flagged_observations} candidate departures; ${evidence.evaluated_observations} eligible observations; ${evidence.unavailable_observations} not evaluated. No flag does not mean a healthy sensor or stable groundwater.`));primary.append(recent);
  const quality=element('section',undefined,'panel');quality.id='station-quality';quality.append(element('p','DATA QUALITY','eyebrow'),element('h2',data.quality.state));
  for(const [label,value] of [['Completeness',`${data.quality.occupied_slots}/${data.quality.expected_slots} nominal slots`],['Expected cadence','6 source-clock hours'],['Longest missing run',`${data.quality.longest_gap_seconds/3600} source-clock hours`],['Usable observations',data.quality.valid_unique_observations]])quality.append(element('p',`${label}: ${value}`));
  const eligibility=element('section',undefined,'panel');eligibility.append(element('p','DETECTOR ELIGIBILITY','eyebrow'),element('h2','What can run here?'));
  for(const detector of evidence.detectors){const row=element('div',undefined,'detector-row');row.append(element('strong',`${detector.detector} · ${detector.eligibility}`),element('p',detector.reason));eligibility.append(row);}
  const provenance=element('details',undefined,'panel details');provenance.append(element('summary','Data provenance and missing metadata'),element('p','Producer: CGWB · Publisher: NWIC / NWDP'),element('p',`Internal grouping: ${data.station.station_group_key}`),element('p',data.station.identity_reason),element('p',`Retrieved ${data.provenance.retrieved_at_utc}`));
  provenance.append(element('p',unitLabel(data.plot_observations[0])),element('p','Observation times are source-clock values. Export generation time, datum and official station identifier are unavailable.'),element('p',`${data.provenance.data_mode}: not live telemetry.`));const resource=element('a','Official dataset reference');resource.href=data.provenance.resource_url;resource.target='_blank';resource.rel='noopener noreferrer';provenance.append(resource);rail.append(quality,eligibility,provenance);layout.append(primary,rail);view.append(layout);
  const tableSection=element('details',undefined,'panel details');tableSection.append(element('summary',`${data.provenance.data_mode==='SYNTHETIC_DEMONSTRATION'?'Synthetic demonstration observations':'Exact source observations'} (${data.observations.length} rows)`));
  const wrap=element('div',undefined,'table-wrap'),table=element('table'),head=element('thead'),heading=element('tr');
  for(const label of ['Source row','Source-clock time',data.provenance.data_mode==='SYNTHETIC_DEMONSTRATION'?'Demonstration value':'Original value','Validation issues'])heading.append(element('th',label));head.append(heading);table.append(head);
  const body=element('tbody');for(const row of data.observations){const tr=element('tr');for(const value of [row.source_row,row.raw_timestamp,row.measurement_raw,row.issues.join(', ')||'None detected'])tr.append(element('td',String(value)));body.append(tr);}table.append(body);wrap.append(table);tableSection.append(wrap);view.append(tableSection);
}
