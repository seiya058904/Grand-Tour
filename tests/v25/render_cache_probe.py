"""Isolated cache counters against a mixed old-function reference.

Sequential real-RAF runs are instrumented diagnostics, not the release benchmark.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import tempfile
from render_cache_source import ROOT, build_sources, sha
from playwright.async_api import async_playwright

INSTALL = r"""()=>{
 const original=cachedCyclistBody,paint=paintCyclistBody,create=document.createElement;
 const get=RiderBodySprites.get,put=RiderBodySprites.set,drop=RiderBodySprites.delete;
 let depth=0,hit=false;
 window.cacheAudit={active:false,stats:{},start(){this.stats={requests:0,hits:0,misses:0,evictions:0,newBodyCanvases:0,bodyPaints:0,directPaints:0,maxSize:RiderBodySprites.size};this.active=true;},stop(){this.active=false;return {...this.stats,finalSize:RiderBodySprites.size};}};
 cachedCyclistBody=function(...args){depth++;try{return original.apply(this,args);}finally{depth--;}};
 RiderBodySprites.get=function(key){const value=get.call(this,key);if(depth&&cacheAudit.active){hit=!!value;cacheAudit.stats.requests++;cacheAudit.stats[hit?'hits':'misses']++;}return value;};
 RiderBodySprites.set=function(key,value){const result=put.call(this,key,value);if(cacheAudit.active)cacheAudit.stats.maxSize=Math.max(cacheAudit.stats.maxSize,this.size);return result;};
 RiderBodySprites.delete=function(key){if(depth&&cacheAudit.active&&!hit&&this.size>=256)cacheAudit.stats.evictions++;return drop.call(this,key);};
 document.createElement=function(name,...args){if(depth&&cacheAudit.active&&String(name).toLowerCase()==='canvas')cacheAudit.stats.newBodyCanvases++;return create.call(this,name,...args);};
 paintCyclistBody=function(...args){if(cacheAudit.active)cacheAudit.stats[depth?'bodyPaints':'directPaints']++;return paint.apply(this,args);};
}"""
READ = r"""()=>{
 const stats=a=>{const b=a.slice().sort((x,y)=>x-y);return {n:b.length,mean:b.reduce((a,b)=>a+b,0)/Math.max(1,b.length),p50:b[Math.floor((b.length-1)*.5)]||0,p95:b[Math.floor((b.length-1)*.95)]||0,p99:b[Math.floor((b.length-1)*.99)]||0,max:b.at(-1)||0};};
 const elapsed=(performance.now()-Perf.startWall)/1000,summary=Perf.summary(),counts=cacheAudit.stop(),frames=stats(Perf.frames);
 Perf.enabled=false;App.testingFreeze=true;App.race.paused=true;
 return {...summary,frames,cpu:stats(Perf.cpu),fps:1000/frames.mean,elapsed,counts,missRate:counts.requests?counts.misses/counts.requests:0,newCanvasesPerSecond:counts.newBodyCanvases/elapsed,missesPerSecond:counts.misses/elapsed,full:Store.settings.quality==='full'&&!RenderBudget.low(),finite:App.race.riders.every(r=>[r.x,r.v,r.power,r.energy].every(Number.isFinite))};
}"""

async def run(args, sources, provenance):
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = {'protocol': 'Counter-instrumented sequential ABBA; 1440x1000 DPR1 full, natural compact restore, 2s warmup, real RAF, periodic storage disabled equally. No screenshots/readback/profiling during windows.',
              'provenance': provenance, 'sources': {k: {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in sources.items()}, 'runs': []}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        report['browser'] = browser.version
        for scene in args.scenes_list.split(','):
            data = (args.scenes / (scene + '-snapshot.json')).read_bytes()
            for order, version in enumerate(args.order.split(',')):
                context = await browser.new_context(viewport={'width':1440,'height':1000}, device_scale_factor=1)
                await context.set_offline(True)
                page = await context.new_page()
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                await page.goto(sources[version].as_uri())
                await page.evaluate('document.fonts.ready')
                await page.evaluate(INSTALL)
                await page.evaluate("s=>{App.testingFreeze=true;App.blockStoreWrite=true;Store.settings.quality='full';RiderBodySprites.clear();initializeRace(Race.restore(SaveCodec.compactSnapshot(s)));App.testingFreeze=false;}", json.loads(data))
                await page.wait_for_timeout(2000)
                cdp = await context.new_cdp_session(page)
                await cdp.send('Performance.enable')
                await cdp.send('HeapProfiler.collectGarbage')
                before = {x['name']:x['value'] for x in (await cdp.send('Performance.getMetrics'))['metrics']}
                await page.wait_for_timeout(200)
                await page.evaluate('cacheAudit.start();Perf.start()')
                await page.wait_for_timeout(round(args.seconds*1000))
                result = await page.evaluate(READ)
                after = {x['name']:x['value'] for x in (await cdp.send('Performance.getMetrics'))['metrics']}
                await cdp.send('HeapProfiler.collectGarbage')
                retained = {x['name']:x['value'] for x in (await cdp.send('Performance.getMetrics'))['metrics']}
                result.update(scene=scene,version=version,order=order,errors=errors,snapshotSHA256=hashlib.sha256(data).hexdigest(),
                              metricDeltas={k:after.get(k,0)-before.get(k,0) for k in ['LayoutCount','RecalcStyleCount','LayoutDuration','RecalcStyleDuration','ScriptDuration','TaskDuration']},
                              before={k:before.get(k) for k in ['JSHeapUsedSize','Nodes','Documents','JSEventListeners']},rawAfter={k:after.get(k) for k in ['JSHeapUsedSize','Nodes','Documents','JSEventListeners']},retainedAfter={k:retained.get(k) for k in ['JSHeapUsedSize','Nodes','Documents','JSEventListeners']})
                report['runs'].append(result)
                args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2))
                print(json.dumps({k:result[k] for k in ['scene','version','fps','counts','missRate','newCanvasesPerSecond','cpu']},ensure_ascii=False),flush=True)
                await context.close()
        await browser.close()
    report['sourceUnchanged'] = (all(sha(p)==report['sources'][k]['sha256'] for k,p in sources.items())
                                 and sha(args.reference)==provenance['referenceSHA256'])
    report['pass'] = report['sourceUnchanged'] and all(not r['errors'] and r['full'] and r['finite'] and r['counts']['maxSize']<=256 and .9<=r['simPerWall']<=1.1 for r in report['runs'])
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    assert report['pass'], report

async def main(args):
    if args.seconds <= 0:
        raise ValueError('--seconds must be positive')
    if not all(name in {'reference', 'candidate'} for name in args.order.split(',')):
        raise ValueError('--order accepts reference and candidate only')
    with tempfile.TemporaryDirectory(prefix='grand-tour-cache-reference-') as folder:
        sources, provenance = build_sources(args.source, args.reference, folder)
        await run(args, sources, provenance)

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'Grand-Tour-V25.html')
    p.add_argument('--reference',type=Path,default=ROOT/'Grand-Tour-V24.html')
    p.add_argument('--scenes',type=Path,required=True)
    p.add_argument('--scenes-list',default='peloton,climb')
    p.add_argument('--order',default='reference,candidate,candidate,reference')
    p.add_argument('--seconds',type=float,default=6)
    p.add_argument('--out',type=Path,required=True)
    asyncio.run(main(p.parse_args()))
