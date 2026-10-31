'use strict';
// V26 is presentation-only. All 14 engine/data families must be source-identical
// to V25 with no exceptions (V25's reviewed SaveCodec entry is inherited as-is).
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {loadEngine}=require('../v23/engine-loader.cjs');
const [oldFile=path.join(__dirname,'../../Grand-Tour-V25.html'),newFile=path.join(__dirname,'../../Grand-Tour-V26.html'),out]=process.argv.slice(2);
const a=loadEngine(oldFile).engine,b=loadEngine(newFile).engine,sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const norm=x=>typeof x==='function'?x.toString().replace(/\r\n/g,'\n'):
 typeof x==='string'?x.replace(/\r\n/g,'\n'):Array.isArray(x)?x.map(norm):
 x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,norm(x[k])])):x;
const props=x=>Object.fromEntries(Object.getOwnPropertyNames(x).filter(k=>!['length','name','prototype','arguments','caller'].includes(k)).map(k=>[k,x[k]]));
const signature=x=>JSON.stringify(norm(typeof x==='function'?{constructor:x.toString(),statics:props(x),prototype:props(x.prototype)}:x));
const families=['Race','Physics','Physiology','Fatigue','Weather','RaceTiming','TeamClassification','Classification','TimeLimits','CompactCourse','SaveCodec','SimulationClock','RIDER_DATA','STAGE_DATA'];
const checks=[];
for(const key of families){const before=signature(a[key]),after=signature(b[key]);assert.equal(after,before,key+' source parity');checks.push({name:key,pass:true,sha256:sha(after)});}
// Storage identity is part of the save contract; only the build number moves.
assert.equal(b.CONFIG.saveKey,a.CONFIG.saveKey);assert.equal(b.CONFIG.saveVersion,a.CONFIG.saveVersion);assert.equal(b.CONFIG.step,a.CONFIG.step);
assert.deepEqual({...b.CONFIG,buildVersion:0},{...a.CONFIG,buildVersion:0});assert.equal(b.CONFIG.buildVersion,260);
checks.push({name:'CONFIG except buildVersion 250→260',pass:true});
const report={source:newFile,sourceSHA256:sha(fs.readFileSync(newFile)),baseline:oldFile,baselineSHA256:sha(fs.readFileSync(oldFile)),exceptions:[],checks,passed:checks.length,failed:0,pass:true};
if(out)fs.writeFileSync(out,JSON.stringify(report,null,2));
console.log('PASS 14 engine/data families identical to V25 with zero exceptions; CONFIG differs only in buildVersion.');
