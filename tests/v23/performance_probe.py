#!/usr/bin/env python3
"""Short, explicitly environment-specific live-frame probe, not a device FPS claim."""
from __future__ import annotations
import argparse, asyncio, hashlib, json, shutil
from pathlib import Path
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from playwright.async_api import async_playwright
from browser_verify import STORAGE
ROOT=Path(__file__).resolve().parents[2]
async def main(args):
    report={'protocol':'1440x1000, DPR 1, headless Chromium, full graphics, stage 5, seed 2058765, 40 s fixed-step warm-start, 1 s live warm-up, 5 s live sample. Order V22 then V23. Single run per version; local Windows machine, shared CPU; not a physical device or isolated laboratory benchmark.','runs':{}}
    async with async_playwright() as pw:
        exe=shutil.which('chromium')
        browser=await pw.chromium.launch(**({'executable_path':exe} if exe else {}),headless=True,args=['--no-sandbox'])
        report['browser']=browser.version
        for version in ['V22','V23']:
            src=ROOT/('Grand-Tour-'+version+'.html')
            ctx=await browser.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1)
            p=await ctx.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
            if args.injected:
                await p.goto('about:blank?test');await p.evaluate(STORAGE);await p.set_content(src.read_text(encoding='utf-8'),wait_until='load')
            else:await p.goto(src.as_uri()+'?test')
            await p.evaluate("""()=>{App.testingFreeze=true;Store.settings.quality='full';const r=new Race(4,0,'single',null,2058765);for(let i=0;i<800;i++)r.tick();initializeRace(r);App.testingFreeze=false;}""")
            await p.wait_for_timeout(1000);await p.evaluate('Perf.start()');await p.wait_for_timeout(5000)
            data=await p.evaluate('({...Perf.summary(),quality:Store.settings.quality,effectiveLow:RenderBudget.low()})');data['errors']=errors;data['sha256']=hashlib.sha256(src.read_bytes()).hexdigest()
            report['runs'][version]=data;print(version,json.dumps(data),flush=True)
            await ctx.close()
        await browser.close()
    Path(args.out).write_text(json.dumps(report,ensure_ascii=False,indent=2), encoding='utf-8')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--injected',action='store_true');parser.add_argument('--out',default='/tmp/grand-tour-v23-performance.json');asyncio.run(main(parser.parse_args()))
