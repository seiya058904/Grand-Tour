'use strict';
// V26 ceremony director regression. Ports the V24 award identity/order checks
// to the new timing and adds determinism, continuity and read-only checks.
// Usage: node tests/v26/ceremony.cjs [Grand-Tour-V26.html] [out.json]
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const {loadEngine} = require('../v23/engine-loader.cjs');
const file = process.argv[2] || path.join(__dirname, '../../Grand-Tour-V26.html');
const out = process.argv[3];
const L = loadEngine(file), E = L.engine, S = E.CeremonyStage;

// Recording 2D context: hashes every call and argument (rounded), so two paints
// of the same presentation time can be compared without a browser.
function recorder() {
  let hash = crypto.createHash('sha256'), calls = 0;
  const grad = {addColorStop: (...a) => feed('stop', a)};
  const feed = (k, a) => { calls++; hash.update(k + ':' + a.map(v => typeof v === 'number' ? (Number.isFinite(v) ? v.toFixed(3) : 'NaN') : typeof v === 'object' ? 'obj' : String(v)).join(',') + ';'); };
  const ctx = new Proxy({}, {
    get(o, k) {
      if (k === 'measureText') return s => ({width: String(s).length * 6});
      if (k === 'createLinearGradient' || k === 'createRadialGradient') return (...a) => { feed(k, a); return grad; };
      if (k in o) return o[k];
      return (...a) => { for (const v of a) if (typeof v === 'number' && !Number.isFinite(v)) throw new Error('non-finite argument to ' + String(k)); feed(String(k), a); };
    },
    set(o, k, v) { o[k] = v; feed('set' + String(k), [v]); return true; }
  });
  return {ctx, digest: () => hash.digest('hex'), calls: () => calls, reset() { hash = crypto.createHash('sha256'); calls = 0; }};
}
const R = recorder();
// Offscreen layer caches draw into an unhashed context: a cache rebuild must
// not change the on-screen call stream (that is what is being compared).
const offscreen = recorder();
L.sandbox.document.createElement = () => ({width: 0, height: 0, getContext: () => offscreen.ctx});
const paintHash = (plan, rec, t, w = 1280, h = 720) => { R.reset(); S.paint(R.ctx, w, h, plan, rec, t, {saved: true}); return R.digest(); };

const checks = [];
function test(name, fn) {
  try { checks.push({name, pass: true, detail: fn()}); console.log('PASS', name); }
  catch (e) { checks.push({name, pass: false, error: e.stack}); console.log('FAIL', name, e.message); }
}

const race = new E.Race(4);
while (!race.complete) race.tick();
const record = race.result(), recordJSON = JSON.stringify(record), rngState = race.rng.state;
const ordinary = S.direct(E.Ceremony.plan(record, 'single'));
const finalRecord = {...record, stage: 20}, final = S.direct(E.Ceremony.plan(finalRecord, 'tour'));
const m = S.metrics(1280, 720), mm = S.metrics(390, 460);
const award = b => b.kind !== 'complete';

test('Compact cinematic timing replaces the 20.8s awards', () => {
  const len = {winner: 10.5, yellow: 10.5, green: 10.5, polka: 10.5, white: 10.5, 'team-stage': 9, 'team-final': 9, 'gc-final': 16};
  for (const p of [ordinary, final]) {
    assert.equal(p.intro, 1.6); assert.equal(p.visualVersion, 26);
    let at = 1.6;
    for (const b of p.beats) { assert.equal(b.start, at); assert.equal(b.seconds, b.kind === 'complete' ? (p.final ? 4 : 3) : len[b.kind]); at += b.seconds; }
    assert.equal(p.duration, at + 1);
  }
  assert(ordinary.duration < 65 && final.duration < 80);
  return {ordinary: ordinary.duration, final: final.duration};
});

