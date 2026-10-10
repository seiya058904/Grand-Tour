'use strict';
// Validate persistence against natural production races. Corrupt one field at
// the boundary; never alter the simulator or manufacture a winning result.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {loadEngine}=require('../v23/engine-loader.cjs');
const source=path.resolve(process.argv[2]||path.join(__dirname,'../../Grand-Tour-V25.html')),out=process.argv[3],fixtureDir=process.argv[4];
const sourceSHA256=crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex');
const E=loadEngine(source,false).engine,checks=[],plain=x=>JSON.parse(JSON.stringify(x));
function test(name,fn){try{checks.push({name,pass:true,detail:fn()});console.log('PASS',name);}catch(e){checks.push({name,pass:false,error:e.stack});console.log('FAIL',name,e.message.slice(0,200));}}
function advance(r,condition){while(!condition(r)&&r.t<4000)r.tick();assert(condition(r),'natural race reaches requested boundary');return r;}
function store(active,results=[],version=9){return {version,progressRevision:3,pendingCeremony:null,tour:{id:'v25-storage-validation',playerId:0,seedBase:314159,seedOrigin:'created',timeModel:active?.timeModel||results[0]?.timeModel||'race-world-v1',results},active,settings:{quality:'full',labelDensity:'standard',musicVolume:.31}};}
function legacy(input,version){
 const s=plain(input);s.engineVersion=version;
 if(s.cutoff)delete s.cutoff.timeModel;
 if(version<8){delete s.courseVersion;delete s.timeModel;delete s.conditions;delete s.timing;delete s.gapCredits;delete s.breakGroupUid;
  for(const r of s.riders)for(const k of ['finishRaceTime','wind','rolling','climate','speedCap'])delete r[k];
  for(const c of s.checkpoints){delete c.timeOffset;for(const h of c.order)delete h.simTime;}
  for(const e of s.events)delete e.raceTime;
 }
 return s;
}
let firstStageRecord,firstStageSnapshot;
for(const stage of [0,1,15])for(const timeModel of ['race-world-v1','legacy-sim']){
 const r=new E.Race(stage,0,'tour',null,314159,{timeModel,...(timeModel==='legacy-sim'?{courseVersion:8,terrainVersion:16}:{})});
 const name=`${r.stage.type} stage ${stage+1} ${timeModel}`;
 const initial=r.snapshot();test(name+' pre-finish absent cutoff remains valid',()=>assert.equal(E.Race.restore(initial).cutoff,null));
 advance(r,x=>x.finishedCount>0);const first=r.snapshot();
 test(name+' natural first finish raw/compact retains cutoff and timing',()=>{
  for(const s of [first,E.SaveCodec.compactSnapshot(first)]){const restored=E.Race.restore(s).snapshot();assert.deepEqual(plain(restored.cutoff),plain(first.cutoff));assert.deepEqual(plain(restored.timing),plain(first.timing));}
  return {t:first.t,cutoff:first.cutoff,finished:first.finishedCount};
 });
 test(name+' damaged active cutoff rejects before simulation can retire riders',()=>{
  const mutations=[
   ['deadline',s=>s.cutoff.deadline=1],
   ['shape',s=>s.cutoff={}],
   ['winner',s=>s.cutoff.winner=s.riders.find(x=>x.status==='RACING').id],
   ['time',s=>{s.cutoff.time+=1;s.cutoff.deadline=s.cutoff.time*(1+s.cutoff.percent);}],
   ['clock',s=>s.cutoff.timeModel=timeModel==='legacy-sim'?'race-world-v1':'legacy-sim']
  ];
  for(const [field,mutate]of mutations){const s=plain(first);mutate(s);const raw=JSON.stringify(s);assert.throws(()=>E.Race.restore(s),/关门线/,field);assert.equal(JSON.stringify(s),raw,'input state remains untouched');
   if(stage===0){assert.throws(()=>E.SaveCodec.decode(store(s)),/关门线/);const recovered=E.SaveCodec.decode(store(s),{recover:true});assert.equal(recovered.store.active,null);assert.equal(recovered.issues.length,1);}
  }
  return {rejected:mutations.map(x=>x[0])};
 });
 const completed=advance(E.Race.restore(first),x=>x.complete),record=completed.result();
 test(name+' natural completed result, optional legacy cutoff metadata',()=>{
  const normalized=E.normalizeRecord(record,stage,null);assert.deepEqual(plain(normalized.cutoff),plain(record.cutoff));
  for(const missing of ['timeModel','cutoff']){const value=plain(record);if(missing==='cutoff')delete value.cutoff;else delete value.cutoff.timeModel;assert.equal(E.normalizeRecord(value,stage,null).statuses.filter(x=>x==='FINISHED').length,record.statuses.filter(x=>x==='FINISHED').length);}
  return {finishers:record.statuses.filter(x=>x==='FINISHED').length,OTL:record.statuses.filter(x=>x==='OTL').length};
 });
 test(name+' historical cutoff must agree with classified finishers',()=>{
  const wrongWinner=plain(record),winner=record.cutoff.winner;
  wrongWinner.cutoff.winner=record.statuses.findIndex((x,id)=>x==='FINISHED'&&id!==winner&&record.simTimes[id]>record.simTimes[winner]+1e-7);
  assert(wrongWinner.cutoff.winner>=0);assert.throws(()=>E.normalizeRecord(wrongWinner,stage,null),/关门线/);
  const late=plain(record);late.cutoff.percent=0;late.cutoff.deadline=late.cutoff.time;assert.throws(()=>E.normalizeRecord(late,stage,null),/关门线/);
  const badTime=plain(record);badTime.cutoff.time=1;badTime.cutoff.deadline=1*(1+badTime.cutoff.percent);assert.throws(()=>E.normalizeRecord(badTime,stage,null),/关门线/);
  return {rejected:['winner','late classified finisher','time']};
 });
 if(stage===0&&timeModel==='race-world-v1'){firstStageRecord=plain(record);firstStageSnapshot=plain(first);}
 advance(r,x=>x.finishedCount>=2);const beforeOTL=r.riders.filter(x=>x.status==='FINISHED').sort((a,b)=>a.finishedTime-b.finishedTime),firstTime=beforeOTL[0].finishRaceTime,lastTime=beforeOTL.at(-1).finishRaceTime;
 r.cutoff.deadline=(firstTime+lastTime)/2;r.cutoff.percent=r.cutoff.deadline/r.cutoff.time-1;r.updateAttrition(0);r.tick();r.relations();const late=r.snapshot();
 test(name+' late OTL crossing keeps its legal timing and checkpoint ledger',()=>{
  assert(late.riders.some(x=>x.status==='OTL'&&x.x===r.stage.length));
  for(const s of [late,E.SaveCodec.compactSnapshot(late)]){const restored=E.Race.restore(s).snapshot();assert.deepEqual(plain(restored.cutoff),plain(late.cutoff));assert.deepEqual(plain(restored.timing),plain(late.timing));assert.deepEqual(plain(restored.checkpoints),plain(late.checkpoints));}
  if(timeModel==='legacy-sim')for(const version of [4,7,8])for(const s of [first,late]){const old=legacy(s,version),restored=E.Race.restore(old);assert.equal(restored.timeModel,'legacy-sim');assert.equal(restored.finishedCount,s.finishedCount);assert.deepEqual(plain(restored.cutoff),plain(old.cutoff));}
  return {finishers:late.finishedCount,OTL:late.riders.filter(x=>x.status==='OTL').length,legacyVersions:timeModel==='legacy-sim'?[4,7,8]:[]};
 });
}
const next=new E.Race(1,0,'tour',firstStageRecord,E.seedForStage(314159,1)).snapshot(),prefix=store(next,[firstStageRecord]);
for(const [name,mutate]of [
 ['invalid active seed',s=>s.active.seed=-1],
 ['unsupported active version',s=>s.active.engineVersion=999],
 ['invalid active course version',s=>s.active.courseVersion=999],
 ['missing compact audit summary',s=>{s.active=E.SaveCodec.compactSnapshot(s.active);delete s.active.auditSummary;}]
])test('recovery isolates '+name+' while strict import stays atomic',()=>{
 const s=plain(prefix);mutate(s);const raw=JSON.stringify(s);assert.throws(()=>E.SaveCodec.decode(s));
 const decoded=E.SaveCodec.decode(s,{recover:true});assert.equal(decoded.store.active,null);assert.equal(decoded.store.tour.results.length,1);assert.equal(decoded.issues.length,1);
 assert.deepEqual(plain(E.SaveCodec.encode(decoded.store).tour.results),plain(E.SaveCodec.encode(store(null,[firstStageRecord])).tour.results));assert.deepEqual(plain(decoded.store.settings),plain(prefix.settings));assert.equal(JSON.stringify(s),raw);
 return {retainedStages:1,active:null,issues:decoded.issues,settingsPreserved:true,inputUnchanged:true};
});
test('active recovery cannot conceal invalid top-level identity or seed',()=>{
 for(const mutate of [s=>s.version=999,s=>s.tour.seedBase=-1,s=>s.progressRevision=-1]){const s=plain(prefix);s.active.seed=-1;mutate(s);const raw=JSON.stringify(s);assert.throws(()=>E.SaveCodec.decode(s,{recover:true}));assert.equal(JSON.stringify(s),raw);}
});
test('active migration fallback still validates and truncates a damaged record suffix',()=>{
 const s=plain(prefix);s.active.seed=-1;s.tour.results.push({broken:true});const raw=JSON.stringify(s);const decoded=E.SaveCodec.decode(s,{recover:true});
 assert.equal(decoded.store.tour.results.length,1);assert.equal(decoded.store.active,null);assert.equal(decoded.issues.length,2);assert.equal(JSON.stringify(s),raw);
 assert.deepEqual(plain(E.SaveCodec.encode(decoded.store).tour.results),plain(E.SaveCodec.encode(store(null,[firstStageRecord])).tour.results));
});
test('loadStore backs up the original damaged bytes before exposing retained progress',()=>{
 const p=loadEngine(source,false),e=p.engine,s=plain(prefix);s.active.seed=-1;const raw=JSON.stringify(s);e.localStorage.setItem(e.CONFIG.saveKey,raw);e.loadStore();
 assert.equal(e.localStorage.getItem(e.CONFIG.saveKey),raw);assert.equal(e.localStorage.getItem(e.CONFIG.saveKey+'-recovery-backup'),raw);assert.equal(e.Store().tour.results.length,1);assert.equal(e.Store().active,null);assert.equal(e.App.blockStoreWrite,false);
 assert.equal(e.persist(),true);const decoded=e.SaveCodec.decode(JSON.parse(e.localStorage.getItem(e.CONFIG.saveKey)));assert.equal(decoded.issues.length,0);assert.equal(decoded.store.tour.results.length,1);
});
if(fixtureDir){fs.mkdirSync(fixtureDir,{recursive:true});fs.writeFileSync(path.join(fixtureDir,'natural-first-finish.json'),JSON.stringify(firstStageSnapshot));fs.writeFileSync(path.join(fixtureDir,'natural-completed-record.json'),JSON.stringify(firstStageRecord));fs.writeFileSync(path.join(fixtureDir,'natural-second-stage-save.json'),JSON.stringify(prefix));}
const sourceUnchanged=crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex')===sourceSHA256;
const report={source,sourceSHA256,sourceUnchanged,checks,passed:checks.filter(c=>c.pass).length,failed:checks.filter(c=>!c.pass).length};
if(out)fs.writeFileSync(out,JSON.stringify(report,null,2));console.log(report.passed+'/'+checks.length+' PASS');process.exitCode=report.failed||!sourceUnchanged?1:0;
