#!/usr/bin/env python3
"""Sequential V24/V25 ABBA with identical natural snapshots and full quality.

Run with no concurrent simulations or browser tests. This measures the actual
1x requestAnimationFrame path, never a reduced quality or frozen benchmark.
--soak-seconds adds one continuous real-time climb and retained-heap sampling.
"""
import argparse
import asyncio
import hashlib
import json
import platform
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]
INSTALL = r"""s=>{
 App.testingFreeze=true;App.blockStoreWrite=true;Store.settings.quality='full';
 initializeRace(Race.restore(SaveCodec.compactSnapshot(s)));App.testingFreeze=false;
 window.qaLongTasks=[];
 window.qaObserver=new PerformanceObserver(list=>{
  for(const e of list.getEntries())qaLongTasks.push({start:e.startTime,ms:e.duration});
 });qaObserver.observe({type:'longtask',buffered:false});
}"""
READ = r"""stop=>{
 const stat=a=>{const b=a.slice().sort((x,y)=>x-y),q=p=>b[Math.floor((b.length-1)*p)]||0;
  return {n:b.length,p50:q(.50),p95:q(.95),p99:q(.99),max:b.at(-1)||0,
   mean:b.length?b.reduce((n,x)=>n+x,0)/b.length:0,
   over33:a.filter(x=>x>33.34).length,over50:a.filter(x=>x>50).length};};
 const summary=Perf.summary(),r=App.race;
 const data={...summary,frames:stat(Perf.frames),cpu:stat(Perf.cpu),
  debt:stat(Perf.debts),quality:Store.settings.quality,effectiveLow:RenderBudget.low(),
  longTasks:qaLongTasks.filter(x=>x.start>=Perf.startWall),
  elapsedSim:r.t,riderStates:r.riders.length,
  finite:r.riders.every(x=>['x','v','power','energy'].every(k=>Number.isFinite(x[k]))),
  canvas:{width:$('raceCanvas').width,height:$('raceCanvas').height},
  screen:App.screen,finished:r.complete,
  running:App.screen==='race'&&!r.paused&&!App.testingFreeze&&!App.finishFlow&&
    !QuickFinish.running&&isRacing(r.player)};
 data.fps=data.frames.mean?1000/data.frames.mean:0;
 if(stop){Perf.enabled=false;App.testingFreeze=true;r.paused=true;}
 return data;
}"""


async def heap(cdp, collect=False):
    if collect:
        await cdp.send('HeapProfiler.collectGarbage')
    data = await cdp.send('Performance.getMetrics')
    return {x['name']: x['value'] for x in data['metrics']
            if x['name'] in ('JSHeapUsedSize', 'JSHeapTotalSize', 'Nodes',
                             'Documents', 'JSEventListeners')}