test('Awards are record-derived; jersey, bouquet and GC order are preserved', () => {
  assert.equal(ordinary.beats[0].kind, 'winner');
  assert.equal(ordinary.beats[0].ids[0], record.places.indexOf(1));
  for (const key of ['green', 'polka', 'white', 'yellow']) {
    const beat = ordinary.beats.find(b => b.kind === key); if (!beat) continue;
    assert.equal(beat.ids[0], record.season.leaders[key]);
    for (const at of [5.0, 8.0, 10.3]) { const s = S.scene(ordinary, beat.start + at, m); assert.equal(s.actors[0].id, beat.ids[0]); assert.equal(s.actors[0].jersey, key); assert.equal(s.prop.type, 'flowers'); assert.equal(s.prop.owner, 'rider'); }
  }
  assert.equal(final.beats.at(-2).kind, 'gc-final');
  assert.deepEqual(final.beats.at(-2).ids, E.Classification.gcOrder(record.season).slice(0, 3));
  assert(!final.beats.some(b => b.kind === 'yellow'));
  const b = final.beats.at(-2), poses = S.scene(final, b.start + 21, m).actors;
  assert(poses[1].x < poses[0].x && poses[0].x < poses[2].x);
  assert(poses[2].entryAt < poses[1].entryAt && poses[1].entryAt < poses[0].entryAt, 'enter 3 → 2 → 1');
  assert(poses[0].entryStart > poses[1].entryStart); assert.equal(poses[0].jersey, 'yellow');
  for (let i = 1; i < poses.length; i++) assert.equal(poses[i].jersey, ['green', 'polka', 'white'].find(k => record.season.leaders[k] === poses[i].id) || null);
  const end = S.scene(final, final.beats.at(-1).start + .5, m);
  assert.equal(end.prop.type, 'trophy'); assert(end.actors[0].pose.lift > .99); assert(end.prop.twoHand);
  // Mid-award order on the stage: rank 3 is up before rank 2, rank 2 before the champion.
  const mid = S.scene(final, b.start + 2.4, m).actors;
  assert(mid[2].walking < .1 && mid[1].alpha > .99 && mid[0].alpha < .01, 'rank 3 placed while the champion has not yet appeared');
  return {order: poses.map(p => ({id: p.id, entry: p.entryAt, x: p.x}))};
});

test('Hand-off: presenter and awardee hold the very same grip during the shared hold', () => {
  let samples = 0;
  for (const [plan, met] of [[ordinary, m], [final, m], [ordinary, mm]]) for (const b of plan.beats.filter(award)) {
    const cue = S.cue(b); if (!(cue.share < cue.release)) continue;
    for (let a = cue.share + .02; a < cue.release; a += .1) {
      const s = S.scene(plan, b.start + a, met); if (!s.prop?.shared) continue;
      const focus = s.actors[0], sc = focus.height / 180, st = s.staff, ss = st.height / 180;
      const rider = [focus.x + focus.handTargets[1][0] * sc, focus.y + focus.handTargets[1][1] * sc];
      const staff = [st.x + st.handTargets[0][0] * ss, st.y + st.handTargets[0][1] * ss];
      assert(Math.hypot(rider[0] - staff[0], rider[1] - staff[1]) < .01, 'shared grip at ' + b.kind + ' +' + a.toFixed(2));
      samples++;
    }
  }
  assert(samples > 20);
  return {samples};
});

test('Props are painted at the solved hand, never floating away from it', () => {
  let n = 0;
  for (const b of ordinary.beats.filter(award)) for (const a of [3.2, 4.0, 5.2, 6.5, 8.5, 10.0]) {
    paintHash(ordinary, record, b.start + a); const s = S.lastScene, item = s.prop; if (!item?.drawnAnchor) continue;
    const r = item.owner === 'rider' ? s.results[item.id] : s.staffResult, h = item.owner === 'rider' ? r.right : r.left;
    assert(Math.hypot(item.drawnAnchor[0] - h[0], item.drawnAnchor[1] - h[1]) < 1e-9); n++;
  }
  const b = final.beats.at(-2);
  for (const a of [6.6, 8.4, 11, 15]) { paintHash(final, finalRecord, b.start + a); const s = S.lastScene, r = s.results[s.prop.id];
    assert(s.prop.twoHand); const mid = [(r.left[0] + r.right[0]) / 2, (r.left[1] + r.right[1]) / 2 + (s.prop.handDrop ?? 20) * s.prop.scale];
    assert(Math.hypot(s.prop.drawnAnchor[0] - mid[0], s.prop.drawnAnchor[1] - mid[1]) < 1e-9); n++; }
  return {checked: n};
});

