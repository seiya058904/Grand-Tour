"""Verify the actual ZIP, then play its extracted offline entry in a fresh browser."""
import argparse, asyncio, hashlib, json, subprocess, sys, zipfile
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding='utf8')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

async def main(args):
    args.out.mkdir(parents=True, exist_ok=False)
    extraction = (args.out / 'extracted').resolve()
    with zipfile.ZipFile(args.zip) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), 'duplicate ZIP members'
        assert all((extraction / name).resolve().is_relative_to(extraction) for name in names), 'unsafe ZIP path'
        assert archive.testzip() is None, 'ZIP CRC failure'
        archive.extractall(extraction)
    root = extraction / 'Grand-Tour-V24'
    manifest = {}
    for line in (root / 'SHA256SUMS.txt').read_text(encoding='utf8').splitlines():
        sha, name = line.split('  ', 1)
        assert name not in manifest and (root / name).resolve().is_relative_to(root)
        assert digest(root / name) == sha, name
        manifest[name] = sha
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    assert actual == set(manifest) | {'SHA256SUMS.txt'}, 'manifest does not cover exact package contents'
    assert digest(root / 'Grand-Tour-V24.html') == digest(ROOT / 'Grand-Tour-V24.html'), 'package differs from workspace payload'
    subprocess.run([sys.executable, str(root / 'tests/v24/static_verify.py'), '--manifest'], check=True)
    report = {'zip_sha256': digest(args.zip), 'html_sha256': digest(root / 'Grand-Tour-V24.html'),
              'manifest_files': len(manifest), 'crc': True, 'exact_manifest': True, 'offline': True,
              'errors': [], 'network_requests': [], 'checks': {}}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        report['browser'] = browser.version
        context = await browser.new_context(viewport={'width': 1440, 'height': 1000})
        await context.set_offline(True)
        page = await context.new_page()
        page.on('pageerror', lambda error: report['errors'].append(str(error)))
        page.on('request', lambda request: report['network_requests'].append(request.url) if request.url.startswith(('http:', 'https:')) else None)
        await page.goto((root / 'index.html').as_uri())
        await page.wait_for_url('**/Grand-Tour-V24.html')
        await page.locator('#chooseStage').click()
        await page.locator('button[data-stage="4"]').last.click()
        await page.locator('#startRace').click()
        await page.wait_for_timeout(3000)
        first = await page.evaluate('({t:App.race.t,n:App.race.riders.length})')
        assert first['n'] == 184 and first['t'] > 0
        await page.locator('#attackButton').click()
        await page.wait_for_timeout(2500)
        after = await page.evaluate('({t:App.race.t,power:App.race.player.power,valid:App.race.riders.every(r=>Number.isFinite(r.x)&&Number.isFinite(r.v))})')
        assert after['t'] > first['t'] and after['power'] > 0 and after['valid']
        await page.locator('#pauseButton').click()
        stopped = await page.evaluate('App.race.t')
        await page.wait_for_timeout(600)
        assert await page.evaluate('App.race.t') == stopped
        await page.locator('#resumeRace').click()
        await page.locator('#raceGC').click()
        await page.keyboard.press('Escape')
        report['checks']['entry_and_controls'] = {'pass': True, 'first': first, 'after': after}
        await page.screenshot(path=str(args.out / 'package-desktop.png'))
        await page.set_viewport_size({'width': 390, 'height': 844})
        await page.wait_for_timeout(400)
        overflow = await page.evaluate('document.documentElement.scrollWidth-innerWidth')
        assert overflow <= 1
        report['checks']['mobile_entry'] = {'pass': True, 'width': 390, 'overflow': overflow}
        await page.screenshot(path=str(args.out / 'package-mobile.png'))
        await context.close()
        await browser.close()
    report['pass'] = not report['errors'] and not report['network_requests']
    (args.out / 'package-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=False, indent=2)); assert report['pass']

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('zip', type=Path)
    parser.add_argument('--out', type=Path, required=True, help='new directory; existing paths are never replaced')
    asyncio.run(main(parser.parse_args()))
