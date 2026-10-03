'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto'),{loadEngine}=require('./engine-loader.cjs');
const file=process.argv[2]||path.join(__dirname,'../../archive/v23/Grand-Tour-V23.html'),baseline=process.argv[3],out=process.argv[4]||path.join(require('node:os').tmpdir(),'grand-tour-v23-focused.json'),E=loadEngine(file).engine,O=baseline?loadEngine(baseline).engine:null;
const checks=[];function test(name,fn){try{checks.push({name,pass:true,detail:fn()});console.log('PASS',name)}catch(e){checks.push({name,pass:false,error:e.stack});console.log('FAIL',name,e.message)}fs.writeFileSync(out,JSON.stringify({source:file,sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),checks,passed:checks.filter(c=>c.pass).length,failed:checks.filter(c=>!c.pass).length},null,2));}
const tick=(r,n)=>{for(let i=0;i<n&&!r.complete;i++)r.tick()},plain=o=>JSON.parse(JSON.stringify(o));
const physical=r=>r.riders.map(x=>({id:x.id,x:x.x,v:x.v,energy:x.energy,w:x.w,draft:x.draft,lane:x.lane,drawLane:x.drawLane}));
function pair(){const r=new E.Race(4,0,'single',null,314159);r.riders.forEach(x=>x.status='DNS');for(const x of r.riders.slice(0,2))Object.assign(x,{status:'RACING',x:100,prevX:100,v:10,groupUid:100,grade:0});r.groups=[];r.t=10;return r;}
test('V23 retains storage key and schema V9',()=>{assert.equal(E.CONFIG.buildVersion,230);assert.equal(E.CONFIG.saveVersion,9);assert.equal(E.CONFIG.saveKey,'tour-cycling-2026-cinematic-v10')});
if(O){
 test('V22 road snapshot import preserves every physical field and RNG',()=>{const r=new O.Race(4,0,'tour',null,314159);tick(r,500);const snap=r.snapshot(),q=E.Race.restore(snap);assert.deepEqual(physical(q),physical(r));assert.equal(q.rng.state,r.rng.state);assert.equal(q.t,r.t);tick(q,100);assert(E.fieldAccounting(q).closed)});
 for(const stage of [0,15])test('TT unchanged production trajectory, stage '+(stage+1),()=>{const a=new O.Race(stage,0,'single',null,2026),b=new E.Race(stage,0,'single',null,2026);tick(a,1000);tick(b,1000);assert.deepEqual(physical(a),physical(b));assert.equal(a.rng.state,b.rng.state)});
}
test('Road snapshot resume is deterministic with optional seam/response state',()=>{const a=new E.Race(4,0,'tour',null,271828);tick(a,850);const b=E.Race.restore(E.SaveCodec.compactSnapshot(a.snapshot()));tick(a,600);tick(b,600);assert.deepEqual(physical(a),physical(b));assert.deepEqual(a.flags,b.flags);assert.equal(a.rng.state,b.rng.state)});
test('Moderate gap requires persistence; capture requires close physical contact',()=>{const r=pair(),[a,b]=r.riders;b.x=76;r.relations();assert.equal(r.groups.length,1);r.t=10.6;r.relations();assert.equal(r.groups.length,1);r.t=12;r.relations();assert.equal(r.groups.length,2);b.x=95;r.t=12.2;r.relations();assert.equal(r.groups.length,2);r.t=13.5;r.relations();assert.equal(r.groups.length,1)});
test('Coherent accelerating separation recognised within 1.2s',()=>{const r=pair(),[a,b]=r.riders;a.v=12;b.v=10;b.x=90;r.relations();assert.equal(r.groups.length,1);r.t=11.2;r.relations();assert.equal(r.groups.length,2);return {gapMetres:10,relativeSpeed:2,recognitionSeconds:1.2}});
test('Climbing-speed 4.4m paceline can rejoin, not remain separate forever',()=>{const r=pair(),[a,b]=r.riders;a.v=b.v=5.5;a.grade=b.grade=.07;a.groupUid=101;b.groupUid=102;b.x=a.x-4.4;r.relations();assert.equal(r.groups.length,2);r.t=11.4;r.relations();assert.equal(r.groups.length,1)});
test('Brief transient gap does not flicker group identity',()=>{const r=pair(),[a,b]=r.riders;b.x=96;r.relations();for(let i=1;i<=8;i++){r.t=10+i*.3;b.x=i===2||i===5?82:96;r.relations();assert.equal(r.groups.length,1)}});
test('Largest fragment retains UID when a small break leaves its front',()=>{const r=new E.Race(4);for(let i=0;i<184;i++){const x=r.riders[i];Object.assign(x,{x:i<5?500-i*4:200-Math.floor((i-5)/6)*4.4,groupUid:777,v:10,grade:0});}r.groups=[];r.relations();assert.equal(r.groups.length,2);assert.equal(r.groups[1].uid,777);assert.equal(r.groups[0].kind,'BREAKAWAY');assert.notEqual(r.groups[0].uid,777);assert(E.fieldAccounting(r).closed)});
test('All 184 riders accounted for across many groups and terminal statuses',()=>{const r=new E.Race(4);r.riders.forEach((x,i)=>Object.assign(x,{x:5000-Math.floor(i/9)*100-(i%9)*4,groupUid:1}));r.riders[0].status='FINISHED';r.riders[1].status='DNF';r.riders[2].status='OTL';r.riders[3].status='DNS';r.relations();const a=E.fieldAccounting(r);assert(a.closed);assert.equal(a.racing+a.finished+a.exited+a.dns,184);assert(a.groups>4);assert.equal(a.assigned,180);return a});
test('Finished rider leaves groups in the same simulation tick',()=>{const r=new E.Race(4),x=r.riders[14];x.x=r.stage.length-.001;x.v=10;r.nextRelations=r.t+10;r.tick();assert(!E.isRacing(x));assert(E.fieldAccounting(r).closed);assert(!r.groups.some(g=>g.ids.includes(x.id)))});
test('Several GC teams organise pursuit of a real separated GC threat',()=>{const r=new E.Race(18);r.t=80;r.stepCount=1600;for(const x of r.riders)Object.assign(x,{x:1000-Math.floor(x.id/6)*4.4,v:10,energy:100,w:x.d.wCapacity,spent:false,inBreak:false,aiAttackUntil:0,attackUntil:0});const attacker=r.player;Object.assign(attacker,{x:1210,attackUntil:90});r.coreX=1000;r.coreV=10;r.relations();r.updateTactics();const plans=r.teams.filter(t=>t.objective==='gc-chase');assert(plans.length>=3);assert(plans.every(p=>p.teamId!==0));assert(plans.every(p=>p.chaseReason===0));return plans.map(p=>({team:p.teamId,target:p.chaseReason,worker:p.workerId}))});
test('Harmless early break is not treated as a GC threat',()=>{const r=new E.Race(4),x=r.riders.find(x=>!r.gcIds.includes(x.id)&&x.d.role!=='GC'&&x.d.teamId!==0);x.x=150;for(const y of r.riders)if(y!==x)y.x=0;x.inBreak=true;r.relations();assert.equal(r.threatFor(r.teams[0]),null)});
// V12's zero-latency reactToMoves fixture predates V17 reaction delays and
// support delegation. Test the current physical predecessor contract directly.
test('Response chain selects a real nearer wheel and never a wheel behind',()=>{
 const r=new E.Race(18),ids=r.gcIds.filter(id=>id!==0).slice(0,3),f=r.player;
 for(const x of r.riders)Object.assign(x,{x:0,v:10,drawLane:2,lane:2,spent:false,waiting:false});
 f.x=100;const [a,b,c]=ids.map(id=>r.riders[id]);a.x=95;b.x=90;c.x=85;
 const q={root:0,target:0,at:50,rootAt:50};
 assert.equal(r.responsePredecessor(c,q,[a.id,b.id]).id,b.id);
 b.x=80;assert.equal(r.responsePredecessor(c,q,[a.id,b.id]).id,a.id);
 a.spent=true;assert.equal(r.responsePredecessor(c,q,[a.id,b.id]).id,0);
 return {root:0,intermediate:ids};
});

