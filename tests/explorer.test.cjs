const {test}=require('node:test');const assert=require('node:assert/strict');
const {filterStations,unitLabel}=require('../frontend/explorer.js');
const rows=[{label:'Ambhasi',district:'Buldana',station_group_key:'group-a',assessment:'UNCERTAIN'},{label:'Other',district:'Jalna',station_group_key:'group-b',assessment:'TELEMETRY_EVIDENCE'}];
const evidence={'group-b':{detectors:[{detector:'FLATLINE',outcome:'FLAG'}]}};
test('search matches supported name and internal identifier',()=>{assert.equal(filterStations(rows,'amb','','',evidence).length,1);assert.equal(filterStations(rows,'group-a','','',evidence)[0].label,'Ambhasi');});
test('combined filters use actual detector flags',()=>{assert.equal(filterStations(rows,'Other','TELEMETRY_EVIDENCE','FLATLINE',evidence).length,1);assert.equal(filterStations(rows,'','UNCERTAIN','FLATLINE',evidence).length,0);});
test('clear filters restores count',()=>assert.equal(filterStations(rows,'','','',evidence).length,2));
test('missing evidence never fabricates a pattern',()=>assert.equal(filterStations(rows,'','','SPIKE',{}).length,0));
test('unknown units are explicit',()=>assert.equal(unitLabel(null),'Units and datum unavailable'));
test('declared units preserve uncertainty',()=>assert.match(unitLabel({declared_unit:'meter'}),/datum unverified/));

const {createSnapshotReader}=require('../frontend/explorer.js');
test('snapshot requests deduplicate including concurrent reads',async()=>{
 let calls=0;const get=createSnapshotReader(async()=>({count:++calls}));
 const [a,b]=await Promise.all([get('/api/stations/a'),get('/api/stations/a')]);
 assert.deepEqual(a,b);assert.equal(calls,1);
});
test('expiry, retry clear and bounded eviction refresh data',async()=>{
 let time=0,calls=0;const get=createSnapshotReader(async()=>++calls,()=>time,2,30);
 await get('/api/stations/a');time=31;assert.equal(await get('/api/stations/a'),2);
 await get('/api/stations/b');await get('/api/stations/c');assert.equal(await get('/api/stations/a'),5);
 get.clear();assert.equal(await get('/api/stations/a'),6);
});
test('failures and network status are not retained',async()=>{
 let calls=0;const get=createSnapshotReader(async()=>{if(++calls===1)throw Error('offline');return calls;});
 await assert.rejects(get('/api/stations/a'),/offline/);
 assert.equal(await get('/api/stations/a'),2);
 await get('/api/network');await get('/api/network');assert.equal(calls,4);
});
