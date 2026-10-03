#!/usr/bin/env python3
"""Observe a physical late-race sprint through the real control and renderer."""
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
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    src=ROOT/'Grand-Tour-V24.html';report={'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'mode':'injected-memory-storage' if args.injected else 'native-file','errors':[]}
    async with async_playwright() as pw:
        exe=shutil.which('chromium');browser=await pw.chromium.launch(**({'executable_path':exe} if exe else {}),headless=True,args=['--no-sandbox'])
        p=await browser.new_page(viewport={'width':1440,'height':1000});p.on('pageerror',lambda e:report['errors'].append(str(e)))
        if args.injected:
            await p.goto('about:blank?test');await p.evaluate(STORAGE);await p.set_content(src.read_text(encoding='utf-8'),wait_until='load')
        else:await p.goto(src.as_uri()+'?test')
        await p.evaluate("App.testingFreeze=true;window.finishRace=new Race(4,0,'single',null,2058765)")
        for _ in range(12):
            data=await p.evaluate("""()=>{const r=finishRace;for(let i=0;i<1000&&r.stage.length-r.player.x>120&&isRacing(r.player);i++)r.tick();return{left:r.stage.length-r.player.x,t:r.t}}""")
            if data['left']<=120:break
        assert 0<data['left']<=120
        await p.evaluate('initializeRace(finishRace);App.testingFreeze=true;updateHud(true);drawRace()');await p.locator('#attackButton').click()
        for name,left in [('finish-sprint.png',25),('finish-lunge.png',1.5)]:
            report[name]=await p.evaluate("""left=>{const r=App.race,v=viewFor(r);for(let i=0;i<300&&r.stage.length-r.player.x>left&&isRacing(r.player);i++){r.tick();v.update(r.t,984,398);}r.paused=true;v.alpha=1;updateHud(true);drawRace();const p=r.player;return{t:r.t,actualLeft:r.stage.length-p.x,power:p.power,speed:p.v,stand:v.riders.get(0).stand,sprint:p.attackKind,lens:v.lens};}""",left)
            await p.evaluate('window.scrollTo(0,0)');await p.wait_for_timeout(650);await p.screenshot(path=str(out/name))
        report['finished_projection']=await p.evaluate("""()=>{const r=App.race;for(let i=0;i<1500&&!r.complete;i++)r.tick();const before=JSON.stringify(r.snapshot()),v=viewFor(r);v.update(r.t,984,398);const terminal=r.riders.filter(p=>p.status==='FINISHED');const error=Math.max(...terminal.map(p=>Math.abs(v.riders.get(p.id).world-p.x)));return{pass:error===0&&before===JSON.stringify(r.snapshot()),finished:terminal.length,maxWorldError:error,complete:r.complete}}""")
        report['terminal_retirement']=await p.evaluate("""()=>{const r=App.race,v=viewFor(r);v.update(r.t+1,984,398);drawRace();const old=r.riders.filter(p=>p.status==='FINISHED'&&v.time-p.finishedTime>=.45);const oldDrawn=v.drawn.filter(o=>old.some(p=>p.id===o.r.id));return{pass:old.length===184&&oldDrawn.length===0,finishedRetired:old.length,finishedDrawn:oldDrawn.length,retainedActualState:v.riders.size}}""")
        await p.evaluate('initializeRace(finishRace);App.testingFreeze=true')
        await p.wait_for_timeout(1600)
        await p.locator('#ceremonyChapters button[data-beat="0"]').click()
        await p.locator('#ceremonySpeed').select_option('2')
        await p.wait_for_timeout(6500)
        await p.locator('#ceremonyPause').click()
        report['ceremony_winner']=await p.evaluate("""()=>{const f=App.finishFlow;return{pass:f?.phase==='ceremony'&&f.elapsed>8&&f.paused&&f.settleCount===1,elapsed:f.elapsed,settled:f.settleCount,phase:f.phase,plan:f.plan.beats.map(b=>({kind:b.kind,start:b.start,end:b.end}))}}""")
        await p.screenshot(path=str(out/'ceremony-winner.png'))
        await p.locator('#ceremonySkip').click()
        report['pass']=not report['errors'] and report['finished_projection']['pass'] and report['terminal_retirement']['pass'] and report['ceremony_winner']['pass']
        await browser.close()
    (out/'finish-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2), encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    if not report['pass']:raise SystemExit(1)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--injected',action='store_true');parser.add_argument('--out',default='/tmp/grand-tour-v23-finish');asyncio.run(main(parser.parse_args()))
