"""Real offline finish/replay regression for the ceremony transport.

Uses the public quick-finish control and the production simulation. The DOM
mutation probe samples presentation time only after the result is frozen.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]


async def main(args):
    source = args.source.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {"sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "checks": {}, "errors": [], "pass": False}

    def check(name, value):
        report["checks"][name] = value
        (out / "transport.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        assert value["pass"], (name, value)
        print(name, "PASS", flush=True)

    async with async_playwright() as pw:
        launch = {"headless": True}
        if args.executable_path:
            launch["executable_path"] = str(args.executable_path)
        browser = await pw.chromium.launch(**launch)
        try:
            context = await browser.new_context(viewport={"width": 1440, "height": 1000})
            await context.set_offline(True)
            page = await context.new_page()
            page.on("pageerror", lambda e: report["errors"].append(str(e)))
            await page.goto(source.as_uri())
            await page.locator("#chooseStage").click()
            await page.locator('[data-stage="4"]').click()
            await page.locator("#startRace").click()
            await page.locator("#quickFinishButton").click()
            await page.wait_for_function("App.finishFlow?.phase==='ceremony'", timeout=180000)
            await page.locator("#ceremonyPause").click()
            before = await page.evaluate("JSON.stringify(App.result)")
            check("same_frame_has_no_dom_writes", await page.evaluate("""() => {
                const f=App.finishFlow;
                CeremonyPlayer.update(f);
                const observer=new MutationObserver(()=>{});
                observer.observe($('ceremonyLayer'),{attributes:true,childList:true,subtree:true,characterData:true});
                for(let i=0;i<240;i++)CeremonyPlayer.update(f);
                const mutations=observer.takeRecords().length;observer.disconnect();
                return {pass:mutations===0,updates:240,mutations};
            }"""))
            check("paused_frame_retained_and_seek_invalidates", await page.evaluate("""() => {
                const f=App.finishFlow,original=CeremonyStage.staticSet;
                Ceremony.draw(f);let paints=0;
                CeremonyStage.staticSet=function(...args){paints++;return original.apply(this,args)};
                try {
                    for(let i=0;i<240;i++)Ceremony.draw(f);
                    const unchanged=paints;
                    f.elapsed+=.01;Ceremony.draw(f);
                    return {pass:unchanged===0&&paints===1,repeatedDraws:240,unchangedPaints:unchanged,afterSeekPaints:paints};
                } finally {CeremonyStage.staticSet=original;}
            }"""))
            await page.locator('[data-beat="1"]').click()
            check("paused_seek_updates_chapter_and_time", await page.evaluate("""() => {
                const f=App.finishFlow,b=f.plan.beats[1],s=CeremonyStage.scene(f.plan,f.elapsed,CeremonyStage.metrics(1280,720));
                return {pass:f.paused&&s.shown.kind===b.kind&&$('ceremonyChapters').children[1].getAttribute('aria-current')==='step'&&$('ceremonyTime').textContent.startsWith('00:'+String(Math.floor(f.elapsed)%60).padStart(2,'0')),kind:b.kind,time:$('ceremonyTime').textContent};
            }"""))
            await page.locator("#ceremonyPause").click()
            await page.wait_for_timeout(1200)
            check("play_state", {"pass": await page.locator("#ceremonyPause").get_attribute("aria-pressed") == "false"})
            await page.locator("#ceremonyPause").click()
            await page.locator('[data-beat="0"]').click()
            await page.wait_for_timeout(250)  # Existing chapter-colour transition.
            await page.screenshot(path=str(out / "ceremony-desktop.png"))
            await page.set_viewport_size({"width": 390, "height": 844})
            await page.wait_for_timeout(200)
            check("paused_resize_repaints", await page.evaluate("""() => {
                const c=$('ceremonyCanvas'),r=c.getBoundingClientRect(),s=CeremonyStage.lastFrame;
                return {pass:!!s&&s.w===Math.round(r.width)&&s.h===Math.round(r.height)&&s.pw===c.width&&s.ph===c.height};
            }"""))
            await page.screenshot(path=str(out / "ceremony-mobile.png"))
            check("mobile_transport_reachable", await page.evaluate("""() => {
                const r=$('ceremonyNext').getBoundingClientRect();return {pass:r.right<=innerWidth&&r.bottom<=innerHeight&&document.documentElement.scrollWidth<=innerWidth+1};
            }"""))
            await page.locator("#ceremonySkip").click()
            await page.locator("#replayCeremony").click()
            check("replay_resets_transport", await page.evaluate("""() => ({pass:$('ceremonyPause').getAttribute('aria-pressed')==='false'&&$('ceremonyLayer').dataset.paused==='false'&&$('ceremonyTime').textContent.startsWith('00:00')&&document.querySelectorAll('#ceremonyChapters [aria-current]').length===0})"""))
            await page.keyboard.press("Escape")
            check("ledger_and_focus_preserved", {"pass": before == await page.evaluate("JSON.stringify(App.result)") and await page.evaluate("document.activeElement.id==='replayCeremony'")})
            check("console", {"pass": not report["errors"], "errors": report["errors"]})
        finally:
            await browser.close()
    report["pass"] = True
    (out / "transport.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "Grand-Tour-V25.html")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--executable-path", type=Path)
    asyncio.run(main(parser.parse_args()))