for(const kind of ['sprint','kom'])test('Relevant riders contest '+kind+' without pulling all GC helpers away',()=>{const stage=kind==='sprint'?4:18,r=new E.Race(stage),c=r.checkpoints.find(c=>c.kind===kind);assert(c);r.t=60;r.stepCount=1200;r.flags.nextOpportunity=0;for(const x of r.riders)Object.assign(x,{x:c.x-100,v:10,grade:kind==='kom'?.06:0,energy:100,w:x.d.wCapacity,nextAttack:0,recoveryUntil:0,spent:false,grupetto:false,missionLastPoint:-1,missionKind:null,missionTarget:null,missionPhase:'none',missionAttempts:0});r.rng.next=()=>0;r.checkpointTactics();const chosen=r.riders.filter(x=>x.missionTarget===c.id&&x.missionPhase==='approach');assert(chosen.length>=3);assert(chosen.length<7);assert(!chosen.some(x=>x.id===r.teams[x.d.teamId].gcId&&r.teams[x.d.teamId].gcTeam));for(const p of r.teams.filter(x=>x.gcTeam))assert(chosen.filter(x=>x.d.teamId===p.teamId).length<=1);for(const x of chosen)x.x=c.x-60;r.t+=4;r.flags.nextOpportunity=0;r.checkpointTactics();assert(r.riders.some(x=>x.missionPhase==='contest'));return chosen.map(x=>({id:x.id,role:x.d.role,team:x.d.teamId}))});
test('Floating role is separate from team job; protected GC and working helper are distinct',()=>{const r=new E.Race(4),leader=r.player,helper=r.riders[r.teams[0].helpers[0]];assert.equal(E.riderRoleLabel(leader,r),'GC 主将');assert.equal(E.riderRoleLabel(helper,r),'副将');helper.inBreak=true;assert.notEqual(E.riderRoleLabel(helper,r),'副将')});
test('Highest priority actual status wins over a generic attacking label',()=>{const r=new E.Race(4),x=r.riders[1];x.missionPhase='contest';x.missionKind='kom';x.aiAttackUntil=100;assert.equal(E.riderAction(x,r),'争抢爬坡点');x.missionKind='sprint';assert.equal(E.riderAction(x,r),'争抢冲刺点');x.missionPhase='none';x.aiAttackUntil=0;x.feedStart=-1;x.feedEnd=10;assert.equal(E.riderAction(x,r),'补给中')});
test('Sparse label budgets and all fixed slots remain non-overlapping',()=>{for(const w of [280,320,390,549,550,800,1134,1500]){assert(E.LabelMotion.budget(w,'calm')<=4);assert(E.LabelMotion.budget(w,'standard')<=5);const slots=E.LabelMotion.slots(w,370,[{x:w*.6,y:300,scale:.7}]);for(const a of slots){assert(a.x>=0&&a.x+a.w<=w);for(const b of slots)if(a!==b)assert(!(a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y))}}});
test('Minimum dwell survives a new ordinary candidate but explicit inspection wins',()=>{const labels=new Map([[7,{desired:true,visibleSince:10}]]),c=[{id:7,value:0,kind:'nearby',distance:15},{id:8,value:910,kind:'wheel',distance:2}];assert.equal(E.LabelMotion.select(c,labels,1,11)[0].id,7);c.push({id:9,value:980,kind:'inspect',distance:40});assert.equal(E.LabelMotion.select(c,labels,1,11)[0].id,9)});
test('Depth decluttering has no physical or RNG effect and never shifts progress',()=>{const r=new E.Race(4);tick(r,240);const before=plain(r.snapshot()),v=new E.RaceView(r);for(let i=0;i<40;i++)v.update(r.t+i*.05,1134,370);assert.deepEqual(plain(r.snapshot()),before);for(const x of v.riders.values()){assert.equal(x.world,x.r.x);assert(Math.abs(x.target-x.physicalDepth)<=1.080001)};return {riders:v.riders.size,maxDepthOffset:Math.max(...[...v.riders.values()].map(x=>Math.abs(x.target-x.physicalDepth)))}});
// Timing/award rules are unchanged source functions. Presentation changes cannot re-score a podium.
if(O)test('Classification, physiology and fatigue remain unchanged',()=>{for(const key of ['Classification','Physics','Physiology','Fatigue'])for(const field of Object.keys(O[key]))if(typeof O[key][field]==='function')assert.equal(E[key][field].toString().replace(/\r\n/g,'\n'),O[key][field].toString().replace(/\r\n/g,'\n'));});
if(O)test('Timing and unchanged save codec helpers remain identical to V22',()=>{let count=0;for(const [a,b] of [[E.RaceTiming,O.RaceTiming],[E.SaveCodec,O.SaveCodec]])for(const key of Object.getOwnPropertyNames(b))if(typeof b[key]==='function'&&!(b===O.SaveCodec&&['encode','decode'].includes(key))){assert.equal(a[key].toString().replace(/\r\n/g,'\n'),b[key].toString().replace(/\r\n/g,'\n'),key);count++;}return {functions:count}});

