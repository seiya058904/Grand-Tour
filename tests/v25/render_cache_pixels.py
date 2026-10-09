"""Actual Chromium pixels versus a mixed old-cache-function reference.

The rest of V25 is identical; delayed-readback stress also checks canvas reuse.
"""
import argparse
import asyncio
import base64
import hashlib
import io
import json
from pathlib import Path
import tempfile
from render_cache_source import ROOT, build_sources, sha
from PIL import Image, ImageChops
from playwright.async_api import async_playwright
from render_cache_probe import INSTALL

SETUP = """window.pixelClock=1000;window.requestAnimationFrame=()=>0;Object.defineProperty(performance,'now',{value:()=>window.pixelClock});"""
FRAME = r"""()=>{
 const r=App.race;r.paused=false;r.tick();r.tick();r.paused=true;viewFor(r).alpha=1;pixelClock+=100;
 const before=JSON.stringify(r.snapshot());drawRace();
 return {png:document.getElementById('raceCanvas').toDataURL(),pure:before===JSON.stringify(r.snapshot()),t:r.t,drawn:viewFor(r).drawn.length,full:!RenderBudget.low()};
}"""
STRESS = r"""poison=>{
 RiderBodySprites.clear();cacheAudit.start();
 const output=document.createElement('canvas');output.width=2048;output.height=960;const c=output.getContext('2d');c.fillStyle='#52705b';c.fillRect(0,0,output.width,output.height);
 for(let i=0;i<320;i++){
  if(i===256&&poison)for(const tile of RiderBodySprites.values()){
   const g=tile.getContext('2d');g.save();g.setTransform(1.7,.3,.2,.8,47,13);g.globalAlpha=.17;g.globalCompositeOperation='destination-out';g.setLineDash([3,7]);g.lineDashOffset=4;g.shadowColor='#f00';g.shadowBlur=9;g.shadowOffsetX=7;g.filter='blur(2px)';g.beginPath();g.rect(0,0,1,1);g.clip();
  }
  const phase=Math.floor(i/12)%24*Math.PI*2/24+.001,color=i<288?'#eeeeea':'#3ea4d7';
  c.save();c.translate(32+(i%32)*64,78+Math.floor(i/32)*96);
  cachedCyclistBody(c,color,phase,false,false,null,{lod:true,identity:i%12,stand:0,tuck:0,signal:0,coast:0,sprint:0,climb:0,fatigueDrop:0});c.restore();
 }
 // All 320 copies are submitted before the first readback. The 64 recycled
 // source canvases must preserve pixels already copied at earlier positions.
 const counts=cacheAudit.stop();return {png:output.toDataURL(),counts,cacheSize:RiderBodySprites.size};
}"""

def raw_png(value):
    return base64.b64decode(value.split(',',1)[1])

def compare(a,b):
    x,y=Image.open(io.BytesIO(a)).convert('RGBA'),Image.open(io.BytesIO(b)).convert('RGBA')
    if x.size!=y.size:return {'pass':False,'sizeA':x.size,'sizeB':y.size}
    same=x.tobytes()==y.tobytes()
    return {'pass':same,'size':x.size,'pixelSHA256':hashlib.sha256(x.tobytes()).hexdigest(),
            'differentBounds':None if same else ImageChops.difference(x,y).getbbox()}

