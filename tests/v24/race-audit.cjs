'use strict';
// Natural races only. The pilot uses public inputs; no position, power, clock,
// weather, winner, or AI state is injected to produce a desired picture/result.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {loadEngine}=require('../v23/engine-loader.cjs');
const [file,out,baselineFile,tourFile]=process.argv.slice(2),E=loadEngine(file,true).engine;
const sha=v=>crypto.createHash('sha256').update(v).digest('hex');
const report={source:path.basename(file),sha256:sha(fs.readFileSync(file)),policy:'public GC controls; feed below 65%; preserve on flat; respond to late GC moves; ITT threshold/downhill recovery',cases:[],snapshots:[],pass:false};
const baseline=baselineFile&&baselineFile!=='-'?JSON.parse(fs.readFileSync(baselineFile)):null;
const prior=tourFile?E.SaveCodec.decode(JSON.parse(fs.readFileSync(tourFile))).store.tour.results[17]:null;
fs.mkdirSync(path.dirname(out),{recursive:true});
const scenes=path.join(path.dirname(out),'scenes');fs.mkdirSync(scenes,{recursive:true});
const physical=r=>JSON.stringify({riders:r.riders.map(x=>[x.id,x.x,x.v,x.power,x.energy,x.w,x.drawLane,x.frontId,x.draft,x.status]),rng:r.rng.state,t:r.t});
function pilot(r){const p=r.player;if(!E.isRacing(p))return;if(p.energy<65&&p.feeds>0&&r.t>=p.feedReady)r.feed();if(p.attackUntil>r.t)return;
 if(r.stage.type==='ITT'){r.setEffort(p.grade<-.04?0:1);return;}
 if(!r.hold)r.automaticWheel();const threat=r.threatFor(r.teams[0]);
 if(r.stage.type==='Mountain'&&r.player.x/r.stage.length>.60&&threat?.stageGain>4&&p.energy>35&&p.w>p.d.wCapacity*.5&&r.canAttack())r.attack();
}
function scene(r,key,why){if(report.snapshots.some(s=>s.name===key))return;const snap=r.snapshot();snap.mode='tour';const name=key+'-snapshot.json';fs.writeFileSync(path.join(scenes,name),JSON.stringify(snap));report.snapshots.push({name:key,file:'scenes/'+name,stage:r.stageIndex+1,seed:r.seed,t:r.t,why,conditions:r.conditions});}
for(const seed of [12345,271828,2058765])for(const stage of [0,2,4,6,15,18,20]){
 const r=new E.Race(stage,0,'tour',stage===18?prior:null,seed),objectives=new Set(),states=new Set(),firstCrossings=[],start=performance.now();let samples=0,draft=0,restoreChecks=0,peakGroups=0,lowEnergyHelpers=0,maxLaneDelta=0,lastLanes=r.riders.map(x=>x.drawLane);
 while(!r.complete&&r.t<4000){
  if(r.stepCount%20===0)pilot(r);const racing=r.riders.filter(E.isRacing);r.tick();
  for(const x of racing)if(x.status==='FINISHED'&&firstCrossings.length<10)firstCrossings.push({id:x.id,role:x.d.role,power:x.power,cp:E.Physics.sustainable(x),energy:x.energy,sprint:x.sprintStarted,ai:x.aiState});
  if(r.stepCount%100!==0)continue;
  samples++;draft+=r.player.draft;peakGroups=Math.max(peakGroups,r.groups.length);
  for(const t of r.teams)objectives.add(t.objective);
  for(const x of r.riders){assert([x.x,x.v,x.w,x.power,x.energy,x.drawLane].every(Number.isFinite),'finite state');assert(x.w>=-.001&&x.w<=x.d.wCapacity+.001&&x.energy>=0&&x.energy<=100.001,'physiology bounds');states.add(x.aiState);maxLaneDelta=Math.max(maxLaneDelta,Math.abs(x.drawLane-lastLanes[x.id]));lastLanes[x.id]=x.drawLane;if(x.spent&&x.energy<30)lowEnergyHelpers++;}
  assert(E.fieldAccounting(r).closed,'184-rider accounting');
  if(r.stepCount%1200===0){const a=E.Race.restore(r.snapshot()),b=E.Race.restore(E.SaveCodec.compactSnapshot(r.snapshot()));assert.equal(physical(a),physical(r));for(let k=0;k<50;k++){a.tick();b.tick();}assert.equal(physical(a),physical(b),'compact resume');restoreChecks++;}
  if(seed===2058765){
   if(stage===4&&r.t>=40)scene(r,'peloton','unmodified road peloton after 40 simulation seconds');
   if(stage===4&&r.groups.some(g=>g.kind==='BREAKAWAY'&&g.count>=2))scene(r,'breakaway','natural multi-rider breakaway');
   if(stage===4&&r.teams.some(t=>t.objective==='leadout'))scene(r,'leadout','a team actually entered its leadout objective');
   if(stage===4&&r.riders.some(x=>E.isRacing(x)&&x.aiState==='sprint'))scene(r,'sprint','an actual rider entered the sprint state');
   if(stage===2&&r.player.grade<-.055&&r.player.v>12)scene(r,'descent','real mountain descent at over 43.2 km/h');
   if(stage===18&&r.player.grade>.07&&r.player.power>E.Physics.sustainable(r.player)*.8)scene(r,'climb','real final Alpine stage terrain and load');
   if(stage===18&&r.audit.attacks.some(e=>e.kind==='gcAttack'))scene(r,'gc-battle','natural GC attack with stage-18 Tour history');
   if(stage===0&&r.audit.rotations.length>2)scene(r,'ttt','actual TTT handovers');
   if(stage===15&&r.t>30)scene(r,'itt','individual time trial on actual lakeside stage');
  }
 }
 assert(r.complete,'race completed');const result=r.result(),account=E.fieldAccounting(r);assert.equal(account.total,184);assert.equal(account.racing,0);assert.equal(result.audit.invariantFailures.length,0);
 const resultHash=sha(JSON.stringify(result)),old=baseline?.cases.find(c=>c.seed===seed&&c.stage===stage+1);
 if(baseline){assert(old,'baseline case exists');assert.equal(resultHash,old.resultHash,'V23/V24 whole result, AI audit, timing and standings parity');}
 const winner=result.places.indexOf(1),row={seed,stage:stage+1,type:r.stage.type,conditions:r.conditions,seconds:r.t,wallMs:Math.round(performance.now()-start),starting:r.startingCount,account,player:{status:r.player.status,place:result.places[0],energy:r.player.energy,meanDraft:draft/samples},winner:{id:winner,name:E.RIDER_DATA[winner]?.name,role:E.RIDER_DATA[winner]?.role},objectives:[...objectives].sort(),states:[...states].sort(),attacks:r.audit.attacks.length,chases:r.audit.chases.length,rotations:r.audit.rotations.length,breakAttempts:r.audit.attacks.filter(x=>x.kind==='break').length,gcAttacks:r.audit.attacks.filter(x=>x.kind==='gcAttack').length,peakGroups,lowEnergyHelperSamples:lowEnergyHelpers,maxLaneDeltaPer5s:maxLaneDelta,firstCrossings,restoreChecks,resultHash,parity:baseline?true:null};
 report.cases.push(row);fs.writeFileSync(out,JSON.stringify(report,null,2));console.log(JSON.stringify({seed,stage:stage+1,winner:row.winner,rotations:row.rotations,gc:row.gcAttacks,parity:row.parity}));
}
report.pass=true;fs.writeFileSync(out,JSON.stringify(report,null,2));console.log('PASS natural multi-seed race audit');
