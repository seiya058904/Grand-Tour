#!/usr/bin/env python3
"""Capture a naturally reached mountain descent, with no rider-state fixture edits."""
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
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True);src=ROOT/'archive/v23/Grand-Tour-V23.html'
    report={'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'mode':'injected-memory-storage' if args.injected else 'native-file','errors':[]}
    async with async_playwright() as pw:
        exe=shutil.which('chromium');b=await pw.chromium.launch(**({'executable_path':exe} if exe else {}),headless=True,args=['--no-sandbox']);p=await b.new_page(viewport={'width':1440,'height':1000});p.on('pageerror',lambda e:report['errors'].append(str(e)))
        if args.injected:
            await p.goto('about:blank?test');await p.evaluate(STORAGE);await p.set_content(src.read_text(encoding='utf-8'),wait_until='load')
        else:await p.goto(src.as_uri()+'?test')
        await p.evaluate("App.testingFreeze=true;window.descRace=new Race(2,0,'single',null,2042383)")
        state=None
        for _ in range(15):
            state=await p.evaluate("""()=>{const r=descRace;for(let i=0;i<1000&&!r.complete;i++){r.tick();if(r.player.grade<-.06&&r.player.v>12)break;}return{grade:r.player.grade,speed:r.player.v,t:r.t,complete:r.complete}}""")
            if state['grade']<-.06 and state['speed']>12:break
        report['descent']=state
        assert state['grade']<-.06 and state['speed']>12
        report['pose']=await p.evaluate("""()=>{const r=descRace;initializeRace(r);App.testingFreeze=true;r.paused=true;viewFor(r).alpha=1;updateHud(true);drawRace();const v=viewFor(r).riders.get(0);return{power:r.player.power,tuck:v.tuck,coast:v.coast,stand:v.stand,pass:[v.tuck,v.coast,v.stand].every(Number.isFinite)&&v.tuck>0}}""")
        await p.wait_for_timeout(650);await p.screenshot(path=str(out/'mountain-descent.png'));report['pass']=report['pose']['pass'] and not report['errors'];await b.close()
    (out/'downhill-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2), encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    if not report['pass']:raise SystemExit(1)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--injected',action='store_true');ap.add_argument('--out',default='/tmp/grand-tour-v23-downhill');asyncio.run(main(ap.parse_args()))
