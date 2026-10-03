'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict'),crypto=require('node:crypto'),{loadEngine}=require('../v23/engine-loader.cjs');
const [oldFile,newFile,out]=process.argv.slice(2),a=loadEngine(oldFile).engine,b=loadEngine(newFile).engine;
const normalize=x=>typeof x==='function'?x.toString().replace(/\r\n/g,'\n'):Array.isArray(x)?x.map(normalize):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,normalize(x[k])])):typeof x==='string'?x.replace(/\r\n/g,'\n'):x;
const classes=['Race','Physics','Physiology','Fatigue','Weather','RaceTiming','TeamClassification','Classification','TimeLimits','CompactCourse','SaveCodec','SimulationClock'];
const checks=[];for(const key of [...classes,'RIDER_DATA','STAGE_DATA']){
 const properties=x=>Object.fromEntries(Object.getOwnPropertyNames(x).filter(k=>!['length','name','prototype','arguments','caller'].includes(k)).map(k=>[k,x[k]]));
 const signature=x=>JSON.stringify(normalize(typeof x==='function'?{constructor:x.toString(),statics:properties(x),prototype:properties(x.prototype)}:x));
 const before=signature(a[key]),after=signature(b[key]),sha=s=>crypto.createHash('sha256').update(s).digest('hex');assert.equal(sha(after),sha(before),key+' is unchanged');checks.push({name:key,sha256:sha(after),pass:true});
}
const report={source:newFile,sha256:crypto.createHash('sha256').update(fs.readFileSync(newFile)).digest('hex'),baseline:oldFile,checks,pass:true};fs.writeFileSync(out,JSON.stringify(report,null,2));console.log('PASS all simulation/data/codec signatures unchanged');
