"use strict";
// Chart geometry uses source-clock components as an ordinal scale. It does
// not assign UTC/IST to source records or make absolute-time joins.
function sourceTick(text) {
  const parts = text.split(/[-T:]/).map(Number);
  return Date.UTC(parts[0],parts[1]-1,parts[2],parts[3],parts[4],parts[5] || 0);
}
function drawHistory(rows, flaggedIds) {
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
  const chart=element('section',undefined,'panel chart-panel');chart.append(element('p','OBSERVATION HISTORY','eyebrow'),element('h2','Provider-native observations · declared meter'),drawHistory(data.plot_observations,data.flagged_ids),element('p','Source clock — timezone unverified. Original signs preserved; gaps remain open. No physical depth interpretation.','chart-caption'));
  primary.append(chart);
  const signal=element('section',undefined,'guidance');signal.append(element('p','CURRENT ASSESSMENT','eyebrow blue'),element('h2',evidence.assessment==='UNCERTAIN'?'UNCERTAIN — ABSTAIN':evidence.assessment.replaceAll('_',' ')),element('p',evidence.assessment_reason),element('p','This is not a diagnosis of physical sensor failure.'));
  const action=element('a','VIEW EVIDENCE →','primary-action');action.href=`#/evidence/${data.station.station_group_key}`;signal.append(action);primary.append(signal);
  const recent=element('section',undefined,'panel chart-panel');recent.append(element('p','SPIKE SCREENING','eyebrow'),element('h2','What changed?'),element('p',`${evidence.flagged_observations} candidate departures; ${evidence.evaluated_observations} eligible observations; ${evidence.unavailable_observations} not evaluated. No flag does not mean a healthy sensor or stable groundwater.`));primary.append(recent);
  const quality=element('section',undefined,'panel');quality.id='station-quality';quality.append(element('p','DATA QUALITY','eyebrow'),element('h2',data.quality.state));
  for(const [label,value] of [['Completeness',`${data.quality.occupied_slots}/${data.quality.expected_slots} nominal slots`],['Expected cadence','6 source-clock hours'],['Longest missing run',`${data.quality.longest_gap_seconds/3600} source-clock hours`],['Usable observations',data.quality.valid_unique_observations]])quality.append(element('p',`${label}: ${value}`));
  const eligibility=element('section',undefined,'panel');eligibility.append(element('p','DETECTOR ELIGIBILITY','eyebrow'),element('h2','What can run here?'));
  for(const detector of evidence.detectors){const row=element('div',undefined,'detector-row');row.append(element('strong',`${detector.detector} · ${detector.eligibility}`),element('p',detector.reason));eligibility.append(row);}
  const provenance=element('section',undefined,'panel');provenance.append(element('p','DATA PROVENANCE','eyebrow'),element('p','Producer: CGWB · Publisher: NWIC / NWDP'),element('p',`Internal grouping: ${data.station.station_group_key}`),element('p',data.station.identity_reason),element('p',`Retrieved ${data.provenance.retrieved_at_utc}`));
  rail.append(quality,eligibility,provenance);layout.append(primary,rail);view.append(layout);
  const tableSection=element('details',undefined,'panel details');tableSection.append(element('summary',`Exact source observations (${data.observations.length} rows)`));
  const wrap=element('div',undefined,'table-wrap'),table=element('table'),head=element('thead'),heading=element('tr');
  for(const label of ['Source row','Original time','Original value','Validation issues'])heading.append(element('th',label));head.append(heading);table.append(head);
  const body=element('tbody');for(const row of data.observations){const tr=element('tr');for(const value of [row.source_row,row.raw_timestamp,row.measurement_raw,row.issues.join(', ')||'None detected'])tr.append(element('td',String(value)));body.append(tr);}table.append(body);wrap.append(table);tableSection.append(wrap);view.append(tableSection);
}