test('Standing feet stay on their surface (no penetration) during celebrations', () => {
  let n = 0;
  for (const [plan, rec] of [[ordinary, record], [final, finalRecord]]) for (let t = 0; t < plan.duration; t += .37) {
    paintHash(plan, rec, t); const s = S.lastScene; if (!s?.results) continue;
    for (const a of s.actors) { const r = s.results[a.id]; if (!r || a.walking > 0 || (a.jump || 0) > 0) continue;
      for (const f of r.feet) { assert(f[1] <= a.feet[0].surface + .01, 'foot below surface ' + a.id + ' t=' + t.toFixed(2)); n++; } }
  }
  return {feet: n};
});

test('Camera is one continuous track: no resets between awards', () => {
  for (const [plan, met] of [[ordinary, m], [final, m], [ordinary, mm]]) {
    let prev = S.camera(plan, 0, met), worst = {x: 0, y: 0, z: 0};
    for (let t = .01; t < plan.duration; t += .01) {
      const c = S.camera(plan, t, met);
      for (const k of ['x', 'y', 'z']) worst[k] = Math.max(worst[k], Math.abs(c[k] - prev[k]));
      prev = c;
    }
    // At 100 Hz sampling: under 3.5 world units and 0.02 zoom per step.
    assert(worst.x < 3.5 && worst.y < 3.5 && worst.z < .02, JSON.stringify(worst));
    const zooms = plan.beats.filter(award).map(b => S.camera(plan, b.start + (b.kind === 'gc-final' ? 8.6 : 5.2), met).z);
    if (!met.mobile) assert(Math.max(...zooms) >= 1.4, 'hero push-in reaches z≈1.45');
  }
  return {pass: true};
});

test('Whip-pan replaces the black dip at every award boundary', () => {
  const html = fs.readFileSync(file, 'utf8');
  assert(!/rgba\(13,35,27,\$\{dip\}\)/.test(html), 'old 96% dip is gone');
  for (const b of ordinary.beats.slice(1).filter(award)) {
    const w = S.whip(ordinary, b.start, m); assert(w && w.u > .4 && w.u < .6, 'cut is mid-wipe');
    assert(!S.whip(ordinary, b.start + 1, m));
  }
  return {boundaries: ordinary.beats.slice(1).filter(award).length};
});

test('Same time ⇒ same scene and same paint, regardless of seek order or cache', () => {
  const times = [], hashes = new Map();
  for (const p of [ordinary, final]) for (let t = 0; t < p.duration; t += 2.9) times.push([p, t]);
  const json = (p, t) => JSON.stringify(S.scene(p, t, m), (k, v) => typeof v === 'number' ? +v.toFixed(6) : v);
  const pick = ([p, t]) => p === final ? finalRecord : record;
  for (const x of times) hashes.set(x, [json(...x), paintHash(x[0], pick(x), x[1])]);
  const order = times.slice().reverse().concat(times.filter((_, i) => i % 3 === 1));
  S.cache = null;
  for (const x of order) { const [j, h] = hashes.get(x); assert.equal(json(...x), j); assert.equal(paintHash(x[0], pick(x), x[1]), h, 'paint hash at ' + x[1].toFixed(2)); }
  return {frames: times.length, repeats: order.length};
});

