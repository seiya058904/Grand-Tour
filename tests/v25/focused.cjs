'use strict';
// Retain all 35 V24 checks. Only the expected build number/name changes.
// Compiling at the original module path preserves fixture and loader paths.
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const assert = require('node:assert/strict');
const original = path.resolve(__dirname, '../v24/focused.cjs');
let source = fs.readFileSync(original, 'utf8');
const identity = 'assert.equal(E.CONFIG.buildVersion,240)';
assert.equal(source.split(identity).length, 2, 'one explicit build-identity assertion');
source = source.replace(identity, 'assert.equal(E.CONFIG.buildVersion,250)')
  .replace('V24 retains storage key and schema V9', 'V25 retains storage key and schema V9')
  .replace('../../Grand-Tour-V24.html', '../../Grand-Tour-V25.html');
const suite = new Module(original, module);
suite.filename = original;
suite.paths = Module._nodeModulePaths(path.dirname(original));
suite._compile(source, original);
