'use strict';
// V25 changes only the recovery entry of SaveCodec.decode. Keep the original
// V24 parity suite intact and constrain this exception to its exact source.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {loadEngine}=require('../v23/engine-loader.cjs');
const [oldFile=path.join(__dirname,'../../Grand-Tour-V24.html'),newFile=path.join(__dirname,'../../Grand-Tour-V25.html'),out]=process.argv.slice(2);
const a=loadEngine(oldFile).engine,b=loadEngine(newFile).engine,sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const oldEntry="  const s=this.migrateStore(input),issues=[],results=[];let prior=null;";
const newEntry=`  let s,activeMigrationIssue=null;
  try{s=this.migrateStore(input);}catch(e){
   if(!recover||!input||typeof input!=='object'||Array.isArray(input)||!input.active)throw e;
   // Salvage only after the same migration validates the untouched outer save.
   // Strict imports still fail; the caller backs up the original raw bytes.
   s=this.migrateStore({...input,active:null});activeMigrationIssue='进行中比赛无法恢复：'+e.message;
  }
  const issues=activeMigrationIssue?[activeMigrationIssue]:[],results=[];let prior=null;`;
const norm=x=>typeof x==='function'?x.toString().replace(/\r\n/g,'\n'):
 typeof x==='string'?x.replace(/\r\n/g,'\n'):Array.isArray(x)?x.map(norm):
 x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,norm(x[k])])):x;
const props=x=>Object.fromEntries(Object.getOwnPropertyNames(x).filter(k=>!['length','name','prototype','arguments','caller'].includes(k)).map(k=>[k,x[k]]));
const signature=x=>JSON.stringify(norm(typeof x==='function'?{constructor:x.toString(),statics:props(x),prototype:props(x.prototype)}:x));
assert.equal(a.SaveCodec.decode.toString().split(oldEntry).length,2,'exact old recovery entry appears once');
assert.equal(b.SaveCodec.decode.toString().split(newEntry).length,2,'exact reviewed new recovery entry appears once');
const checks=[];
for(const key of ['Race','Physics','Physiology','Fatigue','Weather','RaceTiming','TeamClassification','Classification','TimeLimits','CompactCourse','SaveCodec','SimulationClock','RIDER_DATA','STAGE_DATA']){
 const before=signature(a[key]);
 const current=key==='SaveCodec'?{...b[key],decode:b[key].decode.toString().replace(newEntry,oldEntry)}:b[key];
 const after=signature(current);
 assert.equal(after,before,key+' source parity (only explicit recovery entry may differ)');
 checks.push({name:key,pass:true,sha256:sha(after),exception:key==='SaveCodec'?'Exact reviewed decode entry only':null});
}
const report={source:newFile,sourceSHA256:sha(fs.readFileSync(newFile)),baseline:oldFile,baselineSHA256:sha(fs.readFileSync(oldFile)),
 exceptions:[{name:'V25 active migration recovery',oldEntry,newEntry,reason:'Recover a damaged active race without discarding validated previous stages; strict import still rejects.'}],checks,passed:checks.length,failed:0,skipped:0,pass:true};
if(out)fs.writeFileSync(out,JSON.stringify(report,null,2));
console.log('PASS 13 unchanged engine/data families; SaveCodec differs only at the exact reviewed recovery entry.');
