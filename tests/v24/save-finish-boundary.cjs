'use strict';
// Execute the production script without ?test; only ceremony presentation is stubbed.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {loadEngine}=require('../v23/engine-loader.cjs');
const source=process.argv[2]||path.join(__dirname,'../../Grand-Tour-V24.html'),out=process.argv[3];
const E=loadEngine(source,false).engine,plain=x=>JSON.parse(JSON.stringify(x)),checks=[];
function test(name,fn){try{checks.push({name,pass:true,detail:fn()});console.log('PASS',name);}catch(e){checks.push({name,pass:false,error:e.stack});console.log('FAIL',name,e.message.slice(0,300));}}
function store(active,version=9){return {version,progressRevision:3,pendingCeremony:null,tour:{id:'finish-boundary-regression',playerId:0,seedBase:314159,timeModel:active?.timeModel||'race-world-v1',results:[]},active,settings:{quality:'full',labelDensity:'calm',musicVolume:.55}};}
// Integrator intents are recomputed on the next tick; compact saves omit audit history.
function state(s){const value=plain(s);delete value.audit;for(const r of value.riders){delete r._followMaxAccel;delete r._following;}return value;}
function advance(r,until){while(!until(r)&&r.t<4000)r.tick();assert(until(r),'natural race reached requested state');return r;}
const natural=advance(new E.Race(0,0,'tour',null,314159),r=>r.finishedCount>0),snapshot=natural.snapshot();
const finished=snapshot.riders.find(r=>r.status==='FINISHED'),racing=snapshot.riders.find(r=>r.status==='RACING');
const valid=store(snapshot);
test('production loader uses normal save path',()=>assert.equal(E.getTesting(),false));
test('normal first-finish raw and compact saves retain exact state',()=>{
 for(const active of [snapshot,E.SaveCodec.compactSnapshot(snapshot)]){
  const decoded=E.SaveCodec.decode(store(active));assert.equal(decoded.issues.length,0);
  assert.deepEqual(state(E.Race.restore(decoded.store.active).snapshot()),state(snapshot));
 }
 return {t:snapshot.t,finishedId:finished.id,simTime:finished.finishedTime,worldTime:finished.finishRaceTime};
});
const invalid=[
 ['FINISHED with missing physical time',s=>s.riders[finished.id].finishedTime=null],
 ['FINISHED with zero physical time',s=>s.riders[finished.id].finishedTime=0],
 ['FINISHED with future physical time',s=>s.riders[finished.id].finishedTime=s.t+1],
 ['FINISHED with missing world time',s=>s.riders[finished.id].finishRaceTime=null],
 ['FINISHED with zero world time',s=>s.riders[finished.id].finishRaceTime=0],
 ['FINISHED with future world time',s=>s.riders[finished.id].finishRaceTime=s.timing.elapsed+1],
 ['FINISHED before the finish line',s=>{const r=s.riders[finished.id];r.x-=1;r.prevX=Math.min(r.prevX,r.x);}],
 ['RACING with physical finish time',s=>s.riders[racing.id].finishedTime=1],
 ['RACING with world finish time',s=>s.riders[racing.id].finishRaceTime=1]
];
for(const [name,mutate]of invalid)test('strict rejection / recovery: '+name,()=>{
 const input=plain(valid);mutate(input.active);const bytes=JSON.stringify(input);
 assert.throws(()=>E.SaveCodec.decode(input),'strict import must reject impossible finish state');
 const recovered=E.SaveCodec.decode(input,{recover:true});assert.equal(recovered.store.active,null);assert.equal(recovered.store.tour.results.length,0);assert.equal(recovered.issues.length,1);
 assert.equal(JSON.stringify(input),bytes,'validation never mutates the supplied save');
});
test('V22 and V23 actual first-finish snapshots remain compatible',()=>{
 for(const version of [22,23]){
  const old=loadEngine(path.join(__dirname,`../../archive/v${version}/Grand-Tour-V${version}.html`),false).engine;
  const r=advance(new old.Race(0,0,'tour',null,314159),r=>r.finishedCount>0),s=r.snapshot();
  assert.deepEqual(state(E.Race.restore(s).snapshot()),state(s));assert.equal(E.SaveCodec.decode(store(s)).issues.length,0);
 }
});
test('V4 / V7 / V8 legacy-sim active schema migration retains legal finish times',()=>{
 const r=advance(new E.Race(0,0,'tour',null,314159,{timeModel:'legacy-sim',courseVersion:8,terrainVersion:16}),r=>r.finishedCount>0);
 for(const version of [4,7,8]){
  const s=plain(r.snapshot());s.engineVersion=version;
  if(version<8){delete s.courseVersion;delete s.timeModel;delete s.conditions;delete s.timing;delete s.gapCredits;delete s.breakGroupUid;
   for(const x of s.riders)for(const key of ['finishRaceTime','wind','rolling','climate','speedCap'])delete x[key];
   for(const c of s.checkpoints){delete c.timeOffset;for(const h of c.order)delete h.simTime;}
   for(const e of s.events)delete e.raceTime;
  }
  const decoded=E.SaveCodec.decode(store(s,version));assert.equal(decoded.issues.length,0);assert.equal(decoded.store.active.timeModel,'legacy-sim');
  for(const x of decoded.store.active.riders)assert.equal(x.finishRaceTime,x.finishedTime);
  const corrupt=store(s,version);corrupt.active.riders.find(x=>x.status==='FINISHED').finishedTime=null;
  assert.throws(()=>E.SaveCodec.decode(corrupt),'legacy migration cannot invent missing finish times');
 }
});
const complete=advance(E.Race.restore(snapshot),r=>r.complete),completeSnapshot=complete.snapshot();
test('active completed snapshot rejects reversed world finish order',()=>{
 const s=plain(completeSnapshot),order=s.riders.filter(r=>r.status==='FINISHED').sort((a,b)=>a.finishedTime-b.finishedTime||a.id-b.id);
 order[1].finishRaceTime=order[0].finishRaceTime-1;
 assert.throws(()=>E.SaveCodec.decode(store(s)),'active finish times must obey the recorded-result ordering contract');
});
test('natural full stage, active restore and recorded save round trip',()=>{
 assert.equal(E.Race.restore(completeSnapshot).complete,true);
 const record=complete.result(),saved=store(null);saved.tour.timeModel='race-world-v1';saved.tour.results=[record];
 const encoded=E.SaveCodec.encode(saved),decoded=E.SaveCodec.decode(encoded);
 assert.equal(decoded.issues.length,0);assert.deepEqual(plain(E.SaveCodec.encode(decoded.store)),plain(encoded));
 return {simSeconds:complete.t,finished:record.statuses.filter(s=>s==='FINISHED').length,OTL:record.statuses.filter(s=>s==='OTL').length};
});
// The finalizer, codec, ownership check and localStorage write are all real.
// Only rendering a ceremony is unrelated to this persistence boundary.
E.Ceremony.prepare=()=>{};
function arrange(r){const raw=JSON.stringify(valid);E.localStorage.setItem(E.CONFIG.saveKey,raw);E.loadStore();E.App.race=r;E.App.finishFlow={settleCount:0};E.App.result=null;return raw;}
test('settlement validates result before changing progress or recording race',()=>{
 const r=E.Race.restore(completeSnapshot),raw=arrange(r);r.riders.find(x=>x.status==='FINISHED').finishedTime=null;
 const before=JSON.stringify(E.SaveCodec.encode(E.Store()));
 assert.throws(()=>E.finalizeRace(),/物理计时损坏/);
 assert.equal(r.recorded,false);assert.equal(E.App.finishFlow.settleCount,0);assert.equal(E.App.result,null);
 assert.equal(JSON.stringify(E.SaveCodec.encode(E.Store())),before);assert.equal(E.localStorage.getItem(E.CONFIG.saveKey),raw);
});
test('normal production settlement persists strict-decodable result once',()=>{
 const r=E.Race.restore(completeSnapshot);arrange(r);E.finalizeRace();
 assert.equal(r.recorded,true);assert.equal(E.App.finishFlow.settleCount,1);
 const raw=E.localStorage.getItem(E.CONFIG.saveKey),decoded=E.SaveCodec.decode(JSON.parse(raw));
 assert.equal(decoded.issues.length,0);assert.equal(decoded.store.tour.results.length,1);assert.equal(decoded.store.active,null);assert.equal(decoded.store.pendingCeremony.stage,0);
 E.finalizeRace();assert.equal(E.localStorage.getItem(E.CONFIG.saveKey),raw);
 E.loadStore();assert.equal(E.Store().tour.results.length,1);
});
const report={source,sourceSHA256:crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex'),checks,passed:checks.filter(c=>c.pass).length,failed:checks.filter(c=>!c.pass).length};
if(out)fs.writeFileSync(out,JSON.stringify(report,null,2));console.log(`${report.passed}/${checks.length} PASS`);process.exitCode=report.failed?1:0;
