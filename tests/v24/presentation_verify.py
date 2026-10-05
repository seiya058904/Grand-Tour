"""V24 regressions: native offline browser, real controls, interrupted motion,
responsive geometry, contrast, V22 import and browser-process persistence.
No test changes rider positions, power, weather, or results.
"""
import argparse, asyncio, hashlib, json
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]
CONTRAST="""el=>{const s=getComputedStyle(el),nums=c=>c.match(/[\\d.]+/g).slice(0,3).map(Number),lum=c=>nums(c).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0),a=lum(s.color),b=lum(s.backgroundColor);return{color:s.color,background:s.backgroundColor,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)}}"""
WAIT_NATIVE_EXIT="""async backdrop=>{
 const animation=backdrop.hidden?null:InterfaceMotionV22.animations.get(backdrop);
 const state=()=>({hidden:backdrop.hidden,paused:App.race.paused,inert:document.querySelector('.shell').inert,focus:document.activeElement.id,stack:[...App.modalStack],animation:animation?{playState:animation.playState,currentTime:animation.currentTime,startTime:animation.startTime,duration:animation.effect.getTiming().duration}:null});
 if(animation)await new Promise((resolve,reject)=>{
  let deadline;
  const cleanup=()=>{clearTimeout(deadline);animation.removeEventListener('finish',finish);animation.removeEventListener('cancel',cancel);};
  const fail=reason=>{cleanup();reject(Error(reason+' '+JSON.stringify(state())));};
  const finish=()=>{cleanup();resolve();},cancel=()=>fail('close animation cancelled');
  animation.addEventListener('finish',finish);animation.addEventListener('cancel',cancel);
  deadline=setTimeout(()=>fail('close animation did not finish'),500);
 });
 return state();
}"""
async def main(args):
 out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
 report={'source_sha256':hashlib.sha256((ROOT/'Grand-Tour-V24.html').read_bytes()).hexdigest(),'checks':{},'errors':[],'console':[]}
 def check(name,data):
  report['checks'][name]=data
  (out/'presentation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  assert data.get('pass',False),(name,data)
  print(name,'PASS',flush=True)
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  ctx=await browser.new_context(viewport={'width':1440,'height':900},record_video_dir=str(out/'video'),record_video_size={'width':1440,'height':900})
  p=await ctx.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)))
  p.on('console',lambda m:report['console'].append(m.text) if m.type in ['error','warning'] else None)
  await ctx.set_offline(True)
  await p.goto((ROOT/'Grand-Tour-V24.html').as_uri()+'?test')
  await p.evaluate('App.testingFreeze=true')
  await p.evaluate('()=>{window.waitForNativeExit='+WAIT_NATIVE_EXIT+';}')
  check('offline_identity',{'pass':await p.title()=='环法 · Grand Tour V24 · 公路自行车竞赛游戏' and await p.locator('#newTour').is_visible()})
  await p.locator('#chooseStage').click();await p.locator('button[data-stage="4"]').click()
  await p.wait_for_timeout(300);await p.screenshot(path=str(out/'preparation.png'))
  await p.locator('#startRace').click()
  await p.evaluate('for(let i=0;i<800;i++)App.race.tick();updateHud(true);drawRace()')
  for name in ['normal','normal-hover','attacking','attacking-hover','cancelled']:
   b=p.locator('#attackButton')
   if name=='attacking':await b.click();await p.evaluate('for(let i=0;i<40;i++)App.race.tick();updateHud(true)')
   if name=='cancelled':await b.click();await p.evaluate('for(let i=0;i<700;i++)App.race.tick();updateHud(true)')
   if 'hover' in name:await b.hover()
   else:await p.mouse.move(0,0)
   await p.wait_for_timeout(180);c=await b.evaluate(CONTRAST);check('contrast-'+name,{**c,'pass':c['ratio']>=4.5})
  # Capture both sides of the exit, then interrupt closing with an immediate reopen.
  await p.locator('#pauseButton').click();await p.wait_for_timeout(300)
  check('pause_clock',await p.evaluate("({pass:App.race.paused,owner:App.modalOwner})"))
  await p.locator('#resumeRace').click()
  check('close_focus',await p.evaluate("""async()=>{const state=await waitForNativeExit($('pauseBackdrop'));return{...state,pass:state.hidden&&!state.paused&&state.focus==='pauseButton'}}"""))
  check('interrupted_exit',await p.evaluate("""async()=>{
   for(let i=0;i<5;i++){openDialog('pauseBackdrop');closeDialog('pauseBackdrop');openDialog('pauseBackdrop');await new Promise(r=>setTimeout(r,160));if($('pauseBackdrop').hidden||!App.race.paused||App.modalStack.length!==1)throw Error('stale close');closeDialog('pauseBackdrop');}
   const backdrop=$('pauseBackdrop'),shell=document.querySelector('.shell');
   if(App.race.paused||shell.inert||App.modalStack.length)throw Error('close retained modal state');
   const state=await waitForNativeExit(backdrop);
   return{...state,pass:state.hidden&&!state.paused&&!state.inert};
  }"""))
  await p.locator('#pauseButton').click();await p.locator('#pauseHelp').click();await p.keyboard.press('Escape');await p.wait_for_timeout(180)
  check('nested_modal',await p.evaluate("({pass:App.race.paused&&App.modalStack.join()==='pauseBackdrop'&&document.activeElement.id==='pauseHelp'})"))
  await p.keyboard.press('Escape');await p.wait_for_timeout(200)
  await p.locator('[data-area="course"]').click();await p.locator('[data-area="live"]').click()
  await p.evaluate('window.scrollTo(0,0)')
  for width,height in [(1440,900),(1280,720),(1024,768),(768,900),(390,844),(320,740)]:
   await p.set_viewport_size({'width':width,'height':height});await p.wait_for_timeout(350)
   await p.evaluate('updateHud(true);drawRace();window.scrollTo(0,0)')
   geometry=await p.evaluate("""()=>{const labels=[...document.querySelectorAll('.metrics .metric-label')].map(e=>e.getBoundingClientRect()),bad=labels.some((a,i)=>labels.some((b,j)=>i<j&&a.left<b.right-1&&a.right>b.left+1&&a.top<b.bottom-1&&a.bottom>b.top+1));const buttons=[...document.querySelectorAll('#effortButtons button,.action-row button')].map(e=>e.getBoundingClientRect());return{overflow:document.documentElement.scrollWidth-innerWidth,labelOverlap:bad,controlsBottom:Math.max(...buttons.map(b=>b.bottom)),pass:!bad&&document.documentElement.scrollWidth<=innerWidth+1&&buttons.every(b=>b.width>=44&&b.height>=40)}}""")
   check('layout-'+str(width),geometry)
   await p.screenshot(path=str(out/f'race-{width}.png'))
   if width==390:
    await p.locator('#raceGC').click();await p.wait_for_timeout(300)
    check('live_mobile_centre',await p.evaluate("({pass:!App.race.paused&&$('mobileDeskMount').contains($('liveDesk'))&&document.querySelectorAll('#liveDesk').length===1})"))
    await p.keyboard.press('Escape');await p.wait_for_timeout(180)
  await p.emulate_media(reduced_motion='reduce');await p.reload();await p.evaluate('App.testingFreeze=true')
  await p.locator('#chooseStage').click();await p.locator('button[data-stage="4"]').click()
  check('reduced_motion',await p.evaluate("({pass:reducedMotion&&$('prepBackdrop').getAnimations().length===0&&$('prepBackdrop').querySelector('.dialog').getAnimations().length===0})"))
  await p.keyboard.press('Escape');check('reduced_exit',{'pass':await p.locator('#prepBackdrop').is_hidden()})
  # Import a V22 save through the same file control available to the player.
  old=await browser.new_page();await old.goto((ROOT/'archive/v22/Grand-Tour-V22.html').as_uri()+'?test')
  legacy=await old.evaluate("""()=>{App.testingFreeze=true;Store.tour={id:'v22-native-qa',playerId:0,seedBase:2026001,seedOrigin:'test',timeModel:'race-world-v1',results:[]};initializeRace(new Race(0,0,'tour',null,2026001));for(let i=0;i<500;i++)App.race.tick();saveActive();return{data:localStorage.getItem(CONFIG.saveKey),physical:JSON.stringify(App.race.riders.map(r=>[r.x,r.v,r.power,r.energy,r.w])),t:App.race.t}}""")
  await old.close();p.on('dialog',lambda d:d.accept())
  await p.locator('#saveFile').set_input_files({'name':'v22-save.json','mimeType':'application/json','buffer':legacy['data'].encode()})
  await p.wait_for_function("Store.tour?.id==='v22-native-qa'");await p.locator('#continueTour').click()
  check('v22_file_import',await p.evaluate("""s=>({pass:App.race.t===s.t&&JSON.stringify(App.race.riders.map(r=>[r.x,r.v,r.power,r.energy,r.w]))===s.physical})""",legacy))
  await ctx.close();await browser.close()
  # A fresh on-disk profile owned by this test, never the user's browser profile.
  profile=out/'profile';persistent=await pw.chromium.launch_persistent_context(str(profile),headless=True)
  q=await persistent.new_page();await q.goto((ROOT/'Grand-Tour-V24.html').as_uri()+'?test');await q.evaluate('App.testingFreeze=true')
  q.on('dialog',lambda d:d.accept());await q.locator('#saveFile').set_input_files({'name':'v22-save.json','mimeType':'application/json','buffer':legacy['data'].encode()})
  await q.wait_for_function("Store.tour?.id==='v22-native-qa'");await persistent.close()
  persistent=await pw.chromium.launch_persistent_context(str(profile),headless=True)
  q=await persistent.new_page();await q.goto((ROOT/'Grand-Tour-V24.html').as_uri()+'?test');await q.evaluate('App.testingFreeze=true');await q.locator('#continueTour').click()
  check('process_restart_persistence',await q.evaluate("""s=>({pass:App.race.t===s.t&&JSON.stringify(App.race.riders.map(r=>[r.x,r.v,r.power,r.energy,r.w]))===s.physical,t:App.race.t})""",legacy))
  await persistent.close()
 report['pass']=not report['errors'] and not report['console'];check('console',{'pass':report['pass'],'errors':report['errors'],'warnings':report['console']})
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);asyncio.run(main(ap.parse_args()))
