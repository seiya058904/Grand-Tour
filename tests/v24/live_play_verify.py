import asyncio,json,hashlib,argparse,sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf8')
ROOT=Path(__file__).resolve().parents[2]
async def main(args):
 out=args.out;out.mkdir(parents=True,exist_ok=True);src=ROOT/'Grand-Tour-V24.html'
 report={'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'mode':'native offline; real wall-clock input/playback at 1x','flows':[],'windows':[],'errors':[]}
 async with async_playwright() as pw:
  b=await pw.chromium.launch(headless=True);c=await b.new_context(viewport={'width':1440,'height':1000},record_video_dir=str(out/'video'),record_video_size={'width':1440,'height':1000});await c.set_offline(True)
  p=await c.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)));p.on('dialog',lambda d:d.accept())
  async def state():return await p.evaluate("({stage:App.race.stageIndex+1,t:App.race.t,player:{v:App.race.player.v,power:App.race.player.power,w:App.race.player.w,grade:App.race.player.grade,ai:App.race.player.aiState},follow:App.race.followState,selected:App.race.selectedWheel,hold:App.race.hold,attacks:App.race.audit.attacks.length,leadouts:App.race.teams.filter(p=>p.objective==='leadout').map(p=>({team:p.teamId,order:p.paceline?.order})),breaks:App.race.groups.filter(g=>g.kind==='BREAKAWAY').map(g=>({count:g.count,front:g.front})),gc:App.race.gcThreat,complete:App.race.complete})")
  for stage in [4,2,15,0]:
   await p.goto(src.as_uri()+'?test');await p.locator('#chooseStage').click();await p.locator(f'button[data-stage="{stage}"]').last.click();await p.locator('#startRace').click();await p.wait_for_timeout(3200)
   first=await state();actions=[]
   if stage!=15:
    wheel=p.locator('#wheelChoices [data-follow]').first
    if await wheel.count() and await wheel.is_visible():
     await wheel.click();await p.wait_for_timeout(1600);selected=await state();assert selected['selected']>=0;actions.append({'named_wheel':selected['selected']})
     await p.locator('#autoWheelButton').click();await p.wait_for_timeout(1100);assert await p.evaluate('App.race.selectedWheel<0&&App.race.hold');actions.append({'Auto':True})
   else:
    await p.locator('[data-effort="1"]').click();actions.append({'ITT_threshold':True});assert await p.locator('#autoWheelButton').is_disabled()
   await p.locator('#attackButton').click();await p.wait_for_timeout(4000);actions.append({'attack':(await state())['player']})
   if await p.locator('#feedButton').is_enabled():await p.locator('#feedButton').click();actions.append({'feed':True})
   await p.locator('#raceGC').click();await p.wait_for_timeout(900);await p.keyboard.press('Escape')
   await p.locator('#pauseButton').click();paused=await p.evaluate('App.race.t');await p.wait_for_timeout(650);assert await p.evaluate('App.race.t')==paused;await p.locator('#resumeRace').click();await p.wait_for_timeout(2600)
   last=await state();assert last['t']>first['t']+4;await p.screenshot(path=str(out/f'played-stage-{stage+1:02}.png'))
   report['flows'].append({'first':first,'last':last,'actions':actions});print('LIVE',stage+1,last['t'],actions,flush=True)
  for name,file in [('breakaway',args.evidence/'breakaway-snapshot.json'),('leadout-sprint',args.evidence/'stage-05-finale-snapshot.json'),('mountain-gc',args.evidence/'gc-battle-snapshot.json'),('ttt-rotation',args.evidence/'stage-01-finale-snapshot.json'),('descent',args.evidence/'descent-snapshot.json')]:
   if not file.exists():raise RuntimeError('Missing real gameplay snapshot '+str(file))
   # These are isolated race snapshots, not complete importable Tour stores.
   # Do not persist them over the test profile's unrelated single-stage runs.
   await p.evaluate('localStorage.clear()');await p.goto(src.as_uri()+'?test');s=json.loads(file.read_text(encoding='utf8'));await p.evaluate('s=>{App.blockStoreWrite=true;initializeRace(Race.restore(s));App.testingFreeze=false}',s)
   first=await state();await p.wait_for_timeout(6000);await p.screenshot(path=str(out/(name+'-motion.png')))
   if name=='mountain-gc' and await p.locator('#attackButton').is_enabled():await p.locator('#attackButton').click()
   await p.wait_for_timeout(7000);last=await state();assert last['t']>first['t']+2 or last['complete'];report['windows'].append({'name':name,'first':first,'last':last});print('WINDOW',name,first['t'],last['t'],flush=True)
  await c.close();await b.close()
 report['pass']=not report['errors'];(out/'live-play.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');assert report['pass']
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--evidence',type=Path,required=True);asyncio.run(main(ap.parse_args()))
