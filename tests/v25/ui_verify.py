#!/usr/bin/env python3
"""Offline V25 layout, keyboard and presentation review at desktop/mobile/DPR.

Uses the production UI and a deterministic naturally advanced race. Screenshots
are evidence for manual inspection, not an automatic claim of visual quality.
"""
import argparse
import asyncio
import hashlib
import json
import platform
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]


async def main(args):
    args.out.mkdir(parents=True, exist_ok=True)
    report = {'source': args.source.name,
              'sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
              'platform': platform.platform(), 'checks': [], 'errors': [],
              'console': [], 'externalRequests': [], 'screenshots': []}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        report['browser'] = browser.version
        for w, h, dpr in [(320, 740, 1), (390, 844, 1), (768, 900, 1),
                          (1920, 1080, 1), (3840, 2160, 1), (1920, 1080, 2)]:
            context = await browser.new_context(viewport={'width': w, 'height': h},
                                                device_scale_factor=dpr)
            await context.set_offline(True)
            page = await context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.on('console', lambda m: report['console'].append(m.text)
                    if m.type in ('error', 'warning') else None)
            page.on('request', lambda r: report['externalRequests'].append(r.url)
                    if r.url.startswith(('http:', 'https:')) else None)
            await page.goto(args.source.as_uri() + '?test')
            await page.evaluate("App.testingFreeze=true; App.blockStoreWrite=true; Store.settings.quality='full'")
            await page.evaluate('document.fonts.ready')
            await page.locator('#chooseStage').click()
            await page.locator('button[data-stage="4"]').click()
            await page.locator('#startRace').click()
            # Keep screenshot comparisons on the same naturally produced state.
            await page.evaluate('''()=>{
                const r=new Race(4,0,'single',null,2058765);
                for(let i=0;i<800;i++)r.tick();
                initializeRace(r);App.testingFreeze=true;r.paused=true;
                viewFor(r).alpha=1;updateHud(true);drawRace();
            }''')
            await page.wait_for_timeout(280)
            geometry = await page.evaluate('''()=>{
                const canvas=$('raceCanvas'),box=canvas.getBoundingClientRect();
                const buttons=[...document.querySelectorAll('#effortButtons button,.action-row button')]
                    .map(e=>e.getBoundingClientRect());
                const metrics=[...document.querySelectorAll('.metrics .metric-label')]
                    .map(e=>e.getBoundingClientRect());
                const overlap=metrics.some((a,i)=>metrics.some((b,j)=>i<j&&
                    a.left<b.right-1&&a.right>b.left+1&&a.top<b.bottom-1&&a.bottom>b.top+1));
                return {viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,
                    overflow:document.documentElement.scrollWidth-innerWidth,
                    labelOverlap:overlap,canvas:{width:box.width,height:box.height,
                        backingWidth:canvas.width,backingHeight:canvas.height},
                    buttonMinWidth:Math.min(...buttons.map(x=>x.width)),
                    buttonMinHeight:Math.min(...buttons.map(x=>x.height)),
                    full:Store.settings.quality==='full',
                    pass:document.documentElement.scrollWidth<=innerWidth+1&&!overlap&&
                        buttons.every(b=>b.width>=44&&b.height>=40)&&box.width>250};
            }''')
            assert geometry['pass'], geometry
            report['checks'].append({'name': f'layout-{w}-dpr{dpr}', **geometry})
            name = f'race-{w}-dpr{dpr}.png'
            await page.screenshot(path=str(args.out / name))
            report['screenshots'].append(name)
            if w == 1920 and dpr == 1:
                await page.evaluate('App.race.paused=false;updateHud(true)')
                await page.locator('#raceCanvas').focus()
                await page.keyboard.press('ArrowUp')
                assert await page.evaluate('App.race.effort===1')
                await page.keyboard.press('ArrowDown')
                assert await page.evaluate('App.race.effort===0')
                await page.keyboard.press('Space')
                assert await page.evaluate('App.race.player.attackUntil>App.race.t')
                await page.keyboard.press('p')
                assert await page.evaluate("App.race.paused&&App.modalStack.at(-1)==='pauseBackdrop'")
                await page.locator('#pauseHelp').click()
                await page.keyboard.press('Escape')
                assert await page.evaluate("App.race.paused&&App.modalStack.join()==='pauseBackdrop'")
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(200)
                assert await page.evaluate("!App.race.paused&&!document.querySelector('.shell').inert")
                report['checks'].append({'name': 'keyboard-effort-attack-nested-pause', 'pass': True})
            if w == 390:
                await page.evaluate('App.race.paused=false;updateHud(true)')
                await page.locator('#raceGC').click()
                assert await page.evaluate("!$('mobileDeskBackdrop').hidden&&!App.race.paused&&document.querySelectorAll('#liveDesk').length===1")
                await page.wait_for_timeout(200)
                name = 'mobile-race-centre.png'
                await page.screenshot(path=str(args.out / name))
                report['screenshots'].append(name)
                await page.keyboard.press('Escape')
                report['checks'].append({'name': 'mobile-live-centre-single-dom', 'pass': True})
            await context.close()
        # Exercise the actual packaged root route, in native offline mode.
        if args.source.name == 'Grand-Tour-V25.html':
            context = await browser.new_context()
            await context.set_offline(True)
            page = await context.new_page()
            await page.goto((ROOT / 'index.html').as_uri())
            await page.wait_for_url('**/Grand-Tour-V25.html')
            assert await page.locator('#newTour').is_visible()
            assert await page.evaluate("typeof window.__TOUR_TEST__==='undefined'")
            report['checks'].append({'name': 'offline-root-entry-production-mode', 'pass': True})
            await context.close()
        await browser.close()
    report['checks'].append({'name': 'console-offline-health', 'pass': not (
        report['errors'] or report['console'] or report['externalRequests'])})
    report['passed'] = sum(c['pass'] for c in report['checks'])
    report['failed'] = len(report['checks']) - report['passed']
    report['skipped'] = 0
    report['pass'] = report['failed'] == 0
    (args.out / 'ui.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['source', 'browser', 'passed', 'failed', 'skipped']}), flush=True)
    assert report['pass'], report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'Grand-Tour-V25.html')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.source = args.source.resolve()
    asyncio.run(main(args))
