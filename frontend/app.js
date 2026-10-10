"use strict";
const byId = (id) => document.getElementById(id);
const element = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};
let evidenceCache = {};
let stations = [],
  selection = 0;
async function get(path) {
  const response = await fetch(path, { signal: AbortSignal.timeout(15000) });
  if (!response.ok)
    throw new Error(
      `Evidence API returned ${response.status}. Request ${response.headers.get("X-Request-ID") || "unavailable"}.`,
    );
  return response.json();
}
function listBlock(title, items, empty) {
  const section = element("section");
  section.append(element("h3", title));
  if (!items.length) section.append(element("p", empty));
  else {
    const ul = element("ul");
    for (const item of items) ul.append(element("li", item));
    section.append(ul);
  }
  return section;
}
function renderQueue() {
  const target = byId("queue-list");
  target.replaceChildren();
  const search = byId("station-filter").value.toLocaleLowerCase();
  const shown = filterStations(stations,search,byId('state-filter').value,byId('anomaly-filter').value,evidenceCache);
  const missing=stations.filter(s=>!evidenceCache[s.station_group_key]).length;
  byId('filtered-count').textContent = `${shown.length} of ${stations.length} stations shown${missing ? ` · Pattern evidence unavailable for ${missing}; pattern filters exclude those stations.` : ''}`;
  const params=new URLSearchParams(location.search);
  for(const [key,value] of [['q',search],['state',byId('state-filter').value],['pattern',byId('anomaly-filter').value]]) {
    if(value)params.set(key,value);else params.delete(key);
  }
  history.replaceState(null,'',`${location.pathname}${params.size?'?'+params:''}${location.hash}`);
  if (!shown.length)
    target.append(
      element("p", "No stations match this filter.", "placeholder"),
    );
  for (const station of shown) {
    const row = element("button", undefined, "queue-row");
    row.type = "button";
    row.dataset.key = station.station_group_key;
    row.setAttribute("aria-label", `Open station ${station.label}`);
    const identity = element("span");
    identity.append(
      element("strong", station.label),
      element("small", `${station.district}, Maharashtra`),
    );
    const signal = element("span");
    signal.append(
      element(
        "span",
        station.assessment.replaceAll("_", " "),
        `chip ${station.assessment === "UNCERTAIN" ? "uncertain" : "insufficient"}`,
      ),
      element(
        "small",
        `${station.flags} spike candidates · ${station.evaluated} evaluated`,
      ),
    );
    const quality = element("span", station.quality, "row-quality");
    quality.append(
      element("small", `${(station.completeness * 100).toFixed(1)}% slots`),
    );
    row.append(
      element("span", "", "marker"),
      identity,
      signal,
      quality,
      element("span", "→", "arrow"),
    );
    row.addEventListener("click", () =>
      (location.hash = `#/station/${station.station_group_key}`),
    );
    target.append(row);
  }
}
async function selectStation(key, observationId) {
  const request = ++selection;
  const body = byId("evidence-body");
  byId('back-station').href = `#/station/${key}`;
  byId('evidence-title').textContent = 'Loading evidence…';
  body.replaceChildren(element("p", "Loading evidence…", "placeholder"));
  byId("evidence").setAttribute("aria-busy", "true");
  try {
    const data = await get(observationId ? `/api/stations/${encodeURIComponent(key)}/observations/${encodeURIComponent(observationId)}/evidence` : `/api/stations/${encodeURIComponent(key)}/evidence`);
    if (request !== selection) return;
    byId("evidence-title").textContent =
      `${data.station.label} · Evidence Trail`;
    byId('back-station').href = `#/station/${key}`;
    body.replaceChildren();
    body.append(element('p','4–6 · Interpret the evidence, read the next check, then inspect provenance or export.','journey-step'));
    const download=element('button','Download evidence JSON','export-button'); download.type='button';
    download.addEventListener('click',()=>{
      const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)+'\n'],{type:'application/json'}));
      const a=element('a');a.href=url;a.download=`jalsanket-${key}-evidence.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    });body.append(download);
    const strip = element("div", undefined, "observation-strip");
    for (const [label, value] of [
      [
        `${data.provenance.data_mode === "SYNTHETIC_DEMONSTRATION" ? "SYNTHETIC VALUE" : "PROVIDER-NATIVE VALUE"} · ${unitLabel(data.observation)}`,
        data.observation?.measurement_raw ?? "Unavailable",
      ],
      [
        "SOURCE ACQUISITION TIME · ZONE UNVERIFIED",
        data.observation?.raw_timestamp ?? "Unavailable",
      ],
      ["OBSERVED SIGNAL", data.detectors.filter(d=>d.outcome==='FLAG').map(d=>d.detector).join(', ') || "No flagged pattern at this selection"],
    ]) {
      const item = element("div");
      item.append(element("span", label), element("strong", value));
      strip.append(item);
    }
    body.append(strip);
    const grid = element("div", undefined, "evidence-grid");
    grid.append(
      listBlock(
        "SUPPORTING · CONFIGURED PATTERN",
        data.supporting_evidence,
        "No eligible pattern result.",
      ),
      listBlock(
        "CONTRADICTING · OBSERVED COUNTEREVIDENCE",
        data.contradicting_evidence,
        "None established. Absence of counterevidence is not proof.",
      ),
      listBlock(
        "UNAVAILABLE EVIDENCE",
        data.unavailable_evidence,
        "None recorded.",
      ),
      listBlock(
        "LIMITATIONS & COMPETING EXPLANATIONS",
        data.limitations,
        "None recorded.",
      ),
    );
    body.append(grid);
    const assessment = element("section", undefined, "assessment");
    assessment.append(
      element(
        "h3",
        data.assessment === "UNCERTAIN"
          ? "UNCERTAIN — ABSTAIN"
          : data.assessment.replaceAll("_", " "),
      ),
      element("p", data.assessment_reason),
    );
    body.append(assessment);
    const next = element("section", undefined, "next-check");
    next.append(
      element("h3", "NEXT DISCRIMINATING CHECK"),
      element("strong", data.next_check.action),
      element("p", data.next_check.rationale),
      element("p", `Evidence gap: ${data.next_check.evidence_gap_addressed}`),
    );
    body.append(next);
    const quality = element("details", undefined, "details");
    quality.id = "quality";
    quality.append(element("summary", "Data quality & detector eligibility"));
    quality.append(
      element(
        "p",
        `${data.quality.state}: ${data.quality.valid_unique_observations} usable unique observations / ${data.quality.raw_rows} raw rows; ${data.quality.occupied_slots}/${data.quality.expected_slots} expected slots; ${data.quality.duplicate_timestamps} duplicate timestamps; ${data.quality.numeric_invalid} invalid numbers; ${data.quality.timestamp_invalid} invalid timestamps; longest missing run ${data.quality.longest_gap_seconds / 3600} source-clock hours.`,
      ),
    );
    for (const detector of data.detectors)
      quality.append(
        element(
          "p",
          `${detector.detector}: ${detector.eligibility} · ${detector.execution_status} · ${detector.outcome ?? "No result"}. ${detector.reason}`,
        ),
      );
    for (const reason of data.quality.reasons)
      quality.append(element("p", reason));
    body.append(quality);
    const provenance = element("details", undefined, "details");
    provenance.append(
      element("summary", "Source provenance & original evidence rows"),
    );
    const link = element("a", "Open official NWDP resource");
    link.href = data.provenance.resource_url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    provenance.append(link,
      element('p',`Observation time: ${data.observation?.raw_timestamp || 'Unavailable'} (source clock; timezone unverified).`),
      element('p','Export/snapshot generation time: unavailable. Retrieval time below is distinct from observation time.'),
      element('p',unitLabel(data.observation)),
      element('p',`${data.provenance.data_mode}: historical data, never live telemetry. Official station identifier unavailable.`));
    for (const transformation of data.provenance.transformations)
      provenance.append(element('p', transformation));
    provenance.append(
      element(
        "p",
        `Producer: ${data.provenance.producer}. Publisher: ${data.provenance.publisher}. Retrieved ${data.provenance.retrieved_at_utc}.`,
      ),
      element(
        "p",
        `Internal grouping: ${data.station.station_group_key}. ${data.station.identity_reason}`,
      ),
      element("p", `Full-source SHA-256: ${data.provenance.sha256}`),
      element(
        "p",
        `Configuration: ${data.detectors[0].config_version}. ${data.provenance.exclusions.join(" ")}`,
      ),
    );
    const wrap = element("div", undefined, "table-wrap"),
      table = element("table"),
      head = element("thead"),
      tr = element("tr");
    for (const name of [
      "Source CSV row",
      "Original timestamp",
      data.provenance.data_mode === "SYNTHETIC_DEMONSTRATION" ? "Demonstration value" : "Original value",
    ])
      tr.append(element("th", name));
    head.append(tr);
    table.append(head);
    const rows = element("tbody");
    for (const observation of [
      ...data.relevant_history,
      ...(data.observation ? [data.observation] : []),
    ]) {
      const r = element("tr");
      for (const value of [
        observation.source_row,
        observation.raw_timestamp,
        observation.measurement_raw,
      ])
        r.append(element("td", String(value)));
      rows.append(r);
    }
    table.append(rows);
    wrap.append(table);
    provenance.append(wrap);
    body.append(provenance);
    window.scrollTo(0,0);
  } catch (error) {
    if (request === selection) {
      byId("evidence-title").textContent = "Evidence could not be loaded";
      body.replaceChildren(element("p", error.message, "placeholder"));
    }
  } finally {
    if (request === selection)
      byId("evidence").setAttribute("aria-busy", "false");
  }
}
async function load() {
  byId("error").hidden = true;
  try {
    const data = await get("/api/network");
    stations = data.stations;
    evidenceCache={};
    await Promise.all(stations.map(async s=>{try{evidenceCache[s.station_group_key]=await get(`/api/stations/${s.station_group_key}/evidence`);}catch{evidenceCache[s.station_group_key]=null;}}));
    byId('review-window').textContent = `${data.window_start.slice(0,10)} → ${data.window_end_exclusive.slice(0,10)} (end exclusive)`;
    byId('data-mode').textContent = data.provenance.data_mode.replaceAll('_',' ');
    byId("source").replaceChildren(
      element("strong", "SOURCE · CGWB / NWDP"),
      element(
        "span",
        `MODE · ${data.provenance.data_mode.replaceAll("_", " ")}`,
      ),
      element(
        "span",
        `RETRIEVED · ${data.provenance.retrieved_at_utc.slice(0, 10)}`,
      ),
      element("span", "FRESHNESS · HISTORICAL, NOT LIVE"),
    );
    byId("flag-count").textContent = stations.reduce(
      (sum, station) => sum + station.flags,
      0,
    );
    byId("station-count").textContent = stations.length;
    byId("environment-count").textContent = stations.filter(
      (station) => station.assessment === "ENVIRONMENTAL_CHANGE_POSSIBLE",
    ).length;
    byId("abstain-count").textContent = stations.filter((station) =>
      ["UNCERTAIN", "INSUFFICIENT_EVIDENCE"].includes(station.assessment),
    ).length;
    byId("districts").textContent = [
      ...new Set(stations.map((station) => station.district)),
    ].join(" · ");
    renderQueue();
  } catch (error) {
    stations = [];
    byId("queue-list").replaceChildren(
      element(
        "p",
        "Station queue unavailable until the evidence API responds.",
        "placeholder",
      ),
    );
    byId("districts").textContent = "Source districts unavailable.";
    byId("source").textContent = "SOURCE · UNAVAILABLE";
    byId('data-mode').textContent = 'SOURCE UNAVAILABLE';
    byId('review-window').textContent = 'Window unavailable';
    for (const id of [
      "flag-count",
      "station-count",
      "environment-count",
      "abstain-count",
    ])
      byId(id).textContent = "—";
    byId("error-message").textContent = error.message;
    byId("error").hidden = false;
  }
}
function showView(view) {
  for (const name of ['network', 'station', 'evidence']) {
    const link = byId(`nav-${name}`);
    link.classList.toggle('active', name === view);
    if (name === view) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }
  document.querySelector('main > header').hidden = view !== 'network';
  document.querySelector('.metrics').hidden = view !== 'network';
  document.querySelector('.overview').hidden = view !== 'network';
  byId('station-view').hidden = view !== 'station';
  byId('evidence').hidden = view !== 'evidence';
  document.title = `JalSanket — ${view === 'network' ? 'Network overview' : view === 'station' ? 'Station Detail' : 'Evidence Detail'}`;
}
async function route() {
  const [routePath,query=''] = location.hash.split('?');
  const [,view,key] = routePath.split('/');
  const observationId=new URLSearchParams(query).get('observation');
  if (!['station','evidence'].includes(view) || !key) { ++selection; showView('network'); return; }
  showView(view);
  byId('nav-evidence').href = `#/evidence/${key}`;
  byId('nav-station').href = `#/station/${key}`;
  if (view === 'evidence') { await selectStation(key,observationId); return; }
  const request=++selection;byId('station-view').replaceChildren(element('p','Loading station…','placeholder'));
  try {
    const [data,evidence]=await Promise.all([get(`/api/stations/${encodeURIComponent(key)}`),get(`/api/stations/${encodeURIComponent(key)}/evidence`)]);
    if(request!==selection)return;
    renderStation(data,evidence);window.scrollTo(0,0);
  } catch(error) {if(request===selection)byId('station-view').replaceChildren(element('h1','Station unavailable'),element('p',error.message));}
}
window.addEventListener('hashchange',route);
document
  .querySelector('a[href="#quality"]')
  .addEventListener("click", async (event) => {
    event.preventDefault();
    if (!byId('station-view').hidden && byId('station-quality')) {
      byId('station-quality').scrollIntoView({block:'start'});
    } else if (!byId('evidence').hidden && byId("quality")) {
      byId("quality").open = true;
      byId("quality").scrollIntoView({ block: "start" });
    } else if (stations.length) {
      location.hash=`#/station/${stations[0].station_group_key}`;
    }
  });
const filters=new URLSearchParams(location.search);
byId('station-filter').value=filters.get('q') || '';
byId('state-filter').value=filters.get('state') || '';
byId('anomaly-filter').value=filters.get('pattern') || '';
byId("station-filter").addEventListener("input", renderQueue);
for(const id of ['state-filter','anomaly-filter'])byId(id).addEventListener('change',renderQueue);
byId('reset-filters').addEventListener('click',()=>{for(const id of ['station-filter','state-filter','anomaly-filter'])byId(id).value='';renderQueue();byId('station-filter').focus();});
byId('guided-demo').addEventListener('click',()=>{if(stations.length)location.hash=`#/station/${stations.find(s=>evidenceCache[s.station_group_key]?.detectors.some(d=>d.outcome==='FLAG'))?.station_group_key || stations[0].station_group_key}`;});
byId("retry").addEventListener("click", () => load().then(route));
load().then(route);
