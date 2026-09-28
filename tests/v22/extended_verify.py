#!/usr/bin/env python3
"""Additional real-engine, UI and cross-stage tests. No replacement simulation.
Run with --injected only where browser policy blocks file navigation. That mode
uses a test-only memory Storage implementation and cannot prove disk persistence.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, shutil
from pathlib import Path
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from playwright.async_api import async_playwright
from browser_verify import STORAGE
ROOT = Path(__file__).resolve().parents[2]

async def main(args):
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    source = ROOT/'Grand-Tour-V22.html'
    report = {'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'checks': {}, 'errors': [], 'mode': 'injected-memory-storage' if args.injected else 'native-file'}
    def record(name, result):
        report['checks'][name] = result
        print(name, json.dumps(result, ensure_ascii=False)[:1800], flush=True)
        if isinstance(result, dict) and result.get('pass') is False:
            raise AssertionError(name)
    async with async_playwright() as pw:
        exe = shutil.which('chromium')
        browser = await pw.chromium.launch(**({'executable_path': exe} if exe else {}), headless=True, args=['--no-sandbox'])
        async def load(name='Grand-Tour-V22.html', width=1440, height=1000):
            ctx = await browser.new_context(viewport={'width': width, 'height': height}, device_scale_factor=1)
            p = await ctx.new_page(); p.on('pageerror', lambda e: report['errors'].append(str(e)))
            if args.injected:
                await p.goto('about:blank?test'); await p.evaluate(STORAGE)
                await p.set_content((ROOT/name).read_text(encoding='utf-8'), wait_until='load')
            else:
                await p.goto((ROOT/name).as_uri()+'?test', wait_until='load')
            await p.evaluate('App.testingFreeze=true')
            return ctx, p
        ctx, p = await load()
        await p.evaluate("""()=>{const r=new Race(4,0,'single',null,2058765);for(let i=0;i<800;i++)r.tick();initializeRace(r);r.paused=false;updateHud(true);drawRace()}""")
        choice=p.locator('#wheelChoices [data-follow]').first
        target=int(await choice.get_attribute('data-follow'))
        await choice.click()
        record('designated_wheel_input',await p.evaluate("""id=>({pass:App.race.selectedWheel===id&&App.race.hold,selected:App.race.selectedWheel,hold:App.race.hold})""",target))
        record('designated_wheel_travel',await p.evaluate("""()=>{const r=App.race,a=[];for(let i=0;i<400;i++){r.tick();if(i%100===0)a.push({t:r.t,selected:r.selectedWheel,state:r.followState,x:r.player.x,power:r.player.power,draft:r.player.draft,front:r.player.frontId,energy:r.player.energy});}return{pass:a.every(s=>Number.isFinite(s.x+s.power)&&s.draft>=0&&s.draft<1),samples:a}}"""))
        await p.evaluate('updateHud(true)'); await p.locator('#autoWheelButton').click()
        record('return_to_auto',await p.evaluate('({pass:App.race.hold&&App.race.selectedWheel===-1,selected:App.race.selectedWheel})'))
        await p.locator('#attackButton').click();await p.wait_for_timeout(250)
        record('attack_hover_contrast',await p.evaluate("""()=>{const e=document.querySelector('#attackButton'),s=getComputedStyle(e);return{pass:e.classList.contains('attacking')&&s.color!==s.backgroundColor,color:s.color,background:s.backgroundColor}}"""))
        await p.evaluate('App.testingFreeze=false'); await p.wait_for_timeout(2000)
        await p.evaluate('App.testingFreeze=true;App.race.paused=true;updateHud(true);drawRace();window.scrollTo(0,0)')
        record('live_animation',await p.evaluate("""()=>{const v=viewFor(App.race).riders.get(0);return{pass:v.stand>.2&&App.race.player.power>Physics.sustainable(App.race.player),t:App.race.t,stand:v.stand,cadence:v.cadence,power:App.race.player.power}}"""))
        await p.screenshot(path=str(out/'attack-motion.png'))
        # Compare the same seeded physical TTT, not independently authored data.
        comparison={}
        for version in ['V20','V22']:
            vc,vp=await load('Grand-Tour-'+version+'.html')
            comparison[version]=await vp.evaluate("""()=>{const r=new Race(0,0,'single',null,2026001),a=[];for(let i=0;i<2400;i++){r.tick();if(i%100===0&&r.t>10){const q=r.teams[0].relay;a.push({count:q.order.length,returning:q.returning.length,maxGap:Math.max(0,...q.order.slice(1).map((id,i)=>r.riders[q.order[i]].x-r.riders[id].x))});}}return{seconds:120,samples:a.length,meanQueue:a.reduce((s,a)=>s+a.count,0)/a.length,meanReturning:a.reduce((s,a)=>s+a.returning,0)/a.length,maxPairGap:Math.max(...a.map(a=>a.maxGap)),rotations:r.audit.rotations.filter(a=>a.team===0).length}}""")
            await vc.close()
        comparison['pass']=comparison['V22']['maxPairGap']<comparison['V20']['maxPairGap'] and comparison['V22']['meanQueue']>comparison['V20']['meanQueue']
        record('ttt_seeded_comparison',comparison)
        # A proper Tour stage, with its actual result used as next-stage prior.
        await p.evaluate("""()=>{closeDialogs();Store.pendingCeremony=null;Store.tour={id:'v21-cross-stage',playerId:0,seedBase:2026001,seedOrigin:'test',timeModel:'race-world-v1',results:[]};window.tourRace=new Race(0,0,'tour',null,seedForStage(2026001,0));}""")
        for _ in range(20):
            state=await p.evaluate("""()=>{for(let i=0;i<1500&&!tourRace.complete;i++)tourRace.tick();return{complete:tourRace.complete,t:tourRace.t}}""")
            if state['complete']: break
        assert state['complete']
        await p.evaluate('initializeRace(tourRace)'); await p.wait_for_timeout(1200)
        record('tour_classification_committed',await p.evaluate("""()=>({pass:Store.tour.results.length===1&&App.race.recorded&&App.finishFlow.settleCount===1,results:Store.tour.results.length,settled:App.finishFlow.settleCount,active:Store.tour.results[0].season.active.filter(Boolean).length})"""))
        await p.locator('#ceremonySkip').click();await p.wait_for_timeout(300);await p.locator('#nextStage').click()
        record('cross_stage_state',await p.evaluate("""()=>{const r=App.race,expected=Fatigue.morning(RIDER_DATA[0],Store.tour.results[0],1);return{pass:r.stageIndex===1&&r.mode==='tour'&&r.seed===seedForStage(Store.tour.seedBase,1)&&r.player.startFatigue===expected.fatigue,stage:r.stageIndex+1,seed:r.seed,startFatigue:r.player.startFatigue,expectedFatigue:expected.fatigue,season:!!r.prior?.season}}"""))
        # A naturally seeded rainy race, not a changed sky over dry physics.
        rain=await p.evaluate("""()=>{let seed=1;while(seed<1000&&Weather.generate(STAGE_DATA[4],seed).kind!=='rain')seed++;const r=new Race(4,0,'single',null,seed);for(let i=0;i<600;i++)r.tick();initializeRace(r);r.paused=true;viewFor(r).alpha=1;updateHud(true);drawRace();return{pass:r.conditions.kind==='rain',seed,weather:r.conditions.kind,rolling:r.player.rolling,climate:r.player.climate}}""")
        record('rain_scene',rain);await p.wait_for_timeout(700);await p.screenshot(path=str(out/'rain-peloton.png'))
        for w,h in [(320,740),(768,560)]:
            await p.set_viewport_size({'width':w,'height':h});await p.wait_for_timeout(300);await p.evaluate('updateHud(true);drawRace();window.scrollTo(0,0)')
            record('viewport_'+str(w),await p.evaluate("""()=>{const c=document.querySelector('#raceCanvas').getBoundingClientRect(),overflow=document.documentElement.scrollWidth-innerWidth;return{pass:overflow<=1&&c.width>200&&c.right<=innerWidth,overflow,canvasWidth:c.width}}"""))
            await p.screenshot(path=str(out/f'viewport-{w}.png'))
        await ctx.close();await browser.close()
    report['pass']=not report['errors']
    (out/'extended-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2), encoding='utf-8')
    print('COMPLETE',report['pass'],flush=True)
    if not report['pass']:raise SystemExit(1)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--injected',action='store_true');parser.add_argument('--out',default='/tmp/grand-tour-v22-extended');asyncio.run(main(parser.parse_args()))
