"""Exercise the real wheel controls while the seeded TTT retires its helper."""
import argparse
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]


async def main(out):
    out.mkdir(parents=True, exist_ok=True)
    reports, errors = [], []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        for seed in [314159, 12345]:
            for restore_auto in [False, True]:
                page = await browser.new_page(viewport={"width": 1440, "height": 1000})
                page.on("pageerror", lambda error: errors.append(str(error)))
                await page.goto((ROOT / "Grand-Tour-V23.html").as_uri() + "?test")
                await page.evaluate("""seed => {
                    App.testingFreeze = true;
                    initializeRace(new Race(0, 0, 'tour', null, seed));
                    while (App.race.t < 3) App.race.tick();
                    updateHud(true); drawRace();
                }""", seed)
                await page.locator('#wheelChoices button[data-follow="19"]').click()
                assert await page.evaluate("App.race.selectedWheel") == 19
                assert await page.locator("#autoWheelButton").inner_text() == "恢复 Auto"
                await page.evaluate("""() => {
                    while (App.race.t < 40) App.race.tick();
                    if (App.race.selectedWheel !== 19) throw Error('normal manual wheel lost');
                    updateHud(true); drawRace();
                }""")
                if restore_auto:
                    await page.locator("#autoWheelButton").click()
                    assert await page.evaluate("App.race.selectedWheel") == -1
                result = await page.evaluate("""() => {
                    const r = App.race;
                    while (!r.complete && !r.riders[19].tttDone && !r.riders[19].spent) r.tick();
                    for (let i = 0; i < 10; i++) r.tick();
                    updateHud(true); drawRace();
                    return {selected: r.selectedWheel, hold: r.hold, retired: r.riders[19].tttDone || r.riders[19].spent,
                        eligible: r.followEligibility(19).ok, t: r.t, speed: r.player.v};
                }""")
                assert result["retired"] and not result["eligible"], result
                assert result["selected"] == -1 and result["hold"] and result["speed"] > 1.6, result
                assert await page.locator('#wheelChoices button[data-follow="19"]').count() == 0
                assert await page.locator("#autoWheelButton").inner_text() == "Auto 已开启"
                await page.screenshot(path=str(out / f"{seed}-{restore_auto}.png"))
                reports.append({"seed": seed, "restoreAuto": restore_auto, **result})
                await page.close()
        await browser.close()
    (out / "report.json").write_text(json.dumps({"cases": reports, "errors": errors}, indent=2), encoding="utf-8")
    assert not errors, errors
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    asyncio.run(main(parser.parse_args().out))
