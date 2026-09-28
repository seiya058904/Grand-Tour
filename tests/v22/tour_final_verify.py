"""Load the actual 21-stage tour produced by tour-simulation.cjs and replay awards."""
import argparse,asyncio,json,hashlib
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]
async def main(args):
 args.out.mkdir(parents=True,exist_ok=True)
 report={'errors':[],'source_sha256':hashlib.sha256((ROOT/'Grand-Tour-V22.html').read_bytes()).hexdigest()}
 async with async_playwright() as pw:
  b=await pw.chromium.launch(headless=True);p=await b.new_page(viewport={'width':1440,'height':1000})
  p.on('pageerror',lambda e:report['errors'].append(str(e)));p.on('dialog',lambda d:d.accept())
  await p.goto((ROOT/'Grand-Tour-V22.html').as_uri()+'?test');await p.locator('#saveFile').set_input_files(str(args.tour.resolve()))
  await p.wait_for_function('Store.tour?.results.length===21');await p.locator('#continueTour').click();await p.wait_for_timeout(500)
  report['result']=await p.evaluate("({screen:App.screen,title:$('resultTitle').textContent,stages:Store.tour.results.length,gc:Classification.gcOrder(Store.tour.results.at(-1).season).slice(0,3)})")
  assert report['result']['screen']=='results'
  await p.screenshot(path=str(args.out/'tour-results.png'))
  before=await p.evaluate('JSON.stringify(Store.tour.results)')
  await p.locator('#replayCeremony').click();await p.wait_for_timeout(600)
  index=await p.evaluate("App.finishFlow.plan.beats.findIndex(b=>b.kind==='gc-final')")
  assert index>=0
  await p.locator(f'#ceremonyChapters button[data-beat="{index}"]').click();await p.locator('#ceremonySpeed').select_option('2');await p.wait_for_timeout(6200);await p.locator('#ceremonyPause').click()
  await p.screenshot(path=str(args.out/'tour-gc-podium.png'))
  report['ceremony']=await p.evaluate("({phase:App.finishFlow.phase,paused:App.finishFlow.paused,elapsed:App.finishFlow.elapsed,beats:App.finishFlow.plan.beats.map(b=>b.kind)})")
  await p.set_viewport_size({'width':390,'height':844});await p.wait_for_timeout(350);await p.screenshot(path=str(args.out/'tour-gc-mobile.png'))
  await p.locator('#ceremonySkip').click();await p.locator('#nextStage').click()
  report['archive']=await p.evaluate("({screen:App.screen,stages:Store.tour.results.length,overflow:document.documentElement.scrollWidth-innerWidth})")
  report['unchanged']=before==await p.evaluate('JSON.stringify(Store.tour.results)')
  report['pass']=report['unchanged'] and report['archive']['screen']=='history' and not report['errors']
  await b.close()
 (args.out/'tour-final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 assert report['pass'];print('Tour results, GC podium, mobile awards and archive PASS')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--tour',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);asyncio.run(main(ap.parse_args()))