test('Intermediate sprint contender recognises a rival with the same mission',()=>{
 const r=new E.Race(4),a=r.riders.find(a=>a.id!==0&&!r.teams[a.d.teamId].gcTeam&&!r.protected&&a.d.role!=='Sprinter'),b=r.riders.find(b=>b.d.teamId!==a.d.teamId&&b.id!==0&&!r.teams[b.d.teamId].gcTeam);
 r.t=60;Object.assign(a,{x:100,v:11,drawLane:2,energy:95,w:a.d.wCapacity,missionKind:'sprint',missionTarget:0,missionPhase:'approach',recoveryUntil:0});Object.assign(b,{x:109,v:12,drawLane:2,missionKind:'sprint',missionTarget:0});
 const interest=r.moveInterest(a,b,{kind:'points-sprint',joined:[]});assert(interest>0);return {id:a.id,target:b.id,interest};
});
test('A break works under capture risk but will not chase its own team-mate',()=>{
 const r=new E.Race(4),a=r.riders.find(a=>a.id!==0&&!r.teams[a.d.teamId].gcTeam),plan=r.teams[a.d.teamId],mate=r.riders[plan.memberIds.find(id=>id!==a.id)],chaser=r.riders.find(x=>x.d.teamId!==a.d.teamId);
 for(const x of r.riders)Object.assign(x,{x:0,v:10,groupUid:9});Object.assign(a,{x:1000,v:10,groupUid:7,groupId:0,energy:95,w:a.d.wCapacity});Object.assign(chaser,{x:968,v:12.5,groupUid:8});
 r.groups=[{id:0,uid:7,ids:[a.id],count:4,kind:'BREAKAWAY',front:1000,back:1000},{id:1,uid:8,ids:[chaser.id],count:8,front:968,back:960}];plan.chaseReason=null;
 const work=r.cooperationFor(a);assert.equal(work.reason,'DEFEND_BREAK');assert(work.willingness>.7);
 Object.assign(mate,{x:1100,groupUid:6});const sit=r.cooperationFor(a);assert.equal(sit.reason,'TEAMMATE_AHEAD');assert(sit.skip);
 a.energy=20;assert.equal(r.cooperationFor(a).reason,'LOW_RESERVES');return {work,sit};
});
test('GC standings change risk appetite while a short crest remains ineligible',()=>{
 const r=new E.Race(18),a=r.riders[r.gcIds.find(id=>id!==0)],plan=r.teams[a.d.teamId],climb=r.lastClimb;
 Object.assign(a,{x:climb.foot+(climb.x-climb.foot)*.62,grade:.08,v:6,energy:98,w:a.d.wCapacity,fatigue:0});
 for(const x of r.riders)if(x.id!==a.id){x.x=a.x-12;x.spent=!x.protected;}
 r.relations();r.prior={season:{gcTimes:E.zeroField(),active:Array(184).fill(true)}};
 const defend=r.gcAttackAssessment(a,plan);r.prior.season.gcTimes[a.id]=240;const gain=r.gcAttackAssessment(a,plan);
 assert(defend.defending);assert(!gain.defending);assert(gain.score>defend.score+.2);assert(gain.commit);
 a.x=climb.x-12;assert(!r.gcAttackAssessment(a,plan).commit);return {defend,gain};
});
test('Post-sprint passive bunch recovers through power without changing timing rules',()=>{
 const snapshot=JSON.parse(require('node:zlib').gunzipSync(fs.readFileSync(path.join(__dirname,'fixtures/post-sprint-stall.json.gz'))));
 const r=E.Race.restore(snapshot),before=physical(r),slow=r.riders.filter(x=>E.isRacing(x)&&x.v<3).length;
 assert(slow>50);tick(r,400);
 const after=r.riders.filter(x=>E.isRacing(x)&&x.v<3).length;
 assert.equal(after,0);assert(E.fieldAccounting(r).closed);
 for(const x of r.riders.filter(E.isRacing)){assert(x.x>=before[x.id].x);assert(x.x-before[x.id].x<=600);assert(x.w<=x.d.wCapacity+.001);assert(x.energy<=100);}
 return {source:'actual stage 21, seed 477979, t=150.05; corrected sprint mission exposed passive pace feedback',slowBefore:slow,slowAfter:after,seconds:20};
});

