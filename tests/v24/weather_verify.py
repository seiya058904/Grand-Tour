"""Play naturally generated weather; never override race conditions."""
import argparse, asyncio, hashlib, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding='utf8')

async def main(args):
    args.out.mkdir(parents=True, exist_ok=True)
    src = ROOT / 'Grand-Tour-V24.html'
    report = {'sha256': hashlib.sha256(src.read_bytes()).hexdigest(), 'cases': [], 'errors': []}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1440, 'height': 1000})
        await context.set_offline(True)
        page = await context.new_page()
        page.on('pageerror', lambda error: report['errors'].append(str(error)))
        for kind, stage, seed in [('sun', 4, 2058765), ('cloud', 4, 12345), ('rain', 6, 12345)]:
            await page.goto(src.as_uri() + '?test')
            before = await page.evaluate('''([stage, seed]) => {
                App.testingFreeze = true; App.blockStoreWrite = true;
                const race = new Race(stage, 0, 'single', null, seed);
                for (let i = 0; i < 800; i++) race.tick();
                initializeRace(race); App.testingFreeze = false;
                return {t: race.t, kind: race.conditions.kind, conditions: race.conditions};
            }''', [stage, seed])
            assert before['kind'] == kind
            await page.wait_for_timeout(3500)
            after = await page.evaluate('''() => {
                const r = App.race; r.paused = true;
                const before = JSON.stringify(r.snapshot());
                for (let i = 0; i < 8; i++) drawRace();
                return {t: r.t, kind: r.conditions.kind, pure: before === JSON.stringify(r.snapshot()), riders: r.riders.length};
            }''')
            assert after['t'] > before['t'] and after['pure'] and after['kind'] == kind and after['riders'] == 184
            await page.screenshot(path=str(args.out / (kind + '.png')))
            report['cases'].append({'stage': stage + 1, 'seed': seed, 'before': before, 'after': after})
        await context.close()
        await browser.close()
    report['pass'] = not report['errors']
    (args.out / 'weather.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=False)); assert report['pass']

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    asyncio.run(main(parser.parse_args()))
