'use strict';
// Read the real live-standings function through an extra test-only export.
// No alternate standings implementation and no production-engine mutation.
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {loadEngine}=require('../v23/engine-loader.cjs');
const [source,out]=process.argv.slice(2);if(!source)throw new Error('Usage: node tests/v25/simulation-live-standings.cjs source.html [outside-report.json]');
const html=fs.readFileSync(source,'utf8'),marker='window.__TOUR_TEST__={';assert(html.includes(marker),'production test export anchor');
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'gt-live-standings-'));
let E,liveSeason,rules;
try{const exposed=path.join(tmp,'game.html');fs.writeFileSync(exposed,html.replace(marker,marker+'liveSeason,'));const loaded=loadEngine(exposed,true);E=loaded.engine;liveSeason=loaded.sandbox.window.__TOUR_TEST__.liveSeason;rules=loaded.sandbox.window.__TOUR_TEST__.RACE_RULES;}finally{fs.rmSync(tmp,{recursive:true,force:true});}
const cases=[];
function runCase(type,priorWinsA,priorWinsB,hasFinish=true){
 const stage=E.STAGE_DATA.findIndex(s=>s.type===type),r=new E.Race(stage,0,'tour',null,4242),a=r.riders[0],b=r.riders.find(x=>x.d.role==='Sprinter'&&x.id!==a.id);
 // A focused read-model fixture: the day's winner B has crossed, A is still
 // approaching. Both now have the same points; A leads GC from previous days.
 const n=r.riders.length,zero=()=>Array(n).fill(0),season={active:Array(n).fill(false),gcTimes:zero(),ttFractions:zero(),placeSum:zero(),lastPlaces:zero(),points:zero(),kom:zero(),stageWins:zero(),sprintWins:zero(),komWins:r.riders.map(()=>[0,0,0,0,0]),starters:null};
 const points=rules.finish[Math.min(4,r.stage.coefficient)][0];
 season.active[a.id]=season.active[b.id]=true;season.gcTimes[a.id]=10000;season.gcTimes[b.id]=10100;season.points[a.id]=points;season.stageWins[a.id]=priorWinsA;season.stageWins[b.id]=priorWinsB;
 season.leaders=E.Classification.leaders(season);r.prior={season,timeModel:'race-world-v1'};
 for(const x of r.riders){x.status='DNS';x.finishedTime=null;x.finishRaceTime=null;x.points=0;x.kom=0;}
 Object.assign(b,{status:hasFinish?'FINISHED':'RACING',x:r.stage.length-(hasFinish?0:5),prevX:r.stage.length-6,finishedTime:hasFinish?200:null,finishRaceTime:hasFinish?15000:null,rank:1});Object.assign(a,{status:'RACING',x:r.stage.length-20,prevX:r.stage.length-21,v:10,rank:2});
 r.order=[b,a,...r.riders.filter(x=>x.id!==a.id&&x.id!==b.id)];r.t=202;r.stepCount=4040;r.startingCount=2;r.removedCount=n-2;r.timing.elapsed=15002;r.timing.finishSim=hasFinish?200:null;r.timing.finishOffset=hasFinish?14800:null;r.timing.lastFinishSim=hasFinish?200:null;r.timing.lastFinishWorld=hasFinish?15000:null;r.finishedCount=hasFinish?1:0;
 const before=JSON.stringify(r.prior),displayed=liveSeason(r),again=liveSeason(r),expectedStageWins=priorWinsB+(!hasFinish||type==='TTT'?0:1),expectedGreen=!hasFinish||type==='TTT'?a.id:priorWinsA>expectedStageWins?a.id:b.id;
 const row={type,hasFinish,priorWinsA,priorWinsB,points,dayWinner:hasFinish?b.id:null,displayedWins:displayed.stageWins[b.id],expectedWins:expectedStageWins,displayedGreen:displayed.leaders.green,expectedGreen,priorUnchanged:JSON.stringify(r.prior)===before,idempotent:JSON.stringify(displayed)===JSON.stringify(again)};row.pass=row.displayedWins===expectedStageWins&&row.displayedGreen===expectedGreen&&row.priorUnchanged&&row.idempotent;cases.push(row);return row;
}
runCase('Flat',0,0);runCase('Mountain',0,0);runCase('ITT',0,0);runCase('Flat',2,0);runCase('TTT',0,0);runCase('Flat',0,0,false);
const report={source:path.basename(source),sha256:crypto.createHash('sha256').update(html).digest('hex'),cases,pass:cases.every(c=>c.pass)};
if(out){fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(report,null,2));}console.log(JSON.stringify(report,null,2));if(!report.pass)process.exitCode=1;
