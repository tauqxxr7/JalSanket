// Real local API reads through the app reader; not a browser paint benchmark.
const fs=require('node:fs'), vm=require('node:vm'), path=require('node:path');
(async()=>{
 const base=process.env.JALSANKET_BASE_URL||'http://127.0.0.1:8768';
 const network=await (await fetch(base+'/api/network')).json();
 const key=network.stations[0].station_group_key;
 const evidence=await (await fetch(base+`/api/stations/${key}/evidence`)).json();
 const station=`/api/stations/${key}`, selected=station+'/observations/'+encodeURIComponent(evidence.observation.observation_id)+'/evidence';
 const sequence=[station,station+'/evidence',selected,selected,station];
 const runs=[];
 for(let i=0;i<5;i++){
  let requests=0, bytes=0;
  const context=vm.createContext({AbortSignal,Date,Map,Promise,fetch:async p=>{requests++;const r=await fetch(base+p);bytes+=Number(r.headers.get('content-length')||0);return r;}});
  vm.runInContext(fs.readFileSync('frontend/explorer.js','utf8'),context);
  vm.runInContext(fs.readFileSync('frontend/app.js','utf8').split('function listBlock')[0],context);
  const start=performance.now();
  for(const p of sequence)await vm.runInContext(`get(${JSON.stringify(p)})`,context);
  runs.push({requests,responseBytes:bytes,elapsedMs:+(performance.now()-start).toFixed(2)});
 }
 const files=[];function walk(p){for(const e of fs.readdirSync(p,{withFileTypes:true})){const f=path.join(p,e.name);if(e.isDirectory())walk(f);else files.push(f);}}walk('dist');
 const result={scope:'five sequential API reads, five fresh readers, local warm server; no browser rendering metric',sequence,runs,medianMs:runs.map(x=>x.elapsedMs).sort((a,b)=>a-b)[2],buildBytes:files.reduce((n,p)=>n+fs.statSync(p).size,0)};
 console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
