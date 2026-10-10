"use strict";
function filterStations(items, query, state, anomaly, evidence) {
  const term=query.trim().toLocaleLowerCase();
  return items.filter(s=>`${s.label} ${s.station_group_key} ${s.district}`.toLocaleLowerCase().includes(term)
    && (!state || s.assessment===state)
    && (!anomaly || evidence[s.station_group_key]?.detectors.some(d=>d.detector===anomaly && d.outcome==='FLAG')));
}
function unitLabel(observation) {
  return observation?.declared_unit ? `Provider-declared ${observation.declared_unit}; physical meaning/datum unverified` : 'Units and datum unavailable';
}
if (typeof module!=='undefined') module.exports={filterStations,unitLabel};
