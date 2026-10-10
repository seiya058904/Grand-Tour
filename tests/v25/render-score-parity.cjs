'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const {loadEngine} = require('../v24/engine-loader.cjs');
const baseline = process.argv[2] || path.join(__dirname, '../../Grand-Tour-V24.html');
const candidate = process.argv[3] || path.join(__dirname, '../../Grand-Tour-V25.html');
const output = process.argv[4];
const old = loadEngine(baseline).engine, next = loadEngine(candidate).engine;
const reports = [];
const viewState = v => JSON.stringify({
  cameraAnchor: v.cameraAnchor, lens: v.lens, roadGrade: v.roadGrade,
  riders: [...v.riders.values()].map(r => Object.fromEntries(Object.entries(r).filter(([key]) => key !== 'r')))
});
for (const index of [4, 18, 0, 15]) {
  const report = {name: `Stage ${index + 1}: V24/V25 depth targets and every pose field match`, pass: false};
  try {
    // Both read-only views observe exactly the same naturally evolving race.
    // This isolates the rendering optimization from independently audited V25
    // changes to race timing, AI, or save validation.
    const race = new old.Race(index, 0, 'single', null, 2058765);
    let updates = 0, comparedRiders = 0;
    for (const checkpoint of [100, 400]) {
      while (race.stepCount < checkpoint) race.tick();
      const a = new old.RaceView(race), b = new next.RaceView(race);
      for (let i = 0; i <= 60; i++) {
        if (i) race.tick();
        const physics = JSON.stringify(race.riders.map(r => [r.x, r.prevX, r.v, r.lane, r.drawLane, r.power, r.energy, r.w]));
        for (const alpha of [.15, .85]) {
          a.alpha = b.alpha = alpha;
          const visualTime = race.t - old.CONFIG.step + alpha * old.CONFIG.step;
          a.update(visualTime, 1400, 460); b.update(visualTime, 1400, 460);
          assert.equal(viewState(b), viewState(a), `Pose/target mismatch at tick ${race.stepCount}, alpha ${alpha}`);
          updates++; comparedRiders += a.riders.size;
        }
        assert.equal(JSON.stringify(race.riders.map(r => [r.x, r.prevX, r.v, r.lane, r.drawLane, r.power, r.energy, r.w])), physics);
      }
    }
    Object.assign(report, {pass: true, seed: race.seed, updates, comparedRiders});
  } catch (error) { report.error = error.stack; }
  reports.push(report);
  console.log(`${report.pass ? 'PASS' : 'FAIL'} ${report.name}${report.pass ? '' : ': ' + report.error.split('\n')[0]}`);
}
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const result = {
  baseline, baselineSha256: hash(baseline), candidate, candidateSha256: hash(candidate),
  passed: reports.filter(r => r.pass).length, failed: reports.filter(r => !r.pass).length, skipped: 0,
  checks: reports, scope: 'Exact view-state parity on natural race trajectories; not a frame-rate benchmark.'
};
if (output) fs.writeFileSync(output, JSON.stringify(result, null, 2));
console.log(JSON.stringify({passed: result.passed, failed: result.failed, skipped: 0}));
process.exitCode = result.failed ? 1 : 0;
