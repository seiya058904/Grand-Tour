"""V26 real-browser ceremony acceptance.

Plays the public flow (home -> stage 5 -> quick finish -> ceremony -> results
-> replay) offline, then records keyframe screenshots, per-frame paint cost,
pixel determinism across seek orders, reduced motion and the narrow layout.
Screenshots go to --out (keep it outside the repository).
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]

PAINT_PROBE = """async ([seconds]) => {
  const f=App.finishFlow,orig=Ceremony.draw.bind(Ceremony),costs=[],gaps=[];let last=0;
  Ceremony.draw=x=>{const a=performance.now();orig(x);const b=performance.now();costs.push(b-a);if(last)gaps.push(a-last);last=a;};
  try{await new Promise(r=>setTimeout(r,seconds*1000));}finally{Ceremony.draw=orig;}
  const q=(xs,p)=>{const s=xs.slice().sort((a,b)=>a-b);return s.length?+s[Math.min(s.length-1,Math.floor(p*s.length))].toFixed(2):null;};
  return {frames:costs.length,paintP50:q(costs,.5),paintP95:q(costs,.95),paintMax:q(costs,1),frameGapP50:q(gaps,.5),frameGapP95:q(gaps,.95)};
}"""

CANVAS_HASH = """async (t) => {
  const f=App.finishFlow;f.paused=true;f.elapsed=t;CeremonyStage.lastFrame=null;Ceremony.draw(f);
  const d=$('ceremonyCanvas').getContext('2d').getImageData(0,0,$('ceremonyCanvas').width,$('ceremonyCanvas').height).data;
  const h=await crypto.subtle.digest('SHA-256',d);return [...new Uint8Array(h)].map(x=>x.toString(16).padStart(2,'0')).join('');
}"""


async def to_ceremony(page, stage):
    await page.locator("#chooseStage").click()
    await page.locator(f'[data-stage="{stage}"]').click()
    await page.locator("#startRace").click()
    await page.locator("#quickFinishButton").click()
    await page.wait_for_function("App.finishFlow?.phase==='ceremony'", timeout=240000)


async def main(args):
    source, out = args.source.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {"source": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "checks": {}, "errors": []}

    def check(name, value):
        report["checks"][name] = value
        (out / "ceremony-browser.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(name, "PASS" if value.get("pass") else "FAIL", flush=True)

    async with async_playwright() as pw:
        launch = {"headless": True}
        if args.executable_path:
            launch["executable_path"] = str(args.executable_path)
        browser = await pw.chromium.launch(**launch)
        report["browser"] = browser.version
        try:
            ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
            await ctx.set_offline(True)
            page = await ctx.new_page()
            page.on("pageerror", lambda e: report["errors"].append(str(e)))
            page.on("console", lambda m: m.type == "error" and report["errors"].append(m.text))
            await page.goto(source.as_uri())
            check("identity", {"pass": await page.evaluate("CONFIG.buildVersion===260&&document.title.includes('V26')")})
            # The repository's default entry must open V26 in production mode.
            entry = await ctx.new_page()
            await entry.goto((ROOT / "index.html").as_uri())
            await entry.wait_for_url("**/Grand-Tour-V26.html")
            check("default_entry_is_v26", {"pass": await entry.evaluate("CONFIG.buildVersion===260&&typeof window.__TOUR_TEST__==='undefined'")})
            await entry.close()
            await to_ceremony(page, 4)
            before = await page.evaluate("JSON.stringify(App.result)")
            plan = await page.evaluate("App.finishFlow.plan.beats.map(b=>({kind:b.kind,start:b.start,seconds:b.seconds}))")
            dur = await page.evaluate("App.finishFlow.plan.duration")
            check("ordinary_timing", {"pass": 50 < dur < 65 and all(b["seconds"] == 10.5 for b in plan if b["kind"] in ("winner", "yellow", "green", "polka", "white")), "duration": dur, "beats": plan})

            # Live playback cost at 1x through the first award (intro, whip, hero).
            perf = await page.evaluate(PAINT_PROBE, [args.sample_seconds])
            perf["viewport"] = "1280x900"
            perf["pass"] = perf["frames"] > 30
            perf["target"] = "paint p95 < 16.7 ms (recorded; headless timing is indicative only)"
            check("playback_cost_desktop", perf)

            await page.locator("#ceremonyPause").click()
            for b in plan:
                if b["kind"] == "complete":
                    continue
                for label, offset in (("whip", 0.02), ("arrive", 2.6), ("hero", 5.2 if b["kind"] != "gc-final" else 8.6)):
                    await page.evaluate("t=>{const f=App.finishFlow;f.elapsed=t;CeremonyStage.lastFrame=null;Ceremony.draw(f);CeremonyPlayer.update(f)}", b["start"] + offset)
                    await page.locator(".ceremony-theatre").screenshot(path=str(out / f"desktop-{b['kind']}-{label}.png"))

            # Same presentation time => identical pixels after unrelated seeks.
            times = [plan[0]["start"] + 5.2, plan[1]["start"] + 0.1, plan[2]["start"] + 3.1]
            first = [await page.evaluate(CANVAS_HASH, t) for t in times]
            second = [await page.evaluate(CANVAS_HASH, t) for t in reversed(times)][::-1]
            check("pixel_determinism_any_seek_order", {"pass": first == second, "hashes": first})

            await page.set_viewport_size({"width": 390, "height": 844})
            await page.wait_for_timeout(150)
            await page.evaluate("t=>{const f=App.finishFlow;f.elapsed=t;CeremonyStage.lastFrame=null;Ceremony.draw(f)}", plan[1]["start"] + 5.2)
            await page.screenshot(path=str(out / "mobile-hero.png"))
            check("narrow_layout", await page.evaluate("""()=>{const n=$('ceremonyNext').getBoundingClientRect(),c=$('ceremonyCanvas').getBoundingClientRect();
                return {pass:n.right<=innerWidth&&n.bottom<=innerHeight&&c.width>300&&document.documentElement.scrollWidth<=innerWidth+1,canvas:[c.width,c.height]}}"""))
            await page.locator("#ceremonyPause").click()
            perf = await page.evaluate(PAINT_PROBE, [3])
            perf["viewport"] = "390x844"
            perf["pass"] = perf["frames"] > 10
            check("playback_cost_mobile", perf)
            await page.set_viewport_size({"width": 1280, "height": 900})

            # Space pauses, rate change, Esc skips to the unchanged result.
            await page.keyboard.press("Space")
            paused = await page.evaluate("App.finishFlow.paused")
            await page.select_option("#ceremonySpeed", "2")
            rate = await page.evaluate("App.finishFlow.rate")
            await page.keyboard.press("Escape")
            await page.wait_for_function("App.screen==='results'&&!App.finishFlow")
            await page.wait_for_timeout(900)
            after = await page.evaluate("JSON.stringify(App.result)")
            await page.screenshot(path=str(out / "results.png"))
            check("controls_and_record", {"pass": paused and rate == 2 and before == after, "pausedBySpace": paused, "rate": rate,
                                          "resultPlace": await page.locator("#resultPlace").text_content()})
            await page.locator("#replayCeremony").click()
            await page.wait_for_function("App.finishFlow?.phase==='ceremony'")
            await page.wait_for_timeout(1500)
            await page.keyboard.press("Escape")
            check("replay_read_only", {"pass": before == await page.evaluate("JSON.stringify(App.result)") and await page.evaluate("document.activeElement.id==='replayCeremony'")})
            await ctx.close()

            # Reduced motion: short static awards, fixed camera, no particles.
            ctx = await browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
            await ctx.set_offline(True)
            page = await ctx.new_page()
            page.on("pageerror", lambda e: report["errors"].append(str(e)))
            await page.goto(source.as_uri())
            await to_ceremony(page, 4)
            rm = await page.evaluate("""()=>{const f=App.finishFlow,m=CeremonyStage.metrics(1280,720),cams=f.plan.beats.map(b=>CeremonyStage.camera(f.plan,b.start+1,m));
                return {reduced:reducedMotion,seconds:f.plan.beats.map(b=>b.seconds),static:cams.every(c=>c.z===1&&c.x===m.cx&&!c.pan)}}""")
            await page.locator("#ceremonyPause").click()
            await page.locator(".ceremony-theatre").screenshot(path=str(out / "reduced-motion.png"))
            check("reduced_motion", {"pass": rm["reduced"] and rm["static"] and all(s in (4.5, 3, 6) for s in rm["seconds"]), **rm})
            await ctx.close()

            if args.final_stage:
                # The real 21-stage Tour finale needs a complete Tour; the GC
                # director is covered by tests/v26/ceremony.cjs. Here render a
                # synthetic stage-20 record through the production painter only.
                ctx = await browser.new_context(viewport={"width": 1280, "height": 720})
                page = await ctx.new_page()
                page.on("pageerror", lambda e: report["errors"].append(str(e)))
                await page.goto(source.as_uri())
                await page.evaluate("""()=>{const r=new Race(4);while(!r.complete)r.tick();window.__rec={...r.result(),stage:20};window.__plan=CeremonyStage.direct(Ceremony.plan(window.__rec,'tour'));
                  const c=document.createElement('canvas');c.id='shot';c.width=1280;c.height=720;c.style.cssText='position:fixed;inset:0;width:1280px;height:720px;z-index:9999';document.body.appendChild(c);}""")
                gc = await page.evaluate("window.__plan.beats.at(-2).start")
                for label, off in (("team", -6.0), ("rank3", 2.4), ("handoff", 5.9), ("lift", 8.4), ("spray", 10.2), ("wide", 15.5)):
                    await page.evaluate("t=>{const c=document.getElementById('shot');CeremonyStage.paint(c.getContext('2d'),1280,720,window.__plan,window.__rec,t,{saved:true})}", gc + off)
                    await page.locator("#shot").screenshot(path=str(out / f"final-{label}.png"))
                check("final_frames_rendered", {"pass": True, "note": "synthetic stage-20 identity fixture, painter only"})
                await ctx.close()
        finally:
            await browser.close()
    check("console", {"pass": not report["errors"], "errors": report["errors"]})
    report["pass"] = all(v.get("pass") for v in report["checks"].values())
    (out / "ceremony-browser.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PASS" if report["pass"] else "FAIL")
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "Grand-Tour-V26.html")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--executable-path", type=Path)
    parser.add_argument("--sample-seconds", type=float, default=8.0)
    parser.add_argument("--final-stage", action="store_true", help="also render synthetic GC finale frames")
    asyncio.run(main(parser.parse_args()))
