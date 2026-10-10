"""Real production UI regression for empty / legacy progress ownership.

Browser plugin not available; uses the repository's existing Python Playwright
workflow. A same-process ephemeral HTTP server avoids relying on external ports.
Only the animation-loop freeze and reproducible seed are test instrumentation.
"""
import argparse
import asyncio
import functools
import hashlib
import json
import threading
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote
from playwright.async_api import async_playwright


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        if unquote(self.path.split('?')[0]) == '/' + self.source_name:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(self.source_bytes)))
            self.end_headers()
            self.wfile.write(self.source_bytes)
        elif self.path.split('?')[0] == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
        else:
            super().do_GET()


async def main(args):
    args.out.mkdir(parents=True, exist_ok=True)
    # Every page in a multi-page test receives the same captured source bytes.
    Handler.source_name = args.source.name
    Handler.source_bytes = args.source.read_bytes()
    handler = functools.partial(Handler, directory=str(args.source.parent))
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/{quote(args.source.name)}'
    report = {'source': str(args.source), 'sourceSHA256': hashlib.sha256(Handler.source_bytes).hexdigest(),
              'production_query': True, 'browser_path': 'Browser plugin not available; Python Playwright', 'cases': [],
              'errors': [], 'console': [], 'externalRequests': []}
    fixtures = None
    if args.validation_fixtures:
        fixtures = {name: json.loads((args.validation_fixtures / name).read_text(encoding='utf-8'))
                    for name in ['natural-first-finish.json', 'natural-second-stage-save.json']}
        report['fixtureSHA256'] = {name: hashlib.sha256((args.validation_fixtures / name).read_bytes()).hexdigest() for name in fixtures}

    async def context(browser, locks, width=1440, legacy=None):
        ctx = await browser.new_context(viewport={'width': width, 'height': 1000 if width > 600 else 844}, reduced_motion='reduce')
        if not locks:
            await ctx.add_init_script("Object.defineProperty(navigator,'locks',{value:undefined})")
        if legacy is not None:
            await ctx.add_init_script("localStorage.setItem('tour-cycling-2026-refined-v9'," + json.dumps(legacy) + ")")
        return ctx

    async def page(ctx):
        p = await ctx.new_page()
        p.on('pageerror', lambda e: report['errors'].append(str(e)))
        p.on('console', lambda m: report['console'].append(m.text) if m.type == 'error' else None)
        p.on('request', lambda r: report['externalRequests'].append(r.url) if r.url.startswith(('http:', 'https:')) and not r.url.startswith(f'http://127.0.0.1:{server.server_port}/') else None)
        p.on('dialog', lambda d: d.accept())
        await p.goto(url)
        assert await p.evaluate('TEST_MODE') is False
        await p.evaluate('App.testingFreeze=true')
        assert 'grand tour' in (await p.title()).lower(), 'page title identifies Grand Tour'
        assert await p.locator('#newTour').is_visible()
        return p

    async def begin(p):
        await p.locator('#newTour').click()
        await p.evaluate('App.prep.seedBase=314159')
        await p.locator('#startRace').click()
        await p.evaluate('saveQueue')

    async def volume(p, value):
        # This control is actually available on the home screen. Quality and
        # label selectors are race-only, so exercising them here would require
        # an unrelated single-stage detour or bypassing visibility checks.
        await p.locator('#musicOpen').click()
        slider = p.locator('#musicVolume')
        await slider.focus()
        await slider.press('Home' if value < 50 else 'End')
        await slider.press('ArrowRight' if value < 50 else 'ArrowLeft')
        await p.locator('#musicClose').click()
        await p.evaluate('saveQueue')
        return await slider.input_value()

    async def case(name, locks, fn, width=1440):
        row = {'name': name, 'locks': locks, 'width': width}
        try:
            row.update(await fn())
            row['pass'] = True
        except Exception as e:
            row.update({'pass': False, 'failure': str(e), 'traceback': traceback.format_exc()})
        report['cases'].append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=['--no-sandbox'])
            report['browser'] = browser.version
            for locks in [False, True]:
                for width in [1440, 390]:
                    async def same_page(locks=locks, width=width):
                        ctx = await context(browser, locks, width)
                        try:
                            p = await page(ctx)
                            changed_volume = await volume(p, 24)
                            assert await p.evaluate('JSON.parse(localStorage.getItem(CONFIG.saveKey)).tour') is None
                            await begin(p)
                            state = await p.evaluate("({stored:JSON.parse(localStorage.getItem(CONFIG.saveKey)),conflict:!!App.saveConflict,warning:$('storageWarning').textContent})")
                            await p.screenshot(path=str(args.out / f'first-settings-{locks}-{width}.png'))
                            assert state['stored']['tour'] is not None, state['warning']
                            assert not state['conflict']
                            assert state['stored']['settings']['musicVolume'] == int(changed_volume) / 100
                            await p.locator('#pauseButton').click()
                            await p.locator('#saveAndHome').click()
                            await p.evaluate('saveQueue')
                            await p.reload()
                            await p.evaluate('App.testingFreeze=true')
                            assert await p.locator('#continueTour').is_visible()
                            await p.locator('#continueTour').click()
                            assert await p.evaluate('App.race.stageIndex') == 0
                            assert await p.evaluate('App.race.riders.length') == 184
                            return {'firstSave': True, 'refreshContinue': True, 'riders': 184}
                        finally:
                            await ctx.close()
                    await case('fresh page settings -> first tour -> refresh -> continue', locks, same_page, width)

                async def two_pages(locks=locks):
                    ctx = await context(browser, locks)
                    try:
                        a, b = await page(ctx), await page(ctx)
                        await volume(a, 24)
                        await volume(b, 74)
                        await begin(a)
                        before = await a.evaluate('localStorage.getItem(CONFIG.saveKey)')
                        assert json.loads(before)['tour'] is not None, 'first owner failed after two initial settings changes'
                        await begin(b)
                        assert await b.evaluate('!!App.saveConflict')
                        assert await b.evaluate('localStorage.getItem(CONFIG.saveKey)') == before
                        await b.locator('#visualQuality').select_option('low')
                        await b.evaluate('saveQueue')
                        after = json.loads(await b.evaluate('localStorage.getItem(CONFIG.saveKey)'))
                        prior = json.loads(before)
                        for key in ['tour', 'active', 'pendingCeremony', 'progressRevision']:
                            assert after[key] == prior[key]
                        assert await b.evaluate('async()=>await persist()') is False
                        await b.screenshot(path=str(args.out / f'two-empty-pages-{locks}.png'))
                        return {'oneProgressOwner': True, 'staleSaveRejected': True, 'settingsMergedWithoutAdoption': True}
                    finally:
                        await ctx.close()
                await case('two empty pages merge settings before claiming progress', locks, two_pages)

                async def legacy_page(locks=locks):
                    seed_ctx = await context(browser, locks)
                    try:
                        seed = await page(seed_ctx)
                        await begin(seed)
                        raw = await seed.evaluate('localStorage.getItem(CONFIG.saveKey)')
                    finally:
                        await seed_ctx.close()
                    ctx = await context(browser, locks, legacy=raw)
                    try:
                        p = await page(ctx)
                        assert await p.evaluate('localStorage.getItem(CONFIG.saveKey)') is None
                        assert await p.locator('#continueTour').is_visible()
                        changed_volume = await volume(p, 24)
                        await p.locator('#continueTour').click()
                        await p.locator('#pauseButton').click()
                        await p.locator('#saveAndHome').click()
                        await p.evaluate('saveQueue')
                        state = await p.evaluate("({conflict:!!App.saveConflict,stored:JSON.parse(localStorage.getItem(CONFIG.saveKey)),legacy:localStorage.getItem('tour-cycling-2026-refined-v9')})")
                        await p.screenshot(path=str(args.out / f'legacy-settings-{locks}.png'))
                        assert not state['conflict'], 'legacy settings-first promotion caused a self-conflict'
                        assert state['stored']['tour']['id'] == json.loads(raw)['tour']['id']
                        assert state['stored']['settings']['musicVolume'] == int(changed_volume) / 100
                        assert state['legacy'] == raw
                        return {'legacyTourRetained': True, 'saveAfterPromotion': True, 'legacyBytesUnchanged': True}
                    finally:
                        await ctx.close()
                await case('legacy-key load -> settings -> continue -> save', locks, legacy_page)
                if fixtures:
                    for width in [1440, 390]:
                        async def validation_boundaries(locks=locks, width=width):
                            ctx = await context(browser, locks, width)
                            try:
                                p = await page(ctx)
                                dialogs = []
                                p.on('dialog', lambda d: dialogs.append(d.message))
                                prefix = json.loads(json.dumps(fixtures['natural-second-stage-save.json']))
                                prefix['tour']['id'] = f'validation-{locks}-{width}'
                                await p.locator('#saveFile').set_input_files({'name': 'valid-prefix.json', 'mimeType': 'application/json', 'buffer': json.dumps(prefix).encode()})
                                await p.wait_for_function('id=>Store.tour?.id===id', arg=prefix['tour']['id'])
                                await p.evaluate('saveQueue')
                                canonical = await p.evaluate('localStorage.getItem(CONFIG.saveKey)')
                                await p.evaluate("localStorage.setItem(CONFIG.saveKey+'-before-import','existing-import-backup');localStorage.setItem(CONFIG.saveKey+'-recovery-backup','existing-recovery-backup')")
                                first = json.loads(json.dumps(fixtures['natural-first-finish.json']))
                                cutoff = json.loads(json.dumps(prefix))
                                cutoff['tour']['results'] = []
                                cutoff['active'] = first
                                cutoff['active']['cutoff']['deadline'] = 1
                                seed = json.loads(json.dumps(prefix))
                                seed['active']['seed'] = -1
                                historical = json.loads(json.dumps(prefix))
                                historical['active'] = None
                                historical['tour']['results'][0]['cutoff']['time'] = 1
                                historical['tour']['results'][0]['cutoff']['deadline'] = 1 + historical['tour']['results'][0]['cutoff']['percent']
                                rejected = []
                                for label, damaged in [('active-cutoff', cutoff), ('active-migration-seed', seed), ('historical-cutoff', historical)]:
                                    await p.evaluate("$('toast').textContent=''")
                                    count = len(dialogs)
                                    await p.locator('#saveFile').set_input_files({'name': label + '.json', 'mimeType': 'application/json', 'buffer': json.dumps(damaged).encode()})
                                    await p.wait_for_function("$('toast').textContent.startsWith('导入未完成：')")
                                    toast = await p.locator('#toast').inner_text()
                                    protection = await p.evaluate("raw=>({canonical:localStorage.getItem(CONFIG.saveKey)===raw,importBackup:localStorage.getItem(CONFIG.saveKey+'-before-import')==='existing-import-backup',recoveryBackup:localStorage.getItem(CONFIG.saveKey+'-recovery-backup')==='existing-recovery-backup'})", canonical)
                                    assert all(protection.values()), protection
                                    assert len(dialogs) == count, 'a damaged file must fail before confirmation or backup writes'
                                    rejected.append({'file': label, 'toast': toast, 'protected': protection, 'confirmationDialogs': 0})
                                await p.screenshot(path=str(args.out / f'rejected-imports-{locks}-{width}.png'))
                                damaged_raw = json.dumps(seed)
                                await p.evaluate('raw=>localStorage.setItem(CONFIG.saveKey,raw)', damaged_raw)
                                await p.reload()
                                await p.evaluate('App.testingFreeze=true')
                                recovered = await p.evaluate("raw=>({stages:Store.tour?.results.length,active:Store.active,settings:Store.settings,canonicalUntouched:localStorage.getItem(CONFIG.saveKey)===raw,recoveryBackupExact:localStorage.getItem(CONFIG.saveKey+'-recovery-backup')===raw,importBackupUntouched:localStorage.getItem(CONFIG.saveKey+'-before-import')==='existing-import-backup',blocked:!!App.blockStoreWrite,warning:$('storageWarning').textContent})", damaged_raw)
                                assert recovered['stages'] == 1 and recovered['active'] is None
                                assert recovered['canonicalUntouched'] and recovered['recoveryBackupExact'] and recovered['importBackupUntouched']
                                assert recovered['settings'] == prefix['settings'] and not recovered['blocked']
                                assert '进行中比赛无法恢复' in recovered['warning']
                                await p.screenshot(path=str(args.out / f'recovered-prefix-{locks}-{width}.png'))
                                await p.locator('#continueTour').click()
                                await p.evaluate('saveQueue')
                                continued = await p.evaluate("()=>{const d=SaveCodec.decode(JSON.parse(localStorage.getItem(CONFIG.saveKey)));return{stage:App.race.stageIndex,seed:App.race.seed,stages:d.store.tour.results.length,issues:d.issues}}")
                                assert continued == {'stage': 1, 'seed': (prefix['tour']['seedBase'] + 8191) & 0xffffffff, 'stages': 1, 'issues': []}
                                assert await p.evaluate("raw=>localStorage.getItem(CONFIG.saveKey+'-recovery-backup')===raw", damaged_raw)
                                return {'rejected': rejected, 'recovered': recovered, 'continued': continued}
                            finally:
                                await ctx.close()
                        await case('strict import protection and damaged-active reload recovery', locks, validation_boundaries, width)
            await browser.close()
    finally:
        server.shutdown()
        server.server_close()
        report['passed'] = sum(c.get('pass', False) for c in report['cases'])
        report['failed'] = len(report['cases']) - report['passed']
        report['pass'] = bool(report['cases']) and report['failed'] == 0 and not report['errors'] and not report['console'] and not report['externalRequests']
        (args.out / 'storage-first-settings-browser.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if not report['pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[2] / 'Grand-Tour-V25.html')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--validation-fixtures', type=Path,
                        help='Optional natural fixtures generated by storage-validation.cjs (adds strict import/reload cases).')
    args = parser.parse_args()
    args.source = args.source.resolve()
    asyncio.run(main(args))
