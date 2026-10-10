'use strict';
// Natural production-engine races. Public player controls only: no injected
// positions, watts, AI decisions, weather, or desired results.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {loadEngine}=require('../v23/engine-loader.cjs');
const [source,out,seedList='42,2026,65537,3735928559',stageList='flat']=process.argv.slice(2);
if(!source||!out)throw new Error('Usage: node tests/v25/simulation-survey.cjs source.html outside-report.json [comma-separated seeds] [flat|1,3,...]');
const E=loadEngine(source,true).engine,sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const stages=stageList==='flat'?E.STAGE_DATA.map((s,i)=>s.type==='Flat'?i:-1).filter(i=>i>=0):stageList.split(',').map(x=>Number(x)-1);
const report={source:path.basename(source),sha256:sha(fs.readFileSync(source)),policy:'Fresh isolated natural stages. Player GC uses auto wheel and feeds under 65%; no deliberate flat-stage attack. All AI, weather and physics are production code.',seeds:seedList.split(',').map(Number),stages:stages.map(x=>x+1),cases:[],pass:false};
fs.mkdirSync(path.dirname(out),{recursive:true});
const short=(r,x)=>({id:x.id,name:x.d.name,role:x.d.role,status:x.status,x:x.x,v:x.v,power:x.power,energy:x.energy,w:x.w/x.d.wCapacity,grade:x.grade,front:x.frontId,lane:x.drawLane,ai:x.aiState,inBreak:x.inBreak,spent:x.spent,grupetto:x.grupetto,sprint:x.sprintStarted,train:x.trainTarget,objective:r.teams[x.d.teamId].objective});
const thresholds=[25000,15000,8000,3000,1000,300];
function physical(r){return JSON.stringify({riders:r.riders.map(x=>[x.id,x.x,x.v,x.power,x.energy,x.w,x.drawLane,x.frontId,x.draft,x.status]),rng:r.rng.state,t:r.t});}
for(const seed of report.seeds)for(const stage of stages){
 const r=new E.Race(stage,0,'tour',null,seed),samples=[],firstCrossings=[],objectives=new Set(),start=performance.now();let next=0,checks=0,restoreChecks=0,peakGroups=0,peakSpeed=0;
 while(!r.complete&&r.t<4000){
  if(r.stepCount%20===0&&E.isRacing(r.player)){if(r.player.energy<65&&r.player.feeds>0&&r.t>=r.player.feedReady)r.feed();if(!r.hold)r.automaticWheel();}
  const previous=r.riders.filter(E.isRacing);r.tick();
  for(const x of previous)if(x.status==='FINISHED'&&firstCrossings.length<15)firstCrossings.push({...short(r,x),finishTime:x.finishRaceTime,cp:E.Physics.sustainable(x)});
  const first=r.order.find(E.isRacing),left=first?r.stage.reference.length-r.routeX(first):0;
  if(next<thresholds.length&&left<=thresholds[next]){
   samples.push({remaining:thresholds[next++],t:r.t,breakGap:r.breakGap,main:r.mainGroup?.uid,front:r.order.filter(E.isRacing).slice(0,10).map(x=>short(r,x)),sprinters:r.riders.filter(x=>x.d.role==='Sprinter').map(x=>({...short(r,x),eligible:r.finishEligibility(x),contest:r.stageWinContest(x),gap:first?first.x-x.x:null,group:x.groupUid})),teams:r.teams.filter(p=>p.teamObjective==='SPRINT').map(p=>({id:p.teamId,leader:p.leaderId,objective:p.objective,chain:p.chain.slice(),worker:p.workerId,resources:r.teamResources(p),chase:r.flags.chaseReadings?.[p.teamId]||null,paceline:p.paceline?JSON.parse(JSON.stringify(p.paceline)):null})),fullLeadouts:r.flags.fullLeadouts||[],leadoutLock:r.flags.leadoutLock||null});
  }
  if(r.stepCount%100)continue;checks++;peakGroups=Math.max(peakGroups,r.groups.length);
  for(const p of r.teams)objectives.add(p.objective);
  for(const x of r.riders){assert([x.x,x.v,x.w,x.power,x.energy,x.drawLane].every(Number.isFinite),'nonfinite rider state');assert(x.w>=-.001&&x.w<=x.d.wCapacity+.001&&x.energy>=0&&x.energy<=100.001,'physiology bounds');assert(x.x<=r.stage.length+1e-8,'finish distance bound');peakSpeed=Math.max(peakSpeed,x.v);}
  assert(E.fieldAccounting(r).closed,'184-rider accounting');
  if(seed===report.seeds[0]&&r.stepCount%2400===0){const a=E.Race.restore(r.snapshot()),b=E.Race.restore(E.SaveCodec.compactSnapshot(r.snapshot()));assert.equal(physical(a),physical(r),'restore matches live');for(let k=0;k<50;k++){a.tick();b.tick();}assert.equal(physical(a),physical(b),'raw/compact continued determinism');restoreChecks++;}
 }
 assert(r.complete,'stage timed out');const result=r.result(),normalized=E.normalizeRecord(result,stage,null),account=E.fieldAccounting(r);assert(normalized,'record normalization');assert.equal(account.racing,0);assert.equal(result.audit.invariantFailures.length,0);
 const order=result.places.map((p,id)=>({p,id})).filter(x=>x.p).sort((a,b)=>a.p-b.p),winner=r.riders[order[0].id];
 const row={stage:stage+1,seed,type:r.stage.type,seconds:r.t,wallMs:Math.round(performance.now()-start),conditions:r.conditions,winner:{...short(r,winner),seconds:result.times[winner.id]},top10:order.slice(0,10).map(({id,p})=>({...short(r,r.riders[id]),place:p,seconds:result.times[id]})),sprinterResults:r.riders.filter(x=>x.d.role==='Sprinter').map(x=>({...short(r,x),place:result.places[x.id],seconds:result.times[x.id]})),firstCrossings,samples,objectives:[...objectives].sort(),account,checks,restoreChecks,peakGroups,peakSpeed,resultHash:sha(JSON.stringify(result)),attacks:result.audit.attacks.filter(a=>['final-sprint','break','gcAttack','placement-sprint'].includes(a.kind)),chases:result.audit.chases.length};
 report.cases.push(row);fs.writeFileSync(out,JSON.stringify(report,null,2));console.log(JSON.stringify({stage:row.stage,seed,winner:row.winner.name,role:row.winner.role,bestSprinter:row.sprinterResults.filter(x=>x.place).sort((a,b)=>a.place-b.place)[0]?.place,wallMs:row.wallMs}));
}
report.summary={cases:report.cases.length,roleWins:report.cases.reduce((s,c)=>(s[c.winner.role]=(s[c.winner.role]||0)+1,s),{}),restoreChecks:report.cases.reduce((n,c)=>n+c.restoreChecks,0),invariantSamples:report.cases.reduce((n,c)=>n+c.checks,0)};report.pass=true;fs.writeFileSync(out,JSON.stringify(report,null,2));console.log(JSON.stringify({pass:true,...report.summary}));
