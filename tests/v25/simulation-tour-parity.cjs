'use strict';
// Compare complete, newly generated V9 Tour objects. Performance timings and
// source paths stay in the driver reports; no race-record field is ignored.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const [baselineFile,candidateFile,baselineReportFile,candidateReportFile,out]=process.argv.slice(2);
if(!baselineFile||!candidateFile||!baselineReportFile||!candidateReportFile)throw new Error('Usage: node tests/v25/simulation-tour-parity.cjs baseline-tour.json candidate-tour.json baseline-report.json candidate-report.json [outside-result.json]');
const read=file=>JSON.parse(fs.readFileSync(file,'utf8')),sha=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const baseline=read(baselineFile),candidate=read(candidateFile),a=read(baselineReportFile),b=read(candidateReportFile);
const report={baseline:{file:path.basename(baselineFile),sha256:sha(baselineFile),source:a.source,sourceSha256:a.sha256,seed:a.seed,stages:a.stages.length,snapshotRestores:a.snapshotRestores},candidate:{file:path.basename(candidateFile),sha256:sha(candidateFile),source:b.source,sourceSha256:b.sha256,seed:b.seed,stages:b.stages.length,snapshotRestores:b.snapshotRestores},pass:false};
try{
 assert.equal(baseline.version,9,'baseline V9 format');assert.equal(candidate.version,9,'candidate V9 format');
 assert.equal(a.seed,b.seed,'same Tour seed');assert.equal(a.stages.length,21,'baseline complete');assert.equal(b.stages.length,21,'candidate complete');
 assert.equal(baseline.tour.results.length,21,'baseline has every stage');assert.equal(candidate.tour.results.length,21,'candidate has every stage');
 assert(a.snapshotRestores>0&&b.snapshotRestores>0,'both runs exercised natural restore');
 assert.deepStrictEqual(candidate,baseline,'entire V9 object, including every stage result and all rider state arrays');
 report.pass=true;report.checkedStages=21;report.finalField={starting:b.stages.at(-1).starting,finished:b.stages.at(-1).finishers,priorExits:b.stages.at(-1).DNS};
}catch(e){report.error=e.message;process.exitCode=1;}
if(out){fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');}console.log(JSON.stringify(report,null,2));
