'use strict';
// Production codec, save callbacks and persistence; only storage/DOM/lock
// scheduling are doubles. No alternative implementation of ownership is used.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {loadEngine}=require('../v23/engine-loader.cjs');
const source=path.resolve(process.argv[2]||path.join(__dirname,'../../Grand-Tour-V25.html'));
const out=process.argv[3],html=fs.readFileSync(source,'utf8'),checks=[];
const sourceSHA256=crypto.createHash('sha256').update(html).digest('hex');
function shared(locks){
 const data=new Map();let queue=Promise.resolve();
 const storage={getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,String(v)),removeItem:k=>data.delete(k)};
 return {data,storage,locks:locks?{request:(_,fn)=>{const next=queue.then(fn);queue=next.catch(()=>{});return next;}}:null};
}
function page(sh){const p=loadEngine(source,false);Object.assign(p.engine.localStorage,sh.storage);p.sandbox.window.navigator={locks:sh.locks};p.engine.loadStore();return p;}
function setting(p,id,value){
 const start=html.indexOf("$('"+id+"').addEventListener('change',()=>{");assert(start>=0,'actual settings listener exists');
 let i=html.indexOf('{',start),depth=1,j=i+1;for(;depth;j++){if(html[j]==='{')depth++;if(html[j]==='}')depth--;}
 const node={value};let result;
 new Function('Store','$','persist','App','viewFor','drawRace',html.slice(i+1,j-1))(p.engine.Store(),()=>node,(...args)=>result=p.engine.persist(...args),{race:null},()=>{},()=>{});
 return result;
}
function begin(p,id){const e=p.engine;e.Store().tour={id,playerId:0,seedBase:314159,seedOrigin:'created',timeModel:'race-world-v1',results:[]};e.App.race=new e.Race(0,0,'tour',null,314159);return e.saveActive();}
async function test(name,locks,fn){try{checks.push({name,locks,pass:true,detail:await fn()});console.log('PASS',name,'locks='+locks);}catch(e){checks.push({name,locks,pass:false,error:e.stack});console.log('FAIL',name,'locks='+locks,e.message);}}
(async()=>{
 for(const locks of [false,true]){
  await test('first settings change cannot prevent the first tour save',locks,async()=>{
   const sh=shared(locks),p=page(sh),e=p.engine,key=e.CONFIG.saveKey;
   assert.equal(await setting(p,'visualQuality','low'),true);
   assert.equal(await begin(p,'first-tour'),true,'the same page must still own empty progress after changing settings');
   const raw=JSON.parse(sh.data.get(key)),reloaded=page(sh).engine;
   assert.equal(raw.tour.id,'first-tour');assert.equal(raw.settings.quality,'low');assert(raw.progressRevision>0);
   assert.equal(reloaded.Store().tour.id,'first-tour');assert.equal(reloaded.Store().active.rngState,e.App.race.rng.state);
   return {revision:raw.progressRevision,tour:raw.tour.id,quality:raw.settings.quality};
  });
  await test('two empty pages can merge settings before exactly one claims progress',locks,async()=>{
   const sh=shared(locks),a=page(sh),b=page(sh),key=a.engine.CONFIG.saveKey;
   assert.equal(await setting(a,'visualQuality','low'),true);assert.equal(await setting(b,'labelDensity','standard'),true);
   assert.deepEqual(await Promise.all([begin(a,'winner'),begin(b,'stale')]),[true,false]);
   let raw=JSON.parse(sh.data.get(key));assert.equal(raw.tour.id,'winner');assert.equal(raw.settings.quality,'low');assert.equal(raw.settings.labelDensity,'standard');
   const progress=JSON.stringify([raw.progressRevision,raw.tour,raw.active,raw.pendingCeremony]);
   assert.equal(await setting(b,'visualQuality','full'),true);assert.equal(await b.engine.persist(),false,'a settings merge must never adopt another page\'s tour');
   raw=JSON.parse(sh.data.get(key));assert.equal(JSON.stringify([raw.progressRevision,raw.tour,raw.active,raw.pendingCeremony]),progress);
   return {firstClaims:[true,false],staleSettingsMerged:true,staleProgressRejected:true};
  });
  await test('settings before legacy-key promotion retain the loaded tour ownership',locks,async()=>{
   const sh=shared(locks),seed=page(shared(false)),e=seed.engine;
   await begin(seed,'legacy-import');const saved=e.SaveCodec.encode(e.Store()),legacyKey='tour-cycling-2026-refined-v9';
   sh.data.set(legacyKey,JSON.stringify(saved));const p=page(sh),key=p.engine.CONFIG.saveKey;
   assert.equal(p.engine.Store().tour.id,'legacy-import');assert.equal(sh.data.get(key),undefined);
   assert.equal(await setting(p,'labelDensity','player'),true);
   p.engine.App.race=p.engine.Race.restore(p.engine.Store().active);p.engine.App.race.tick();
   assert.equal(await p.engine.saveActive(),true,'promoting the loaded legacy progress through a setting is still owned by this page');
   const current=JSON.parse(sh.data.get(key));assert.equal(current.active.t,p.engine.App.race.t);assert.equal(current.settings.labelDensity,'player');assert.equal(sh.data.get(legacyKey),JSON.stringify(saved),'legacy bytes remain untouched');
   return {canonicalTime:current.active.t,legacyUnchanged:true};
  });
  await test('a revision-bearing empty store is distinct from never-saved progress',locks,async()=>{
   const sh=shared(locks),stale=page(sh),owner=page(sh),e=owner.engine,key=e.CONFIG.saveKey;
   await begin(owner,'prior-tour');e.Store().tour=null;e.Store().active=null;e.App.race=null;
   assert.equal(await e.persist(),true);const raw=sh.data.get(key);assert(JSON.parse(raw).progressRevision>0);
   assert.equal(await begin(stale,'must-not-reappear'),false);assert.equal(sh.data.get(key),raw);
   return {revision:JSON.parse(raw).progressRevision,staleRejected:true};
  });
  await test('a stale setting cannot republish a tour after canonical storage disappears',locks,async()=>{
   const sh=shared(locks),p=page(sh),key=p.engine.CONFIG.saveKey;await begin(p,'old-tour');sh.data.delete(key);
   assert.equal(await setting(p,'visualQuality','low'),false,'creating canonical progress again requires ownership of its absence');
   assert.equal(sh.data.get(key),undefined);assert.equal(p.engine.Store().tour.id,'old-tour','unsaved in-memory progress remains exportable');
   return {staleRejected:true,inMemoryPreserved:true};
  });
 }
 const sourceUnchanged=crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex')===sourceSHA256;
 const report={source,sourceSHA256,sourceUnchanged,checks,passed:checks.filter(c=>c.pass).length,failed:checks.filter(c=>!c.pass).length};
 if(out)fs.writeFileSync(out,JSON.stringify(report,null,2));console.log(report.passed+'/'+checks.length+' PASS');process.exitCode=report.failed||!sourceUnchanged?1:0;
})().catch(e=>{console.error(e);process.exitCode=1;});