async def main(args):
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sources = {'V24': ROOT / 'Grand-Tour-V24.html', 'V25': ROOT / 'Grand-Tour-V25.html'}
    hashes = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in sources.items()}
    report = {'protocol': {
        'order': 'V24,V25,V25,V24 for each scene; sequential contexts in one browser',
        'viewport': [1440, 1000], 'DPR': 1, 'quality': 'full', 'speed': '1x real RAF',
        'warmupSeconds': 2, 'sampleSeconds': args.seconds,
        'heap': 'CDP JS heap; forced GC only outside ABBA measurement windows',
        'production': 'Native file URL without test mode; normal compact-save restore. Periodic storage writes blocked in both versions; storage I/O is covered separately.',
        'limitation': 'Linux headless Chromium on a shared host; not physical phone or hardware GPU results',
        'concurrency': 'Operator must stop all other test/benchmark processes before this command'},
        'platform': platform.platform(), 'hashes': hashes, 'runs': [], 'soak': []}

    def save():
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        report['browser'] = browser.version
        for scene in ['peloton', 'climb', 'leadout']:
            snapfile = args.scenes / (scene + '-snapshot.json')
            snapbytes = snapfile.read_bytes()
            snapshot = json.loads(snapbytes)
            snapshot_sha = hashlib.sha256(snapbytes).hexdigest()
            for order, version in enumerate(['V24', 'V25', 'V25', 'V24']):
                context = await browser.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
                await context.set_offline(True)
                page = await context.new_page()
                errors, requests = [], []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.on('request', lambda r: requests.append(r.url) if r.url.startswith(('http:', 'https:')) else None)
                await page.goto(sources[version].as_uri())
                await page.evaluate('document.fonts.ready')
                await page.evaluate(INSTALL, snapshot)
                await page.wait_for_timeout(2000)
                cdp = await context.new_cdp_session(page)
                await cdp.send('Performance.enable')
                before = await heap(cdp, True)
                await page.wait_for_timeout(200)
                await page.evaluate('Perf.start();qaLongTasks=[]')
                await page.wait_for_timeout(round(args.seconds * 1000))
                data = await page.evaluate(READ, True)
                raw_after, retained_after = await heap(cdp), await heap(cdp, True)
                data.update(version=version, scene=scene, order=order, sha256=hashes[version],
                            snapshotSHA256=snapshot_sha,
                            heapBefore=before, heapAfter=raw_after, heapRetainedAfter=retained_after,
                            errors=errors, externalRequests=requests)
                report['runs'].append(data)
                save()
                print(json.dumps({k: data[k] for k in ['version', 'scene', 'order', 'fps', 'frames', 'cpu', 'lastDebt', 'simPerWall']}, ensure_ascii=False), flush=True)
                await context.close()
        if args.soak_seconds:
            snapshot = json.loads((args.scenes / 'climb-snapshot.json').read_text(encoding='utf-8'))
            context = await browser.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
            await context.set_offline(True)
            page = await context.new_page()
            report['soakErrors'] = []
            page.on('pageerror', lambda e: report['soakErrors'].append(str(e)))
            await page.goto(sources['V25'].as_uri())
            await page.evaluate('document.fonts.ready')
            await page.evaluate(INSTALL, snapshot)
            await page.wait_for_timeout(2000)
            cdp = await context.new_cdp_session(page)
            await cdp.send('Performance.enable')
            report['soakHeapBefore'] = await heap(cdp, True)
            await page.wait_for_timeout(200)
            report['soakStartSim'] = await page.evaluate('App.race.t')
            await page.evaluate('window.qaSoakStartWall=performance.now()')
            elapsed = 0
            while elapsed < args.soak_seconds:
                segment = min(30, args.soak_seconds - elapsed)
                await page.evaluate('Perf.start();qaLongTasks=[]')
                await page.wait_for_timeout(round(segment * 1000))
                elapsed += segment
                data = await page.evaluate(READ, False)
                data.update(wallTarget=elapsed, heap=await heap(cdp))
                report['soak'].append(data)
                save()
                print('soak', elapsed, json.dumps({k: data[k] for k in ['fps', 'lastDebt', 'elapsedSim', 'caches', 'heap']}), flush=True)
            await page.evaluate(READ, True)
            report['soakElapsed'] = await page.evaluate('({wallSeconds:(performance.now()-qaSoakStartWall)/1000,simEnd:App.race.t})')
            report['soakHeapRetainedAfter'] = await heap(cdp, True)
            await context.close()
        await browser.close()
    report['sourceUnchanged'] = all(hashes[k] == hashlib.sha256(p.read_bytes()).hexdigest() for k, p in sources.items())
    report['pass'] = report['sourceUnchanged'] and all(
        not r['errors'] and not r['externalRequests'] and r['quality'] == 'full' and
        not r['effectiveLow'] and r['finite'] and r['lastDebt'] < .15 and r['frames']['n'] > 30
        and r['running'] and .9 <= r['simPerWall'] <= 1.1
        for r in report['runs']) and not report.get('soakErrors') and all(
        r['finite'] and r['quality'] == 'full' and not r['effectiveLow'] and
        r['lastDebt'] < .15 and r['caches']['bodies'] <= 256 and r['frames']['n'] > 30
        and r['running'] and .9 <= r['simPerWall'] <= 1.1 for r in report['soak'])
    if report['soak']:
        elapsed = report['soakElapsed']
        report['soakSimPerWall'] = (elapsed['simEnd'] - report['soakStartSim']) / elapsed['wallSeconds']
        report['pass'] = report['pass'] and .9 <= report['soakSimPerWall'] <= 1.1
    save()
    assert report['pass'], 'See complete report; quality, debt or runtime health failed.'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenes', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=8)
    parser.add_argument('--soak-seconds', type=int, default=180)
    asyncio.run(main(parser.parse_args()))
