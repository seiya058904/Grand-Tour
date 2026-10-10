'use strict';
// Extract the actual production scenery painter. A call recorder replaces only
// Canvas rasterization, so these tests can check world-space continuity in Node.
const fs = require('node:fs');

function sceneHarness(file) {
  const html = fs.readFileSync(file, 'utf8');
  const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
  const section = (from, until) => {
    const first = script.indexOf(from);
    const last = script.indexOf(until, first);
    if (first < 0 || last <= first) throw new Error('Missing production scenery section: ' + from);
    return script.slice(first, last);
  };
  const recorded = {buildings: [], trees: [], heads: []};
  const stack = [];
  const target = {globalAlpha: 1};
  const gradient = {addColorStop() {}};
  const ctx = new Proxy(target, {
    get(o, key) {
      if (key === 'save') return () => stack.push(o.globalAlpha);
      if (key === 'restore') return () => { o.globalAlpha = stack.pop() ?? 1; };
      if (key === 'createLinearGradient' || key === 'createRadialGradient') return () => gradient;
      return key in o ? o[key] : () => {};
    },
    set(o, key, value) { o[key] = value; return true; }
  });
  const tree = (c, x, y, size, kind, tone) => recorded.trees.push({
    key: `${kind}:${tone}:${size.toFixed(7)}`, x, y, size, opacity: c.globalAlpha
  });
  const head = (c, x, y, radius, color) => {
    if (color === '#c5a281') recorded.heads.push({x, y, radius, opacity: c.globalAlpha});
  };
  const code = [
    'const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));',
    'const lerp=(a,b,t)=>a+(b-a)*t;',
    section('function sceneNoise(', '/* V19 finish furniture'),
    section('function segmentAt(', 'const Physics='),
    section('const RaceLandscapeV24=', 'function drawScenery('),
    'return RaceLandscapeV24;'
  ].join('\n');
  const painter = new Function('SceneArt', 'RenderBudget', 'pathStroke', 'circle', 'reducedMotion', code)(
    {tree}, {low: () => false}, () => {}, head, false
  );
  painter.building = (c, x, y, width, height, key) => recorded.buildings.push({
    key: `${key}:${width.toFixed(7)}:${height.toFixed(7)}`, x, y, width, height, opacity: c.globalAlpha
  });
  function reset() {
    for (const key of Object.keys(recorded)) recorded[key] = [];
    stack.length = 0; target.globalAlpha = 1;
  }
  function backdrop(stage, motion, altitude, options = {}) {
    reset();
    const width = options.width || 1400, height = 460;
    const ground = x => 320 - (x - width * .4) * (options.slope || 0);
    painter.backdrop(ctx, width, height, stage, motion, options.weather || 'sun', altitude, ground, 120);
    return structuredClone(recorded);
  }
  function verge(stage, motion, options = {}) {
    reset();
    const width = options.width || 1400, height = 460, scale = options.scale || 18.5;
    painter.verge(ctx, width, height, stage, motion, width * .4, scale, () => 320, 120,
      ['#aaaaaa', '#aaaaaa', '#aaaaaa', '#aaaaaa', '#aaaaaa', '#aaaaaa', '#aaaaaa'], 'sun', 10);
    return structuredClone(recorded);
  }
  return {painter, backdrop, verge};
}

function interiorTransitions(previous, next, field, width = 1400, margin = 180) {
  const before = new Map(previous[field].map(x => [x.key, x]));
  const after = new Map(next[field].map(x => [x.key, x]));
  const interior = x => x.x > margin && x.x < width - margin && x.opacity > .99;
  return [
    ...[...before].filter(([key, x]) => !after.has(key) && interior(x)).map(([key, x]) => ({kind: 'disappeared', key, x: x.x})),
    ...[...after].filter(([key, x]) => !before.has(key) && interior(x)).map(([key, x]) => ({kind: 'appeared', key, x: x.x}))
  ];
}
module.exports = {sceneHarness, interiorTransitions};