async def run(args, sources, provenance):
    args.out.mkdir(parents=True,exist_ok=True)
    report={'protocol':'Identical actual production painters in isolated Chromium contexts; manual natural ticks + fixed presentation clock, full quality; no performance conclusions. Separate >256-key single-task delayed-readback stress and poisoned evicted-context state.',
            'provenance':provenance,'sources':{k:{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in sources.items()},'checks':[],'errors':[],
            'snapshots':{scene:sha(args.scenes/(scene+'-snapshot.json')) for scene in ['peloton','climb']}}
    reference={}
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True)
        report['browser']=browser.version
        for version,src in sources.items():
            context=await browser.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1)
            await context.set_offline(True)
            await context.add_init_script(SETUP)
            page=await context.new_page()
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            await page.goto(src.as_uri())
            await page.evaluate('document.fonts.ready')
            await page.evaluate(INSTALL)
            for scene in ['peloton','climb']:
                snap=json.loads((args.scenes/(scene+'-snapshot.json')).read_text())
                await page.evaluate("s=>{pixelClock=1000;App.testingFreeze=true;App.blockStoreWrite=true;Store.settings.quality='full';RiderBodySprites.clear();initializeRace(Race.restore(SaveCodec.compactSnapshot(s)));App.race.paused=true;viewFor(App.race).alpha=1;cacheAudit.start();}",snap)
                for i in range(48):
                    sample=await page.evaluate(FRAME)
                    png=raw_png(sample.pop('png'));key=f'{scene}-{i}'
                    if version=='reference':reference[key]=(png,sample)
                    else:
                        expected,meta=reference.pop(key)
                        result=compare(expected,png)
                        result.update(name=key,scene=scene,frame=i,pure=sample['pure'] and meta['pure'],full=sample['full'] and meta['full'],sameT=sample['t']==meta['t'],sameDrawn=sample['drawn']==meta['drawn'],drawn=sample['drawn'])
                        result['pass']=result['pass'] and result['pure'] and result['full'] and result['sameT'] and result['sameDrawn']
                        report['checks'].append(result)
                        if not result['pass']:
                            (args.out/(key+'-reference.png')).write_bytes(expected)
                            (args.out/(key+'-candidate.png')).write_bytes(png)
                counts=await page.evaluate('cacheAudit.stop()')
                report.setdefault('naturalCounts',[]).append({'version':version,'scene':scene,**counts})
                print(version,scene,json.dumps(counts),flush=True)
            for poison in [False,True]:
                sample=await page.evaluate(STRESS,poison);png=raw_png(sample.pop('png'));key='same-task-recycle'+('-poison' if poison else '')
                if version=='reference':reference[key]=(png,sample)
                else:
                    expected,meta=reference.pop(key)
                    result=compare(expected,png)
                    result.update(name=key,baselineCounts=meta['counts'],candidateCounts=sample['counts'],cacheSize=sample['cacheSize'])
                    result['pass']=result['pass'] and sample['cacheSize']==256 and sample['counts']['requests']==320 and sample['counts']['misses']==320 and sample['counts']['newBodyCanvases']==256 and meta['counts']['newBodyCanvases']==320
                    report['checks'].append(result)
                    if not result['pass']:
                        (args.out/(key+'-reference.png')).write_bytes(expected)
                        (args.out/(key+'-candidate.png')).write_bytes(png)
                    print(key,result['pass'],flush=True)
            await context.close()
        await browser.close()
    report['sourceUnchanged']=(all(sha(p)==report['sources'][k]['sha256'] for k,p in sources.items())
                               and sha(args.reference)==provenance['referenceSHA256'])
    parity_keys=['requests','hits','misses','evictions','bodyPaints','directPaints','maxSize','finalSize']
    report['naturalCountParity']=all(
        all(next(x for x in report['naturalCounts'] if x['scene']==scene and x['version']=='reference')[key]
            == next(x for x in report['naturalCounts'] if x['scene']==scene and x['version']=='candidate')[key]
            for key in parity_keys)
        for scene in ['peloton','climb'])
    report['passed']=sum(c['pass'] for c in report['checks']);report['failed']=len(report['checks'])-report['passed'];report['skipped']=0
    report['pass']=not report['failed'] and not report['errors'] and report['sourceUnchanged'] and report['naturalCountParity'] and not reference
    (args.out/'pixel-parity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({k:report[k] for k in ['passed','failed','errors','sourceUnchanged','pass']}),flush=True)
    assert report['pass'], 'See pixel-parity.json and exact failure images'

async def main(args):
    with tempfile.TemporaryDirectory(prefix='grand-tour-cache-reference-') as folder:
        sources, provenance = build_sources(args.source, args.reference, folder)
        await run(args, sources, provenance)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'Grand-Tour-V25.html')
    p.add_argument('--reference',type=Path,default=ROOT/'Grand-Tour-V24.html')
    p.add_argument('--scenes',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    asyncio.run(main(p.parse_args()))
