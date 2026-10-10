#!/usr/bin/env python3
"""Verify exact V25 ZIP bytes and use its extracted offline production entry."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import zipfile
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


async def main(args):
    args.out.mkdir(parents=True, exist_ok=False)
    extraction = (args.out / 'extracted').resolve()
    with zipfile.ZipFile(args.zip) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), 'Duplicate ZIP names'
        assert all(n.startswith('Grand-Tour-V25/') and not PurePosixPath(n).is_absolute() and
                   '..' not in PurePosixPath(n).parts and not n.endswith('/') for n in names)
        assert archive.testzip() is None, 'CRC failure'
        archive.extractall(extraction)
    root = extraction / 'Grand-Tour-V25'
    manifest = {}
    for line in (root / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        assert name not in manifest and (root / name).resolve().is_relative_to(root)
        assert sha(root / name) == digest, name
        manifest[name] = digest
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    assert actual == set(manifest) | {'SHA256SUMS.txt'}, 'Exact manifest coverage'
    assert sha(root / 'Grand-Tour-V25.html') == sha(ROOT / 'Grand-Tour-V25.html'), 'Workspace/package mismatch'
    subprocess.run([sys.executable, str(root / 'tests/v25/static_verify.py'), '--out', str(args.out / 'static.json')], check=True)
    report = {'zip': args.zip.name, 'zipSHA256': sha(args.zip), 'bytes': args.zip.stat().st_size,
              'htmlSHA256': sha(root / 'Grand-Tour-V25.html'), 'manifestFiles': len(manifest),
              'checks': [{'name': 'CRC-safe-paths-exact-manifest', 'pass': True},
                         {'name': 'extracted-static-11', 'pass': True}],
              'errors': [], 'console': [], 'externalRequests': []}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        report['browser'] = browser.version
        context = await browser.new_context(viewport={'width': 1440, 'height': 1000})
        await context.set_offline(True)
        page = await context.new_page()
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        page.on('console', lambda m: report['console'].append(m.text) if m.type in ('warning', 'error') else None)
        page.on('request', lambda r: report['externalRequests'].append(r.url) if r.url.startswith(('http:', 'https:')) else None)
        page.on('dialog', lambda d: d.accept())
        await page.goto((root / 'index.html').as_uri())
        await page.wait_for_url('**/Grand-Tour-V25.html')
        assert await page.evaluate("typeof __TOUR_TEST__==='undefined' && document.documentElement.dataset.build==='2500'")
        await page.locator('#musicOpen').click()
        await page.locator('#musicVolume').focus()
        await page.keyboard.press('ArrowLeft')
        await page.locator('#musicClose').click()
        await page.locator('#newTour').click()
        await page.locator('#startRace').click()
        await page.wait_for_timeout(3000)
        first = await page.evaluate('({t:App.race.t,n:App.race.riders.length,stored:!!JSON.parse(localStorage.getItem(CONFIG.saveKey))?.active})')
        assert first['t'] > 0 and first['n'] == 184 and first['stored']
        await page.locator('#attackButton').click()
        assert await page.evaluate('App.race.player.attackUntil>App.race.t'), 'Actual attack begins'
        await page.wait_for_timeout(1800)
        after = await page.evaluate('({t:App.race.t,power:App.race.player.power,finite:App.race.riders.every(r=>Number.isFinite(r.x)&&Number.isFinite(r.v))})')
        assert after['t'] > first['t'] and after['power'] > 0 and after['finite']
        await page.locator('#pauseButton').click()
        stopped = await page.evaluate('App.race.t')
        await page.wait_for_timeout(600)
        assert await page.evaluate('App.race.t') == stopped
        await page.locator('#resumeRace').click()
        await page.wait_for_timeout(300)
        assert await page.evaluate('App.race.t') > stopped, 'Resume advances the real clock'
        report['checks'].append({'name': 'native-entry-settings-first-tour-attack-pause', 'pass': True, 'first': first, 'after': after})
        await page.screenshot(path=str(args.out / 'package-desktop.png'))
        await page.reload()
        await page.locator('#continueTour').click()
        await page.wait_for_timeout(1600)
        assert await page.evaluate("App.screen==='race'&&App.race.riders.length===184&&App.race.t>0&&!App.saveConflict")
        report['checks'].append({'name': 'native-first-tour-reload-continue', 'pass': True})
        for width, height in [(390, 844), (320, 740)]:
            await page.set_viewport_size({'width': width, 'height': height})
            await page.wait_for_timeout(350)
            overflow = await page.evaluate('document.documentElement.scrollWidth-innerWidth')
            assert overflow <= 1
            await page.locator('#raceGC').click()
            assert await page.evaluate("!$('mobileDeskBackdrop').hidden&&!App.race.paused")
            await page.keyboard.press('Escape')
            report['checks'].append({'name': f'offline-layout-centre-{width}', 'pass': True, 'overflow': overflow})
            await page.screenshot(path=str(args.out / f'package-{width}.png'))
        await context.close()
        await browser.close()
    report['checks'].append({'name': 'offline-console-health', 'pass': not (report['errors'] or report['console'] or report['externalRequests'])})
    report['passed'] = sum(c['pass'] for c in report['checks'])
    report['failed'] = len(report['checks']) - report['passed']
    report['skipped'] = 0
    report['pass'] = report['failed'] == 0
    (args.out / 'package-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    assert report['pass'], report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip', type=Path)
    parser.add_argument('--out', type=Path, required=True, help='New directory, never overwrite a prior verification')
    asyncio.run(main(parser.parse_args()))
