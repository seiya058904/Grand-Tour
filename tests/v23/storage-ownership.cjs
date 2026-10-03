'use strict';
// Real HTML engine/codec and UI callbacks; only DOM, storage and lock scheduling
// are doubles. A naturally completed TTT result is used, not a fabricated ledger.
const assert=require('node:assert/strict'),fs=require('node:fs'),{loadEngine}=require('./engine-loader.cjs');
const file=process.argv[2]||'archive/v23/Grand-Tour-V23.html',html=fs.readFileSync(file,'utf8');
function shared(locks){const data=new Map();let failRead=false,failWrite=false,failLock=false,queue=Promise.resolve();const storage={getItem:k=>{if(failRead)throw Error('read unavailable');return data.get(k)||null},setItem:(k,v)=>{if(failWrite)throw Error('quota');data.set(k,String(v))}};return {data,storage,failure:(r,w,l=false)=>{failRead=r;failWrite=w;failLock=l},locks:locks?{request:(_,fn)=>{if(failLock)return Promise.reject(Error('lock unavailable'));const next=queue.then(fn);queue=next.catch(()=>{});return next}}:null}}
function page(sh){const p=loadEngine(file,false);Object.assign(p.engine.localStorage,sh.storage);p.sandbox.window.navigator={locks:sh.locks};p.engine.loadStore();return p}
function setting(p,id,field,value){const start=html.indexOf("$('"+id+"').addEventListener('change',()=>{");assert(start>=0);let i=html.indexOf('{',start),depth=1,j=i+1;for(;depth;j++){if(html[j]==='{')depth++;if(html[j]==='}')depth--;}const code=html.slice(i+1,j-1);const node={value};let result;new Function('Store','$','persist','App','viewFor','drawRace',code)(p.engine.Store(),()=>node,(...args)=>result=p.engine.persist(...args),{race:null},()=>{},()=>{});return result}
function begin(p,id='tour'){const e=p.engine;e.Store().tour={id,playerId:0,seedBase:314159,seedOrigin:'created',timeModel:'race-world-v1',results:[]};e.App.race=new e.Race(0,0,'tour',null,314159);return e.saveActive()}
(async()=>{for(const locks of [false,true]){const sh=shared(locks),a=page(sh);await begin(a);const b=page(sh),e=a.engine,key=e.CONFIG.saveKey;
 while(!e.App.race.complete)e.App.race.tick(true);
 e.App.finishFlow={settleCount:0};e.Ceremony.prepare=()=>{};await e.finalizeRace();assert.equal(e.App.finishFlow.settleCount,1);
 const progress=JSON.parse(sh.data.get(key));await setting(b,'visualQuality','quality','low');await setting(b,'labelDensity','labelDensity','standard');let saved=JSON.parse(sh.data.get(key));assert.deepEqual(saved.tour,progress.tour);assert.deepEqual(saved.pendingCeremony,progress.pendingCeremony);assert.equal(saved.active,null);assert.equal(saved.settings.quality,'low');assert.equal(saved.settings.labelDensity,'standard');assert.equal(await b.engine.persist(),false);assert(b.engine.App.saveConflict);assert(b.nodes.get('storageWarning').textContent.includes('导出'));
 // Two independent settings patches merge without adopting the other's race.
 await e.persist({musicVolume:.2});assert.equal(JSON.parse(sh.data.get(key)).settings.quality,'low');
 e.Store().pendingCeremony=null;assert.equal(await e.persist(),true);await setting(b,'visualQuality','quality','full');assert.equal(JSON.parse(sh.data.get(key)).pendingCeremony,null);
 const stale=page(sh);e.Store().tour={...e.Store().tour,id:'replacement',results:[]};assert.equal(await e.persist(),true);assert.equal(await stale.engine.persist(),false);
 // Import uses the same CAS, plus a durable pre-import backup.
 const incoming=e.SaveCodec.decode(e.SaveCodec.encode(e.Store())).store;incoming.tour.id='imported';assert.equal(await e.persist(null,incoming,'-before-import'),true);assert(sh.data.has(key+'-before-import'));assert.equal(await stale.engine.persist(),false);
 const good=page(sh),before=sh.data.get(key);sh.failure(true,false);assert.equal(await good.engine.persist(),false);assert.equal(sh.data.get(key),before);sh.failure(false,true);assert.equal(await good.engine.persist(),false);assert.equal(sh.data.get(key),before);sh.failure(false,false,locks);if(locks)assert.equal(await good.engine.persist(),false);sh.failure(false,false);assert.equal(await good.engine.persist(),true);
 const encoded=good.engine.SaveCodec.encode(good.engine.Store());assert(encoded.progressRevision>0);assert.equal(good.engine.SaveCodec.decode(encoded).store.progressRevision,encoded.progressRevision);delete encoded.progressRevision;assert.equal(good.engine.SaveCodec.decode(encoded).store.progressRevision,0);
 // loadStore's recovered/backed-up canonical may be safely repaired; corrupt
 // canonical requires the explicit import backup path, never a normal write.
 const recovery=shared(locks),raw={...encoded,tour:{...encoded.tour,results:[{broken:true}]}};recovery.data.set(key,JSON.stringify(raw));const recovered=page(recovery);assert(recovery.data.has(key+'-recovery-backup'));assert.equal(await recovered.engine.persist(),true);
 recovery.data.set(key,'broken JSON');const broken=page(recovery);assert(broken.engine.App.blockStoreWrite);assert.equal(await broken.engine.persist(),false);const importing={...encoded,settings:{quality:'low',labelDensity:'player',musicVolume:.1}};assert.equal(await broken.engine.persist(null,importing,'-before-import'),true);assert.equal(recovery.data.get(key+'-before-import'),'broken JSON');assert.equal(JSON.parse(recovery.data.get(key)).settings.quality,'low');
 recovery.data.set(key,'broken again');const newTour=page(recovery);assert.equal(newTour.engine.backupBeforeNewTour(),true);assert.equal(recovery.data.get(key+'-before-new-tour'),'broken again');assert.equal(await begin(newTour,'recovery-new'),true);
 // beforeunload precedes pagehide: snapshot starts while the page is alive,
 // and a pending lock prevents silent navigation. Explicitly leaving anyway
 // (or browser termination without lifecycle events) cannot be guaranteed.
 const leaving=page(shared(locks));await begin(leaving);leaving.engine.App.race.tick(true);let warned=false;const event={preventDefault(){warned=true}};leaving.engine.beforeUnloadSave(event);assert.equal(warned,locks);await leaving.engine.persist();assert.equal(JSON.parse(leaving.engine.localStorage.getItem(key)).active.t,leaving.engine.App.race.t);
 if(locks){
  const concurrent=shared(true),owner=page(concurrent);await begin(owner);const old=page(concurrent);old.engine.App.race=old.engine.Race.restore(old.engine.Store().active);owner.engine.App.race.tick(true);
  const first=owner.engine.saveActive(),second=old.engine.saveActive();assert.deepEqual(await Promise.all([first,second]),[true,false]);assert.equal(JSON.parse(concurrent.data.get(key)).active.t,owner.engine.App.race.t);
  const reloaded=page(concurrent),queued=reloaded.engine.persist();reloaded.engine.loadStore();assert.equal(await queued,false,'reload invalidates queued write ownership');
 }
 console.log('PASS storage ownership, actual settings callbacks, completion, ceremony, replacement, import, failures, codec; Web Locks='+locks);
 }
 const p=loadEngine(file),e=p.engine,r=new e.Race(18),x=r.riders.find(x=>x.d.teamId!==0&&!r.gcIds.includes(x.id)&&x.d.role==='GC'&&x.d.climb>=90);for(const y of r.riders){y.x=0;y.v=10}x.x=300;x.inBreak=true;r.relations();assert.equal(r.threatFor(r.teams[0]).id,x.id);assert(r.gcSituation().rivals.some(v=>v.id===x.id));assert.equal(new Set(r.gcSituation().rivals.map(v=>v.id)).size,r.gcSituation().rivals.length);r.prior={season:{gcTimes:Array(184).fill(1000)}};r.prior.season.gcTimes[0]=0;r.prior.season.gcTimes[x.id]=200;assert.equal(r.threatFor(r.teams[0]).id,x.id);assert(r.gcSituation().rivals.some(v=>v.id===x.id));x.status='DNF';assert(!r.gcSituation().rivals.some(v=>v.id===x.id));console.log('PASS secondary GC current threat and exit');
})().catch(e=>{console.error(e);process.exitCode=1});