test('Particles are analytic, capped and never use Math.random or Race.rng', () => {
  const html = fs.readFileSync(file, 'utf8'), start = html.indexOf('const CeremonyStage={'), end = html.indexOf('const Ceremony={');
  const src = html.slice(start, end).replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
  assert(!/Math\.random|\.rng\b|Race\.|\.tick\(/.test(src), 'presentation code has no randomness or simulation calls');
  let peak = 0;
  for (const [p, met] of [[ordinary, m], [final, m]]) { const list = S.burstList(p, met); for (let t = 0; t < p.duration; t += .05) { const live = list.filter(q => t >= q.at && t - q.at <= q.life).length; peak = Math.max(peak, live); } }
  assert(peak <= 220, 'live confetti ' + peak);
  return {peakLiveConfetti: peak};
});

test('Ceremony is a read-only consumer of the frozen record', () => {
  for (const [p, rec] of [[ordinary, record], [final, finalRecord]]) for (let t = 0; t < p.duration; t += .5) paintHash(p, rec, t);
  assert.equal(JSON.stringify(record), recordJSON); assert.equal(race.rng.state, rngState);
  assert(Object.isFrozen(ordinary) && Object.isFrozen(ordinary.beats[0]));
  return {pass: true};
});

test('Turned faces keep both eyes in 3/4 and move the mouth toward the facing side', () => {
  const R = S.rig.head, f1 = S.faceLayout(1, 1);
  assert(Math.abs(f1.eyes[0].x + f1.eyes[1].x) < 1e-9 && Math.abs(f1.mouth.x) < 1e-9, 'front view is symmetric');
  for (const dir of [1, -1]) {
    const q = S.faceLayout(.5, dir);
    assert(q.eyes.every(e => e.alpha > .95), '3/4 view shows both eyes');
    assert(Math.sign(q.mouth.x) === dir && Math.abs(q.mouth.x) > .3 * R, 'mouth follows the turn');
    assert(q.eyes.every(e => Math.sign(e.x - f1.eyes[e.side > 0 ? 1 : 0].x) === dir), 'eyes rotate with the head');
    const side = S.faceLayout(0, dir);
    assert(side.ears.find(e => e.side === dir).depth < 0, 'far ear is behind the head in profile');
    assert(side.eyes.filter(e => e.alpha > .5).length === 1, 'profile shows one eye');
  }
  return {R, threeQuarterMouth: S.faceLayout(.5, 1).mouth.x};
});

test('Running is a 3/4 view and the turn to camera is continuous', () => {
  let worst = 0, runFronts = [];
  for (const plan of [ordinary, final]) {
    let prev = new Map();
    for (let t = 0; t < plan.duration; t += .01) {
      const s = S.scene(plan, t, m), bi = plan.beats.indexOf(s.beat), now = new Map();
      for (const a of s.actors) { if (a.alpha < .5) continue; now.set(bi + ':' + a.id, [a.front, a.headFront]); if (a.walking > .99) runFronts.push(a.front); }
      for (const [k, v] of now) { const q = prev.get(k); if (q) worst = Math.max(worst, Math.abs(v[0] - q[0]), Math.abs(v[1] - q[1])); }
      prev = now;
    }
  }
  assert(worst < .05, 'front/headFront step ' + worst);
  assert(runFronts.length && runFronts.every(f => f >= .4 && f <= .6), '3/4 run');
  return {maxStepPer10ms: +worst.toFixed(4), runSamples: runFronts.length};
});

test('Hands never snap between poses (relative to the body, 50 Hz)', () => {
  const limit = 9, worst = {d: 0};
  for (const [plan, rec] of [[ordinary, record], [final, finalRecord]]) {
    const whip = t => plan.beats.some((b, i) => i && Math.abs(t - b.start) < .4);
    let prev = new Map();
    for (let t = 0; t < plan.duration; t += .02) {
      paintHash(plan, rec, t); const s = S.lastScene, now = new Map();
      if (s?.results) {
        const bi = plan.beats.indexOf(s.beat), rel = (r, a) => ({left: [r.left[0] - a.x, r.left[1] - a.y], right: [r.right[0] - a.x, r.right[1] - a.y]});
        for (const a of s.actors) { const r = s.results[a.id]; if (r && a.alpha > .5 && !(a.walking > 0)) now.set(bi + ':' + a.id, rel(r, a)); }
        if (s.staffResult) now.set(bi + ':staff', rel(s.staffResult, s.staff));
        if (!whip(t)) for (const [k, v] of now) { const q = prev.get(k); if (!q) continue;
          for (const h of ['left', 'right']) { const d = Math.hypot(v[h][0] - q[h][0], v[h][1] - q[h][1]); if (d > worst.d) Object.assign(worst, {d, t: +t.toFixed(2), k, h}); } }
      }
      prev = now;
    }
  }
  assert(worst.d < limit, 'hand jump ' + JSON.stringify(worst));
  return {maxWorldUnitsPer20ms: +worst.d.toFixed(2), at: worst};
});

const failed = checks.filter(c => !c.pass).length;
const report = {source: file, sha256: crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'), checks, passed: checks.length - failed, failed, pass: !failed};
if (out) fs.writeFileSync(out, JSON.stringify(report, null, 2));
console.log(`${checks.length - failed}/${checks.length} ${failed ? 'FAIL' : 'PASS'}`);
process.exitCode = failed ? 1 : 0;
