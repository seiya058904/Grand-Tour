'use strict';
// Codec-only regression against the already generated natural V24 Tour fixture:
// seed 314159, original tests/v23/tour-simulation.cjs standard-GC-v2 policy.
// That particular Tour has 21 completed stages and 162 final-stage finishers.
// The finisher count is a fixture assertion, not a rule for arbitrary Tour seeds.
// No Race.tick() calls or new race simulation are performed here.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {loadEngine} = require(path.join(__dirname, '../v24/engine-loader.cjs'));
const [baseline, candidate, inputFile, outputFile] = process.argv.slice(2);
if (!baseline || !candidate || !inputFile || !outputFile) {
  throw new Error('Usage: node tests/v25/full-tour-compatibility.cjs baseline.html candidate.html natural-v24-tour-314159.json output.json');
}
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const plain = value => JSON.parse(JSON.stringify(value));
const inputBytes = fs.readFileSync(inputFile);
const input = JSON.parse(inputBytes);
const report = {
  input: path.resolve(inputFile), inputSHA256: hash(inputBytes), sources: [],
  fixture: {tourSeed: 314159, policy: 'standard-GC-v2', expectedStages: 21, expectedFinalFinishers: 162},
  normalization: "Both versions add the same default settings to the simulation export's empty settings object.",
  scope: 'Strict decode and encode of the existing natural V24 seed 314159 Tour fixture; 162 final finishers applies only to this fixture. No new race simulation.',
  passed: 0, failed: 0, skipped: 0, pass: false
};
try {
  assert.equal(input.version, 9);
  assert.equal(input.tour.seedBase, report.fixture.tourSeed, 'This regression requires the documented seed 314159 V24 Tour fixture');
  assert.equal(input.tour.results.length, report.fixture.expectedStages);
  const normalized = [];
  for (const file of [baseline, candidate]) {
    const sourceSHA256 = hash(fs.readFileSync(file));
    const E = loadEngine(file).engine;
    const value = plain(input), before = JSON.stringify(value);
    const decoded = E.SaveCodec.decode(value, {recover: false});
    assert.deepEqual(plain(decoded.issues), [], 'Strict decoding must not isolate or discard anything');
    assert.equal(decoded.store.tour.results.length, report.fixture.expectedStages, 'All original results retained');
    assert.equal(decoded.store.tour.results.at(-1).statuses.filter(s => s === 'FINISHED').length,
      report.fixture.expectedFinalFinishers, 'The documented natural seed 314159 fixture retains its 162 final finishers');
    assert.equal(JSON.stringify(value), before, 'Input object unchanged');
    const encoded = plain(E.SaveCodec.encode(decoded.store));
    normalized.push(encoded);
    assert.equal(hash(fs.readFileSync(file)), sourceSHA256, 'Source unchanged during quick codec check');
    report.sources.push({source: file, sourceSHA256, issues: plain(decoded.issues),
      retainedStages: encoded.tour.results.length,
      normalizedOutputSHA256: hash(JSON.stringify(encoded))});
  }
  assert.deepEqual(normalized[1], normalized[0], 'Whole normalized outputs must agree, including settings defaults');
  assert.equal(hash(fs.readFileSync(inputFile)), report.inputSHA256, 'Original stored V24 bytes unchanged');
  Object.assign(report, {retainedStages: report.fixture.expectedStages,
    finalFinishers: report.fixture.expectedFinalFinishers, normalizedOutputsIdentical: true,
    originalInputUnchanged: true, passed: 1, pass: true});
} catch (error) {
  report.failed = 1;
  report.error = error.stack;
  process.exitCode = 1;
}
fs.writeFileSync(outputFile, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
