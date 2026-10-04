"""GT-01: real production file import, backup protection, settlement and reload.
Uses fresh browser contexts and the normal UI; only simulation waiting is accelerated.
"""
import argparse, asyncio, hashlib, json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[2]

async def main(args):
 args.out.mkdir(parents=True,exist_ok=True)
 report={'source':str(args.source),'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'production_query':True,'cases':[],'errors':[],'console':[],'network':[],'pass':False}
 try:
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(headless=True)
   report['browser']=browser.version
   try:
    for width,height in [(1440,1000),(390,844)]:
     context=await browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
     try:
      page=await context.new_page();dialogs=[]
      page.on('pageerror',lambda e:report['errors'].append(str(e)))
      page.on('console',lambda m:report['console'].append(m.text) if m.type in ['error','warning'] else None)
      page.on('request',lambda r:report['network'].append(r.url) if r.url.startswith(('https:','http:')) else None)
      async def accept(dialog):dialogs.append(dialog.message);await dialog.accept()
      page.on('dialog',accept)
      await context.set_offline(True)
      await page.goto(args.source.as_uri())
      assert await page.evaluate('TEST_MODE') is False
      await page.evaluate('App.testingFreeze=true')
      await page.locator('#newTour').click();await page.evaluate('App.prep.seedBase=314159')
      await page.locator('#startRace').click()
      state=await page.evaluate("""()=>{const r=App.race;while(!r.finishedCount&&r.t<4000)r.tick();if(!r.finishedCount)throw Error('first finish timeout');return{t:r.t,finished:r.finishedCount,first:r.riders.find(x=>x.status==='FINISHED').id}}""")
      await page.locator('#pauseButton').click();await page.locator('#saveAndHome').click()
      await page.wait_for_function("App.screen==='home'");await page.evaluate('saveQueue')
      raw=await page.evaluate('localStorage.getItem(CONFIG.saveKey)')
      valid=json.loads(raw);valid['tour']['id']='browser-finish-valid'
      await page.evaluate("localStorage.setItem(CONFIG.saveKey+'-before-import','preexisting-import-backup');localStorage.setItem(CONFIG.saveKey+'-recovery-backup','preexisting-recovery-backup')")
      case={'width':width,'height':height,'natural':state,'rejected':[]};report['cases'].append(case)
      for field in ['finishedTime','finishRaceTime']:
       corrupt=json.loads(json.dumps(valid));corrupt['tour']['id']='browser-finish-invalid';corrupt['active']['riders'][state['first']][field]=None
       await page.evaluate("$('toast').textContent=''")
       count=len(dialogs)
       await page.locator('#saveFile').set_input_files({'name':'invalid-'+field+'.json','mimeType':'application/json','buffer':json.dumps(corrupt).encode()})
       await page.wait_for_function("$('toast').textContent.length>0")
       toast=await page.locator('#toast').inner_text()
       await page.screenshot(path=str(args.out/f'rejected-{field}-{width}.png'))
       assert toast.startswith('导入未完成：'),toast
       protected=await page.evaluate("""raw=>({canonical:localStorage.getItem(CONFIG.saveKey)===raw,importBackup:localStorage.getItem(CONFIG.saveKey+'-before-import')==='preexisting-import-backup',recoveryBackup:localStorage.getItem(CONFIG.saveKey+'-recovery-backup')==='preexisting-recovery-backup'})""",raw)
       assert all(protected.values()),protected
       assert len(dialogs)==count,'invalid file must be rejected before confirmation and backup writes'
       case['rejected'].append({'field':field,'toast':toast,'protected':protected,'confirmationDialogs':0})
      await page.locator('#saveFile').set_input_files({'name':'valid-finish.json','mimeType':'application/json','buffer':json.dumps(valid).encode()})
      await page.wait_for_function("Store.tour?.id==='browser-finish-valid'")
      assert await page.evaluate('raw=>localStorage.getItem(CONFIG.saveKey+"-before-import")===raw',raw)
      await page.locator('#continueTour').click()
      assert await page.evaluate('App.race.t')==state['t']
      await page.evaluate("async()=>{while(!App.race.complete&&App.race.t<4000)App.race.tick();if(!App.race.complete)throw Error('stage timeout');await finalizeRace()}")
      await page.wait_for_function("App.finishFlow?.phase==='ceremony'",timeout=60000)
      await page.locator('#ceremonySkip').click();await page.wait_for_function("App.screen==='results'")
      settled=await page.evaluate("""()=>{const data=JSON.parse(localStorage.getItem(CONFIG.saveKey)),decoded=SaveCodec.decode(data);return{results:data.tour.results.length,active:data.active,issues:decoded.issues,validTimes:data.tour.results[0].simTimes.every((t,i)=>data.tour.results[0].statuses[i]==='FINISHED'?Number.isFinite(t)&&t>0:t===null)}}""")
      assert settled['results']==1 and settled['active'] is None and not settled['issues'] and settled['validTimes'],settled
      await page.screenshot(path=str(args.out/f'settled-{width}.png'))
      await page.reload();await page.evaluate('App.testingFreeze=true')
      after=await page.evaluate("({results:Store.tour.results.length,active:Store.active,warningVisible:!$('storageWarning').hidden,recoveryBackup:localStorage.getItem(CONFIG.saveKey+'-recovery-backup')})")
      assert after['results']==1 and after['active'] is None and not after['warningVisible'],after
      assert after['recoveryBackup']=='preexisting-recovery-backup'
      # A normal next-stage start proves the retained result remains playable.
      await page.locator('#continueTour').click()
      if await page.locator('#startRace').is_visible():await page.locator('#startRace').click()
      await page.wait_for_function('App.race?.stageIndex===1')
      await page.evaluate('for(let i=0;i<20;i++)App.race.tick();updateHud(true);drawRace()')
      await page.screenshot(path=str(args.out/f'resumed-stage2-{width}.png'))
      case.update({'settled':settled,'afterReload':after,'continuedStage':2,'pass':True})
     finally:await context.close()
   finally:await browser.close()
  assert not report['errors'] and not report['console'] and not report['network'],report
  report['pass']=True
 except Exception as e:
  report['failure']=str(e);raise
 finally:(args.out/'save-finish-browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--source',type=Path,default=ROOT/'Grand-Tour-V24.html');parser.add_argument('--out',type=Path,required=True)
 args=parser.parse_args();args.source=args.source.resolve();asyncio.run(main(args))
