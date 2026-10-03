'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { loadEngine } = require('./engine-loader.cjs');
const file = process.argv[2] || 'archive/v23/Grand-Tour-V23.html';
const { engine: E } = loadEngine(file, false);
const reports = [];
for (const seed of [314159, 12345]) for (const mode of ['auto', 'early', 'late', 'restore-auto']) {
  let race = new E.Race(0, 0, 'tour', null, seed), selected = false, resumed = false, restored = false;
  let invalidSeconds = 0, stallSeconds = 0, normalFollowSteps = 0;
  while (!race.complete && race.t < 4000) {
    const target = race.riders[19];
    if (mode !== 'auto' && !selected && (mode === 'late' ? race.player.x >= race.stage.length * .18 : race.t >= 3)) {
      assert.equal(race.selectWheel(19).ok, true, `${seed}/${mode}: natural wheel selection must be legal`);
      assert.equal(race.selectedWheel, 19);
      selected = true;
    }
    if (selected && !restored && race.t > 31) { race = E.Race.restore(race.snapshot()); restored = true; }
    if (mode === 'restore-auto' && selected && !resumed && race.t > 40) { assert.equal(race.automaticWheel(), true); resumed = true; }
    if (race.selectedWheel === 19 && (target.tttDone || target.spent)) invalidSeconds += .05;
    if (race.selectedWheel === 19 && !target.tttDone && !target.spent) normalFollowSteps++;
    if (race.player.v < 1.6 && race.player.power < 1 && race.player.energy > 50 && race.t > 60) stallSeconds += .05;
    race.tick();
  }
  const result = race.result();
  reports.push({ seed, mode, complete: race.complete, player: result.statuses[0], otl: result.statuses.filter(s => s === 'OTL').length, invalidSeconds, stallSeconds, normalFollowSteps, restored, resumed });
}
console.log(JSON.stringify(reports, null, 2));
if (process.argv[3]) fs.writeFileSync(process.argv[3], JSON.stringify(reports, null, 2));
for (const row of reports) {
  assert(row.complete, JSON.stringify(row));
  assert.equal(row.player, 'FINISHED', JSON.stringify(row));
  assert.equal(row.otl, 0, JSON.stringify(row));
  assert(row.invalidSeconds <= .1, JSON.stringify(row));
  assert(row.stallSeconds < 1, JSON.stringify(row));
  if (row.mode !== 'auto') { assert(row.normalFollowSteps > 20, JSON.stringify(row)); assert(row.restored); }
  if (row.mode === 'restore-auto') assert(row.resumed);
}
