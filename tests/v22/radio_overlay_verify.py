#!/usr/bin/env python3
"""Targeted browser regression for the compact canvas radio and detailed lower panel."""
from __future__ import annotations
import argparse, asyncio, hashlib, json
from pathlib import Path
from playwright.async_api import async_playwright

STORAGE="""()=>{const d=new Map();Object.defineProperty(window,'localStorage',{value:{getItem:k=>d.has(String(k))?d.get(String(k)):null,setItem:(k,v)=>d.set(String(k),String(v)),removeItem:k=>d.delete(String(k)),clear:()=>d.clear(),key:i=>[...d.keys()][i]??null,get length(){return d.size}},configurable:true})}"""
EVENT="""()=>{App.testingFreeze=true;const r=App.race;r.paused=false;const serial=r.eventSerial+1000;r.events=[{serial,t:r.t,kind:'team-radio',priority:3,riderId:r.player.id,text:'前方进攻组仍有间隙，注意左侧横风。'}];r.eventSerial=serial;updateRaceRadioV17(r,performance.now());return{serial,t:r.t}}"""
CHECK="""()=>{const e=document.querySelector('#raceRadioV17'),wrap=document.querySelector('.canvas-wrap'),c=document.querySelector('#raceCanvas').getBoundingClientRect(),b=e.getBoundingClientRect(),v=V20RadioView.get(e),lower=document.querySelector('.team-radio-panel'),notice=document.querySelector('#raceNotice'),s=getComputedStyle(e),opacity=radioLabelOpacityV20(App.race,{x:v.bounds.x+1,y:v.bounds.y+1,w:3,h:3});return{parentIsCanvas:e.parentElement===wrap,position:s.position,visible:e.classList.contains('visible')&&!e.hidden&&e.getAttribute('aria-hidden')==='false',popupText:document.querySelector('#raceRadioText').textContent,centered:Math.abs((b.left+b.right)/2-(c.left+c.right)/2)<2,insideCanvas:b.top>=c.top&&b.bottom<=c.bottom&&b.left>=c.left&&b.right<=c.right,lowerPanelPresent:!!lower&&lower.isConnected,lowerPanelHasText:!!notice.textContent.trim(),independentMessages:!!notice.textContent.trim()&&document.querySelector('#raceRadioText').textContent.trim()!==notice.textContent.trim(),lowerText:notice.textContent.trim(),labelFades:opacity<1,overflow:document.documentElement.scrollWidth-innerWidth}}"""

async def main(args):
    args.out.mkdir(parents=True,exist_ok=True)
    report={'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'mode':'exact HTML injection with test-only in-memory storage','checks':{},'errors':[],'console':[],'screenshots':[]}
    def check(name,data):
        report['checks'][name]=data
        if data.get('pass') is False: raise AssertionError(name+': '+json.dumps(data,ensure_ascii=False))
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True,args=['--no-sandbox'])
        report['browser']={'name':'Chromium','version':browser.version}
        for width,height,reduced,label in [(1440,1000,False,'desktop'),(390,844,True,'mobile-reduced')]:
            ctx=await browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,reduced_motion='reduce' if reduced else 'no-preference')
            page=await ctx.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));page.on('console',lambda m:report['console'].append({'type':m.type,'text':m.text}) if m.type in ('error','warning') else None)
            await page.goto('about:blank?radio-test');await page.evaluate(STORAGE)
            await page.set_content(args.source.read_text(encoding='utf-8'),wait_until='load')
            await page.locator('#chooseStage').click();await page.locator('button[data-stage="4"]').click();await page.locator('#startRace').click()
            await page.wait_for_function('App.race !== null && App.screen === "race"')
            start=await page.evaluate(EVENT)
            await page.wait_for_function("document.querySelector('#raceRadioV17').classList.contains('visible')",timeout=5000)
            await page.wait_for_timeout(400)
            rendered=await page.evaluate(CHECK)
            rendered['pass']=rendered['parentIsCanvas'] and rendered['position']=='absolute' and rendered['visible'] and bool(rendered['popupText'].strip()) and rendered['centered'] and rendered['insideCanvas'] and rendered['lowerPanelPresent'] and rendered['lowerPanelHasText'] and rendered['independentMessages'] and rendered['labelFades'] and rendered['overflow']<=1
            check(label+'_render',{'viewport':[width,height],'event':start,**rendered})
            check(label+'_reduced_motion',await page.evaluate("()=>({requested:matchMedia('(prefers-reduced-motion: reduce)').matches,transition:getComputedStyle(document.querySelector('#raceRadioV17')).transitionDuration,pass:reducedMotion===matchMedia('(prefers-reduced-motion: reduce)').matches})"))
            shot=args.out/(label+'.png');await page.screenshot(path=str(shot));report['screenshots'].append(shot.name)
            if label=='desktop':
                lower_shot=args.out/'lower-panel-desktop.png';await page.locator('.team-radio-panel').screenshot(path=str(lower_shot));report['screenshots'].append(lower_shot.name)
            paused=await page.evaluate("""()=>{const r=App.race,e=document.querySelector('#raceRadioV17'),v=V20RadioView.get(e);r.paused=true;const clock=v.clock;updateRaceRadioV17(r,performance.now()+5000);return{paused:r.paused,clockBefore:clock,clockAfter:v.clock,stillVisible:e.classList.contains('visible')&&e.getAttribute('aria-hidden')==='false',pass:v.clock===clock&&e.classList.contains('visible')&&e.getAttribute('aria-hidden')==='false'}}""")
            check(label+'_pause',paused)
            hidden=await page.evaluate("""()=>{const r=App.race,e=document.querySelector('#raceRadioV17'),v=V20RadioView.get(e);r.paused=false;let t=performance.now()+6000;v.lastWall=t;v.until=v.clock+1;updateRaceRadioV17(r,t+20);updateRaceRadioV17(r,t+300);return{active:e.classList.contains('is-active'),visible:e.classList.contains('visible'),ariaHidden:e.getAttribute('aria-hidden'),pass:!e.classList.contains('is-active')&&e.getAttribute('aria-hidden')==='true'}}""")
            check(label+'_dismiss',hidden)
            await ctx.close()
        await browser.close()
    report['pass']=not report['errors'] and not any(c['type']=='error' for c in report['console']) and all(v.get('pass',False) for v in report['checks'].values())
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'radio-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not report['pass']:raise SystemExit(1)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);asyncio.run(main(ap.parse_args()))