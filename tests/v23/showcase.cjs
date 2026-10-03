'use strict';
const fs=require('node:fs'),path=require('node:path'),{loadEngine}=require('./engine-loader.cjs');
const root=path.resolve(__dirname,'../..'),out=path.resolve(process.argv[2]),tourPath=process.argv[3],E=loadEngine(path.join(root,'archive/v23/Grand-Tour-V23.html')).engine;
fs.mkdirSync(out,{recursive:true});
const report={source:'current V23 production Race.tick; natural state, no rider/clock edits',snapshots:[]};
function save(r,name,reason){const s=r.snapshot();s.mode='tour';fs.writeFileSync(path.join(out,name+'-snapshot.json'),JSON.stringify(s));report.snapshots.push({name,stage:r.stageIndex+1,t:r.t,seed:r.seed,reason});console.log(name,r.t,reason);}
let r=new E.Race(4,0,'single',null,2058765),breakShot=false;
while(!r.complete){r.tick();if(!breakShot&&r.groups.some(g=>g.kind==='BREAKAWAY'&&g.count>=2)&&r.t>30){save(r,'breakaway','real breakaway group');breakShot=true;}if(r.order[0].x>r.stage.length-200){save(r,'stage-05-finale','real leading rider at final 200 compact metres');break;}}
r=new E.Race(0,0,'single',null,E.seedForStage(2026001,0));while(!r.complete){r.tick();if(r.order[0].x>r.stage.length-200){save(r,'stage-01-finale','real TTT finish approach');break;}}
r=new E.Race(2,0,'single',null,E.seedForStage(2026001,2));while(!r.complete){r.tick();if(r.t>80&&r.player.grade<-.055){save(r,'descent','actual downhill terrain');break;}}
const prior=tourPath?E.SaveCodec.decode(JSON.parse(fs.readFileSync(tourPath,'utf8'))).store.tour.results[17]:null;
r=new E.Race(18,0,'tour',prior,314159+18*8191);let found=false;
while(!r.complete){if(r.stepCount%20===0&&r.player.energy<70)r.feed();r.tick();const event=r.audit.attacks.find(e=>e.kind==='gcAttack');if(event){save(r,'gc-battle','natural GC attack by rider '+event.id);found=true;break;}}
if(!found)throw Error('No GC attack: do not manufacture a showcase');
fs.writeFileSync(path.join(out,'provenance.json'),JSON.stringify(report,null,2));
