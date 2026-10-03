'use strict';
// Diagnose natural flat-stage outcomes without assigning positions or AI actions.
const fs=require('node:fs'),{loadEngine}=require('../v23/engine-loader.cjs');
const [source,out]=process.argv.slice(2),E=loadEngine(source,true).engine,report={source,cases:[]};
for(const seed of [12345,271828,2058765])for(const stage of [4,6,20]){
 const r=new E.Race(stage,0,'tour',null,seed),samples=[];let next=0;
 const rider=x=>({id:x.id,name:x.d.name,role:x.d.role,gap:Math.round((r.order.find(E.isRacing)?.x-x.x)||0),energy:+x.energy.toFixed(1),w:+(x.w/x.d.wCapacity).toFixed(3),speed:+x.v.toFixed(2),power:Math.round(x.power),ai:x.aiState,group:x.groupId,inBreak:x.inBreak,spent:x.spent,sprint:x.sprintStarted,front:x.frontId});
 while(!r.complete&&r.t<4000){
  if(r.stepCount%20===0&&E.isRacing(r.player)){if(r.player.energy<65&&r.player.feeds>0&&r.t>=r.player.feedReady)r.feed();if(!r.hold)r.automaticWheel();}
  r.tick();const lead=r.order.find(E.isRacing),left=lead?r.stage.reference.length-r.routeX(lead):0;
  if(next<[20000,10000,5000,2000,1000,300].length&&left<=[20000,10000,5000,2000,1000,300][next]){
   samples.push({at:[20000,10000,5000,2000,1000,300][next++],t:r.t,front:r.order.filter(E.isRacing).slice(0,7).map(rider),sprinters:r.riders.filter(x=>x.d.role==='Sprinter').map(rider),trains:r.teams.filter(t=>t.paceline).map(t=>({team:t.teamId,objective:t.objective,stageObjective:t.teamObjective,nominated:t.sprinterId,fullTrain:r.flags.fullLeadouts?.includes(t.teamId),plan:JSON.parse(JSON.stringify(t.paceline)),resources:r.teamResources(t)}))});
  }
 }
 const result=r.result(),winner=r.riders[result.places.indexOf(1)],row={stage:stage+1,seed,winner:rider(winner),sprinterResults:r.riders.filter(x=>x.d.role==='Sprinter').map(x=>({...rider(x),place:result.places[x.id],secondsBehind:result.times[x.id]-result.times[winner.id]})),samples};
 report.cases.push(row);fs.writeFileSync(out,JSON.stringify(report,null,2));console.log(JSON.stringify({stage:row.stage,seed,winner:row.winner,highestSprinter:row.sprinterResults.sort((a,b)=>a.place-b.place)[0]}));
}