test('Open-road cruise preserves an intentional rescue and a real slow wheel',()=>{
 const r=pair(),[a,b]=r.riders;a.id=0;b.x=104.4;a.v=b.v=3;a.drawLane=b.drawLane=2;a.grade=b.grade=0;a.power=b.power=80;
 r.relations();let watts=r.flowPower(a);assert(watts<E.Physics.sustainable(a)*.35);
 b.status='DNS';r.groups=[];r.t+=1;r.relations();a.brake=0;watts=r.flowPower(a);assert(watts>E.Physics.sustainable(a)*.6);
 const plan=r.teams[a.d.teamId];plan.leaderId=a.id;r.flags.leaderSupport={[plan.teamId]:{rescueGroup:99}};a.brake=0;
 const rescue=r.flowPower(a);assert(rescue<watts);return {cruiseWatts:watts,rescueWatts:rescue};
});

test('Nominated sprinter buys local position, respects a fast train and low reserves',()=>{
 const r=new E.Race(4,0,'single',null,2026),plan=r.teams.find(p=>p.teamObjective==='SPRINT'),a=r.riders[plan.leaderId];
 const live=[a,...r.riders.filter(x=>x.id!==0&&x.d.teamId!==a.d.teamId).slice(0,7)],x=r.course.toLocal(r.stage.reference.length-12000);
 for(const z of r.riders)z.status='DNS';live.forEach((z,i)=>Object.assign(z,{status:'RACING',x:x+i*5,v:11,grade:0,drawLane:2,lane:2,power:240,energy:85,w:z.d.wCapacity,aiState:'follow',groupUid:7,spent:false,waiting:false,grupetto:false,inBreak:false,sprintStarted:null}));r.groups=[];r.t=150;r.relations();a.trainTarget=-1;
 const before=[a.x,a.v,a.w,a.energy],watts=r.sprintPositionPower(a);assert(Number.isFinite(watts)&&watts>0);assert.equal(a.aiState,'positioning');assert.deepEqual([a.x,a.v,a.w,a.energy],before);
 const f=live[1];a.trainTarget=f.id;f.v=13;plan.paceline={order:[f.id,a.id]};assert.equal(r.sprintPositionPower(a),null);
 a.trainTarget=-1;a.w=a.d.wCapacity*.1;assert.equal(r.sprintPositionPower(a),null);return {id:a.id,watts};
});

