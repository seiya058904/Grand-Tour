'use strict';
// Retain all 35 V24 checks through the same in-memory adapter V25 used.
// Changes: build identity 240→260, default file name, and one reviewed
// ceremony sampling time. V26 shortened each award from 20.8s to 10.5s, so
// the old probe at award start +13s lands in the *next* award. The probe moves
// to +8s (inside the same award, after the hand-off); every assertion is kept.
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const assert = require('node:assert/strict');
const original = path.resolve(__dirname, '../v24/focused.cjs');
let source = fs.readFileSync(original, 'utf8');
const swaps = [
  ['assert.equal(E.CONFIG.buildVersion,240)', 'assert.equal(E.CONFIG.buildVersion,260)'],
  ['V24 retains storage key and schema V9', 'V26 retains storage key and schema V9'],
  ['../../Grand-Tour-V24.html', '../../Grand-Tour-V26.html'],
  ['E.CeremonyStage.scene(ordinary,beat.start+13,', 'E.CeremonyStage.scene(ordinary,beat.start+8,'],
];
for (const [from, to] of swaps) {
  assert.equal(source.split(from).length, 2, 'exactly one occurrence: ' + from);
  source = source.replace(from, to);
}
const suite = new Module(original, module);
suite.filename = original;
suite.paths = Module._nodeModulePaths(path.dirname(original));
suite._compile(source, original);
