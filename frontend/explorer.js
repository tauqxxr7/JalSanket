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
// Small, same-origin, short-lived cache for the pinned historical snapshot.
// Rejections are never cached; refresh/retry clears all entries.
function createSnapshotReader(read, now=Date.now, maxEntries=32, ttlMs=30000) {
  const entries=new Map();
  const get=path=>{
    if(!path.startsWith('/api/stations/'))return read(path);
    const existing=entries.get(path);
    if(existing && now()<existing.expires)return existing.promise;
    entries.delete(path);
    const entry={expires:now()+ttlMs};
    entry.promise=Promise.resolve().then(()=>read(path)).catch(error=>{
      if(entries.get(path)===entry)entries.delete(path);
      throw error;
    });
    entries.set(path,entry);
    if(entries.size>maxEntries)entries.delete(entries.keys().next().value);
    return entry.promise;
  };
  get.clear=()=>entries.clear();
  return get;
}
if (typeof module!=='undefined') module.exports={filterStations,unitLabel,createSnapshotReader};
