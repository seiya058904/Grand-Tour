'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const {loadEngine} = require('../v24/engine-loader.cjs');
const {sceneHarness, interiorTransitions} = require('./render-harness.cjs');
const file = process.argv[2] || path.join(__dirname, '../../Grand-Tour-V25.html');
const out = process.argv[3];
const E = loadEngine(file).engine, painter = sceneHarness(file);
// Natural production V24 (sha256 b5d0899fad82ed6576f416e12267ec6d369405a4dfa56559e5629e6fcf00fa1f)
// seed 2058765, stages 5 and 19. Recorded every ten real Race.tick() steps.
// These are observed camera/altitude inputs, not fabricated rider states.
const naturalPairs = [{"stage":5,"field":"buildings","before":{"tick":170,"t":8.5,"x":78.19315622406609,"altitude":550.0741578430625},"after":{"tick":180,"t":9,"x":84.07436055926503,"altitude":546.3311922764736}},{"stage":5,"field":"buildings","before":{"tick":190,"t":9.5,"x":90.0092488109121,"altitude":542.5540254459129},"after":{"tick":200,"t":10,"x":95.9977620965542,"altitude":538.7426954033208}},{"stage":5,"field":"buildings","before":{"tick":2600,"t":130,"x":1598.357938941496,"altitude":257.5892683436047},"after":{"tick":2610,"t":130.5,"x":1604.242979265067,"altitude":255.09370709679158}},{"stage":5,"field":"buildings","before":{"tick":2670,"t":133.5,"x":1640.995466088126,"altitude":235.01314453094},"after":{"tick":2680,"t":134,"x":1647.3194167562863,"altitude":231.55151793001684}},{"stage":5,"field":"buildings","before":{"tick":2720,"t":136,"x":1673.062230602183,"altitude":209.71064264828456},"after":{"tick":2730,"t":136.5,"x":1679.6069712381084,"altitude":202.44303689803854}},{"stage":5,"field":"buildings","before":{"tick":3620,"t":181,"x":2247.4061856529356,"altitude":338.8349330382704},"after":{"tick":3630,"t":181.5,"x":2253.03927611637,"altitude":328.53163121272655}},{"stage":5,"field":"buildings","before":{"tick":3740,"t":187,"x":2321.051620575306,"altitude":263.6324151365336},"after":{"tick":3750,"t":187.5,"x":2327.3953471823106,"altitude":280.96784887466714}},{"stage":5,"field":"buildings","before":{"tick":4120,"t":206,"x":2570.8890495097426,"altitude":302.2924432768413},"after":{"tick":4130,"t":206.5,"x":2577.65821052833,"altitude":301.2430632073384}},{"stage":5,"field":"buildings","before":{"tick":4300,"t":215,"x":2690.7746329963024,"altitude":309.14125959114875},"after":{"tick":4310,"t":215.5,"x":2696.9623420655566,"altitude":311.9928481979542}},{"stage":19,"field":"buildings","before":{"tick":3650,"t":182.5,"x":1653.936746462896,"altitude":1138.8035401138457},"after":{"tick":3660,"t":183,"x":1661.783765490144,"altitude":1130.7964611513078}},{"stage":19,"field":"buildings","before":{"tick":3790,"t":189.5,"x":1767.4648613162872,"altitude":1021.0724741679605},"after":{"tick":3800,"t":190,"x":1775.784557508106,"altitude":1011.1462196028803}},{"stage":19,"field":"buildings","before":{"tick":3900,"t":195,"x":1860.7050985982648,"altitude":929.7546281866285},"after":{"tick":3910,"t":195.5,"x":1869.2242292161652,"altitude":925.1892597289961}},{"stage":19,"field":"buildings","before":{"tick":4490,"t":224.5,"x":2316.546740655534,"altitude":920.0919395532857},"after":{"tick":4500,"t":225,"x":2323.7158176558123,"altitude":918.4581413814853}},{"stage":19,"field":"buildings","before":{"tick":4520,"t":226,"x":2338.0080226205123,"altitude":915.2011637060027},"after":{"tick":4530,"t":226.5,"x":2345.134245685151,"altitude":913.5772438133109}},{"stage":19,"field":"buildings","before":{"tick":4540,"t":227,"x":2352.2484459959287,"altitude":911.9560798585015},"after":{"tick":4550,"t":227.5,"x":2359.3512749460415,"altitude":910.33752037485}},{"stage":19,"field":"buildings","before":{"tick":4690,"t":234.5,"x":2455.609828910106,"altitude":924.1618204488136},"after":{"tick":4700,"t":235,"x":2462.3268840773235,"altitude":921.8911628782693}},{"stage":19,"field":"buildings","before":{"tick":4770,"t":238.5,"x":2509.6732377223666,"altitude":913.9181269195917},"after":{"tick":4780,"t":239,"x":2516.4410013128554,"altitude":914.6360529927364}},{"stage":19,"field":"buildings","before":{"tick":6150,"t":307.5,"x":3450.9821180212994,"altitude":1030.3491826576542},"after":{"tick":6160,"t":308,"x":3455.1293582250146,"altitude":1041.7483388332512}},{"stage":19,"field":"buildings","before":{"tick":6670,"t":333.5,"x":3697.2404498093424,"altitude":1199.833601039979},"after":{"tick":6680,"t":334,"x":3704.637902007925,"altitude":1190.118059869711}},{"stage":19,"field":"buildings","before":{"tick":7480,"t":374,"x":4397.3734190482965,"altitude":758.7386119591837},"after":{"tick":7490,"t":374.5,"x":4404.282313917979,"altitude":763.7702076402409}},{"stage":19,"field":"buildings","before":{"tick":9120,"t":456,"x":4930.330589003707,"altitude":1536.7759498257287},"after":{"tick":9130,"t":456.5,"x":4932.780912312657,"altitude":1541.4424440714042}},{"stage":19,"field":"trees","before":{"tick":2540,"t":127,"x":1025.3836167314917,"altitude":1589.8314893997203},"after":{"tick":2550,"t":127.5,"x":1028.547071695756,"altitude":1592.5206312375312}},{"stage":19,"field":"trees","before":{"tick":2700,"t":135,"x":1076.77410713054,"altitude":1633.553222409935},"after":{"tick":2710,"t":135.5,"x":1079.8034225632555,"altitude":1636.1317386731848}},{"stage":19,"field":"trees","before":{"tick":2880,"t":144,"x":1133.520349924968,"altitude":1637.4592525424137},"after":{"tick":2890,"t":144.5,"x":1137.6729380454897,"altitude":1632.171385952722}},{"stage":19,"field":"trees","before":{"tick":9370,"t":468.5,"x":4991.318174098275,"altitude":1649.3385150889965},"after":{"tick":9380,"t":469,"x":4993.816087531344,"altitude":1653.5072202605409}},{"stage":19,"field":"trees","before":{"tick":9420,"t":471,"x":5003.893014064845,"altitude":1670.3259540114004},"after":{"tick":9430,"t":471.5,"x":5006.429363369601,"altitude":1674.5595340193195}},{"stage":19,"field":"trees","before":{"tick":9430,"t":471.5,"x":5006.429363369601,"altitude":1674.5595340193195},"after":{"tick":9440,"t":472,"x":5008.971163394935,"altitude":1678.802315771572}},{"stage":19,"field":"trees","before":{"tick":9510,"t":475.5,"x":5026.875245988665,"altitude":1708.6899793267241},"after":{"tick":9520,"t":476,"x":5029.444432937632,"altitude":1712.978991449029}},{"stage":19,"field":"trees","before":{"tick":9680,"t":484,"x":5074.500255207183,"altitude":1756.6847837442517},"after":{"tick":9690,"t":484.5,"x":5077.702225370618,"altitude":1759.137479652228}},{"stage":19,"field":"trees","before":{"tick":9790,"t":489.5,"x":5111.1987108725625,"altitude":1784.8050109197472},"after":{"tick":9800,"t":490,"x":5114.66010964562,"altitude":1787.4580463066604}},{"stage":19,"field":"trees","before":{"tick":9840,"t":492,"x":5128.649097854514,"altitude":1798.1808689822326},"after":{"tick":9850,"t":492.5,"x":5132.177804901721,"altitude":1800.8858558794266}}];
const results = [];
function test(name, fn) {
  try { results.push({name, pass: true, detail: fn()}); }
  catch (error) { results.push({name, pass: false, error: error.stack}); }
}
const stages = new Map();
function stage(id) {
  if (!stages.has(id)) stages.set(id, new E.Race(id - 1, 0, 'single', null, 2058765).stage);
  return stages.get(id);
}
for (const [id, field] of [[5, 'buildings'], [19, 'buildings'], [19, 'trees']]) {
  test(`Natural stage ${id}: ${field} remain at fixed world locations`, () => {
    const pairs = naturalPairs.filter(p => p.stage === id && p.field === field);
    let geometry = 0;
    for (const pair of pairs) {
      const a = painter.backdrop(stage(id), pair.before.x, pair.before.altitude);
      const b = painter.backdrop(stage(id), pair.after.x, pair.after.altitude);
      const changes = interiorTransitions(a, b, field);
      assert.deepEqual(changes, [], `Interior object popped between simulation ${pair.before.t}s and ${pair.after.t}s`);
      geometry += a[field].length + b[field].length;
    }
    assert(geometry > pairs.length, 'Continuity must not be achieved by hiding the scenery');
    return {pairs: pairs.length, recordedObjects: geometry};
  });
}
test('Finish spectators enter with the roadside instead of appearing across the viewport', () => {
  const s = stage(5), a = painter.verge(s, s.length - 140.1), b = painter.verge(s, s.length - 139.9);
  assert(a.heads.length >= 4, 'The finish corridor should already be visible ahead');
  assert.equal(a.heads.length, b.heads.length, 'Crossing a player-distance threshold must not spawn a crowd');
  for (let i = 0; i < a.heads.length; i++) {
    assert(Math.abs(a.heads[i].x - b.heads[i].x - .2 * 18.5) < 1e-7, 'Spectators must retain the shared world projection');
    assert.equal(a.heads[i].y, b.heads[i].y);
  }
  return {before: a.heads.length, after: b.heads.length, cameraTravelMetres: .2};
});
test('Scenery remains deterministic and cannot change the simulation snapshot', () => {
  const race = new E.Race(18, 0, 'single', null, 2058765);
  for (let i = 0; i < 100; i++) race.tick();
  const before = JSON.stringify(race.snapshot());
  const a = painter.backdrop(race.stage, race.player.x, race.player.alt);
  const b = painter.backdrop(race.stage, race.player.x, race.player.alt);
  assert.deepEqual(a, b);
  painter.verge(race.stage, race.player.x);
  assert.equal(JSON.stringify(race.snapshot()), before);
  return {buildings: a.buildings.length, trees: a.trees.length, seed: race.seed};
});
const report = {
  source: file, sha256: crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),
  passed: results.filter(r => r.pass).length, failed: results.filter(r => !r.pass).length,
  skipped: 0, checks: results,
  scope: 'Production scenery painter call recorder; browser rasterization and visual QA run separately.'
};
if (out) fs.writeFileSync(out, JSON.stringify(report, null, 2));
for (const r of results) console.log(`${r.pass ? 'PASS' : 'FAIL'} ${r.name}${r.pass ? '' : ': ' + r.error.split('\n')[0]}`);
console.log(JSON.stringify({passed: report.passed, failed: report.failed, skipped: 0}));
process.exitCode = report.failed ? 1 : 0;
