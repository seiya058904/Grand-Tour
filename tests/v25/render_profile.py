#!/usr/bin/env python3
"""Diagnostic CPU/timeline profile for a natural full-quality dense scene.

Run separately from performance_probe.py. Profiling adds overhead; these
numbers identify work, not a comparable FPS benchmark or acceptance gate.
"""
import argparse
import asyncio
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]


async def main(args):
    args.out.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'Grand-Tour-V25.html'
    data = args.snapshot.read_bytes()
    report = {'sourceSHA256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'snapshotSHA256': hashlib.sha256(data).hexdigest(),
              'protocol': 'Diagnostic only: production file, compact restore, full, 1440x1000 DPR1, actual RAF; profiling adds overhead; no periodic storage writes',
              'errors': []}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        report['browser'] = browser.version
        browser_cdp = await browser.new_browser_cdp_session()
        try:
            system = await browser_cdp.send('SystemInfo.getInfo')
            report['gpu'] = system['gpu']
        except Exception as e:
            report['gpuQueryError'] = str(e)
        context = await browser.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
        await context.set_offline(True)
        page = await context.new_page()
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        await page.goto(source.as_uri())
        await page.evaluate("s=>{App.testingFreeze=true;App.blockStoreWrite=true;Store.settings.quality='full';initializeRace(Race.restore(SaveCodec.compactSnapshot(s)));App.testingFreeze=false}", json.loads(data))
        await page.wait_for_timeout(2000)
        session = await context.new_cdp_session(page)
        await session.send('Profiler.enable')
        trace, complete = [], asyncio.Event()
        session.on('Tracing.dataCollected', lambda e: trace.extend(e['value']))
        session.on('Tracing.tracingComplete', lambda _: complete.set())
        await session.send('Tracing.start', {'categories': 'devtools.timeline,blink,cc,disabled-by-default-devtools.timeline', 'transferMode': 'ReportEvents'})
        await session.send('Profiler.start')
        before = await page.evaluate('({t:App.race.t,wall:performance.now(),visible:viewFor(App.race).drawn.length})')
        await page.wait_for_timeout(round(args.seconds * 1000))
        report['state'] = await page.evaluate("({t:App.race.t,wall:performance.now(),visible:viewFor(App.race).drawn.length,full:!RenderBudget.low(),screen:App.screen,player:App.race.player.status})")
        profile = (await session.send('Profiler.stop'))['profile']
        await session.send('Tracing.end')
        await asyncio.wait_for(complete.wait(), 30)
        report['start'] = before
        nodes = {n['id']: n for n in profile['nodes']}
        self_us = defaultdict(int)
        for node, delta in zip(profile.get('samples', []), profile.get('timeDeltas', [])):
            frame = nodes[node]['callFrame']
            key = (frame.get('functionName', '(anonymous)'), frame.get('lineNumber', -1))
            self_us[key] += delta
        report['cpuSelfTop'] = [{'function': name, 'line': line + 1, 'ms': us / 1000}
                                for (name, line), us in sorted(self_us.items(), key=lambda x: -x[1])[:35]]
        categories = ['Paint', 'PrePaint', 'Layout', 'UpdateLayoutTree', 'RasterTask',
                      'FireAnimationFrame', 'FunctionCall', 'RunTask', 'MinorGC', 'MajorGC']
        durations, counts = defaultdict(float), defaultdict(int)
        for event in trace:
            name = event.get('name')
            if name in categories and event.get('ph') == 'X':
                counts[name] += 1
                durations[name] += event.get('dur', 0) / 1000
        report['timeline'] = {name: {'count': counts[name], 'sumDurationMs': round(durations[name], 3)} for name in categories}
        report['timelineCaution'] = 'Nested and cross-thread durations are not additive wall-time shares.'
        (args.out / 'cpu-profile.json').write_text(json.dumps(profile), encoding='utf-8')
        (args.out / 'trace.json').write_text(json.dumps({'traceEvents': trace}), encoding='utf-8')
        await context.close()
        await browser.close()
    (args.out / 'render-profile-summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'gpu': report.get('gpu', {}).get('auxAttributes', {}).get('glRenderer'),
                      'state': report['state'], 'cpuSelfTop': report['cpuSelfTop'][:15],
                      'timeline': report['timeline'], 'errors': report['errors']}, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=5)
    parser.add_argument('--out', type=Path, required=True)
    asyncio.run(main(parser.parse_args()))