test('A recalled helper cannot invalidate a race save; old V9 metadata is repaired',()=>{
 const snapshot=JSON.parse(require('node:zlib').gunzipSync(fs.readFileSync(path.join(__dirname,'fixtures/recalled-helper.json.gz'))));
 const q=E.Race.restore(snapshot);assert.deepEqual(q.riders.map(x=>[x.x,x.v,x.w,x.energy]),snapshot.riders.map(x=>[x.x,x.v,x.w,x.energy]));
 for(const p of q.teams)assert(!p.paceline?.trimmed?.some(id=>p.paceline.order.includes(id)));
 tick(q,400);const resumed=E.Race.restore(q.snapshot());tick(q,200);tick(resumed,200);assert.deepEqual(physical(q),physical(resumed));
 const bad=plain(snapshot);bad.teams[9].paceline.trimmed.push(183);assert.throws(()=>E.Race.restore(bad));return {stage:3,time:snapshot.t,helper:12,continuedSeconds:30};
});

test('Road grade has inertia with no physical-coordinate or snapshot changes',()=>{
 const r=new E.Race(4),v=new E.RaceView(r);r.player.grade=.08;v.update(0,1400,460);r.player.grade=-.06;const before=JSON.stringify(r.snapshot());
 v.update(.05,1400,460);assert(v.roadGrade>0);for(let i=2;i<=80;i++)v.update(i*.05,1400,460);
 assert(Math.abs(v.roadGrade+.06)<.001);assert.equal(JSON.stringify(r.snapshot()),before);return {settledGrade:v.roadGrade};
});
test('Awards are record-derived and the final GC is the last presentation',()=>{
 const r=new E.Race(4);while(!r.complete)r.tick();const record=r.result(),before=JSON.stringify(record);
 const ordinary=E.CeremonyStage.direct(E.Ceremony.plan(record,'single'));
 assert.equal(ordinary.beats[0].kind,'winner');assert.equal(ordinary.beats.find(b=>b.kind==='winner').ids[0],record.places.indexOf(1));
 for(const key of ['green','polka','white','yellow']){const beat=ordinary.beats.find(b=>b.kind===key);if(beat){assert.equal(beat.ids[0],record.season.leaders[key]);const scene=E.CeremonyStage.scene(ordinary,beat.start+13,E.CeremonyStage.metrics(1280,720));assert.equal(scene.actors[0].jersey,key);assert.equal(scene.prop.type,'flowers');}}
 // Explicit synthetic identity fixture: only the scheduler sees stage=20.
 const fixture={...record,stage:20},final=E.CeremonyStage.direct(E.Ceremony.plan(fixture,'tour'));
 assert.equal(final.beats.at(-2).kind,'gc-final');assert.deepEqual(final.beats.at(-2).ids,E.Classification.gcOrder(record.season).slice(0,3));assert(!final.beats.some(b=>b.kind==='yellow'));
 const m=E.CeremonyStage.metrics(1280,720,true),b=final.beats.at(-2),poses=E.CeremonyStage.scene(final,b.start+21,m).actors;
 assert(poses[1].x<poses[0].x&&poses[0].x<poses[2].x);assert(poses[2].entryAt<poses[1].entryAt&&poses[1].entryAt<poses[0].entryAt);
 assert(poses[0].entryStart>poses[1].entryStart);assert.equal(poses[0].jersey,'yellow');
 for(let i=1;i<poses.length;i++)assert.equal(poses[i].jersey,['green','polka','white'].find(k=>record.season.leaders[k]===poses[i].id)||null);
 const end=E.CeremonyStage.scene(final,final.beats.at(-1).start+.5,m);assert.equal(end.prop.type,'trophy');assert(end.actors[0].pose.lift>.99);assert(end.prop.twoHand);
 assert.equal(JSON.stringify(record),before);return {ordinary:ordinary.duration,final:final.duration,order:poses.map(p=>({id:p.id,entry:p.entryAt,x:p.x}))};
});

process.exitCode=checks.some(c=>!c.pass)?1:0;
