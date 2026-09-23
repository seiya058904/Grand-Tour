'use strict';
const fs=require('node:fs'),{loadEngine}=require('./engine-loader.cjs');
const file=process.argv[2],out=process.argv[3],seed=Number(process.argv[4]||314159),{engine:E}=loadEngine(file,true);
function pilot(r){const p=r.player;if(!E.isRacing(p))return;if(p.energy<70&&p.feeds>0&&r.t>=p.feedReady)r.feed();if(p.attackUntil>r.t)return;const left=r.stage.length-p.x,ref=r.stage.reference.length-r.routeX(),fraction=1-ref/r.stage.reference.length,eta=left/Math.max(3,p.v);
 if(r.stage.type==='ITT'){if(eta<10&&p.w>p.d.wCapacity*.18&&r.canAttack())r.attack();else r.setEffort(p.grade<-.04?0:1);return;}
 if(!r.hold)r.automaticWheel();const threat=r.threatFor(r.teams[0]);
 const sprint=ref<1000&&eta<10&&(r.stage.isTT||r.stage.type!=='Flat');
 const response=threat&&threat.stageGain>4&&p.w>p.d.wCapacity*.5&&p.energy>35&&fraction>.60;
 const initiative=r.stage.type==='Mountain'&&fraction>.76&&p.grade>.045&&p.w>p.d.wCapacity*.82&&p.energy>55&&p.attacks===0;
 if((sprint||response||initiative)&&r.canAttack())r.attack();
}
const mean=a=>a.length?a.reduce((n,x)=>n+x,0)/a.length:0;
const report={source:file,policy:'standard-GC-v2: public controls once/sec; feed <70%; TT slope pacing; road/TTT follow; last-climb initiative; late GC response; GC does not contest ordinary flat sprint.',seed,stages:[],roleWins:{},errors:[]};let prior=null;const allRecords=[];
for(let stage=0;stage<21;stage++){
 const start=performance.now(),r=new E.Race(stage,0,'tour',prior,(seed+stage*8191)>>>0);let samples=0,draft=0,groups=0,mountain=null;
 while(!r.complete&&r.t<4000){if(r.stepCount%20===0)pilot(r);r.tick();if(r.stepCount%200===0){samples++;draft+=r.player.draft;groups+=r.groups.length;for(const x of r.riders)if(!Number.isFinite(x.x)||!Number.isFinite(x.w)||x.energy<0||x.energy>100||x.w<-.001||x.w>x.d.wCapacity+.001)throw new Error('Bounds');
  const c=r.lastClimb,first=E.isRacing(r.order[0])?r.order[0]:null;if(c&&['HC','1'].includes(c.category)&&first&&first.x>c.foot+(c.x-c.foot)*.85&&first.x<c.x){const front=r.riders.filter(x=>E.isRacing(x)&&first.x-x.x<25);mountain={count:front.length,lowClimbSprinters:front.filter(x=>x.d.role==='Sprinter'&&x.d.climb<78).map(x=>x.id),front:front.map(x=>({id:x.id,role:x.d.role,climb:x.d.climb}))};}
 }}
 if(!r.complete)throw new Error('Stage timeout '+(stage+1));const rec=r.result();E.normalizeRecord(rec,stage,prior);prior=rec;allRecords.push(rec);
 const order=rec.places.map((place,id)=>({id,place})).filter(x=>x.place).sort((a,b)=>a.place-b.place),roles=[...new Set(E.RIDER_DATA.map(d=>d.role))];
 const data={stage:stage+1,type:r.stage.type,seed:r.seed,simSeconds:r.t,worldSeconds:r.timing?.elapsed??r.t,wallMs:Math.round(performance.now()-start),conditions:r.conditions,starting:r.startingCount,finishers:rec.statuses.filter(x=>x==='FINISHED').length,OTL:rec.statuses.filter(x=>x==='OTL').length,DNF:rec.statuses.filter(x=>x==='DNF').length,DNS:rec.statuses.filter(x=>x==='DNS').length,player:{status:rec.statuses[0],place:rec.places[0],time:rec.times[0],energy:rec.energies[0],fatigue:rec.fatigues[0],meanDraft:draft/Math.max(1,samples)},stageTop10:order.slice(0,10).map(x=>({id:x.id,name:E.RIDER_DATA[x.id].name,role:E.RIDER_DATA[x.id].role,time:rec.times[x.id]})),podium:r.stage.type==='TTT'?rec.teamStage.slice(0,3).map(x=>({teamId:x.teamId,time:x.time})):order.slice(0,3).map(x=>({id:x.id,time:rec.times[x.id]})),gcTop10:E.Classification.gcOrder(rec.season).slice(0,10).map(id=>({id,name:E.RIDER_DATA[id].name,role:E.RIDER_DATA[id].role,time:rec.season.gcTimes[id]})),fatigue:roles.map(role=>({role,morning:mean(r.riders.filter(x=>x.d.role===role&&x.status!=='DNS').map(x=>x.startFatigue)),evening:mean(r.riders.filter(x=>x.d.role===role&&x.status!=='DNS').map(x=>rec.fatigues[x.id]))})),attacks:r.audit.attacks.length,chases:r.audit.chases.length,rotations:r.audit.rotations.length,breakAttempts:r.audit.attacks.filter(x=>x.kind==='break').length,breakWinner:order[0]?r.riders[order[0].id].inBreak:false,meanGroups:groups/Math.max(1,samples),draftSeconds:r.audit.draftSeconds,mountain};
 if(order[0]&&r.stage.type!=='TTT'){const role=E.RIDER_DATA[order[0].id].role;report.roleWins[role]=(report.roleWins[role]||0)+1;}
 report.stages.push(data);fs.writeFileSync(out,JSON.stringify(report,null,2));console.log(JSON.stringify({seed,stage:stage+1,ms:data.wallMs,finished:data.finishers,place:data.player.place,time:data.stageTop10[0]?.time,fatigue:data.player.fatigue}));
}
fs.writeFileSync(out.replace('.json','-record.json'),JSON.stringify(prior));console.log('DONE');

fs.writeFileSync(out.replace('.json','-tour.json'),JSON.stringify(E.SaveCodec.encode({version:8,tour:{id:'regression-'+seed,playerId:0,seedBase:seed,timeModel:'race-world-v1',results:allRecords},active:null,settings:{}})));
