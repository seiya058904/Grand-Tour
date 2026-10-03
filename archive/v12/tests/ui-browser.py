"""V12 annotation/interaction acceptance; no simulated rider positions are edited.
Real Chromium + production DOM/Canvas, in-memory Storage adapter because managed
navigation is blocked. Time is frozen ONLY for identical before/after fixtures.
"""
from pathlib import Path
import sys,json,time,traceback,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
from browser_common import *
from playwright.sync_api import sync_playwright
B=Path(__file__).resolve().parent.parent;OUT=B/'evidence';GAME=B/'grand-tour-v12.html';OLD=Path(sys.argv[1]) if len(sys.argv)>1 else None
report={'environment':'Browser plugin absent. Actual Chromium DOM/Canvas in about:blank via explicit memory Storage adapter; browser navigation to localhost is blocked. Fixed production seed, 120 actual engine ticks; no rider relocation, no labels mocked. Tests use true pointer/keyboard/button events.','sha256':hashlib.sha256(GAME.read_bytes()).hexdigest(),'checks':[],'viewports':[],'errors':[]}
def save(): (OUT/'ui-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
def check(name,ok,detail=None):
 report['checks'].append({'name':name,'pass':bool(ok),'detail':detail});print(('PASS ' if ok else 'FAIL ')+name,flush=True);save()
 if not ok: raise AssertionError(name+': '+str(detail))
SETUP="""() => {const T=__TOUR_TEST__;T.start(4);T.App.testingFreeze=true;for(let i=0;i<120;i++)T.App.race.tick();T.updateHud(true);T.drawRace();return {seed:T.App.race.seed,time:T.App.race.t,riders:T.App.race.riders.length};}"""
STATS="""() => {const T=__TOUR_TEST__,v=T.view(),b=v.boxes.filter(x=>x.opacity>.015),rect=document.getElementById('raceCanvas').getBoundingClientRect();let overlaps=0,area=0;for(let i=0;i<b.length;i++)for(let j=i+1;j<b.length;j++){let a=b[i],z=b[j],w=Math.max(0,Math.min(a.x+a.w,z.x+z.w)-Math.max(a.x,z.x)),h=Math.max(0,Math.min(a.y+a.h,z.y+z.h)-Math.max(a.y,z.y));if(w*h>.1){overlaps++;area+=w*h;}}return {canvas:[rect.width,rect.height],labels:b.length,budget:v.stats.labelBudget,overlaps,overlapArea:area,ids:b.map(x=>x.id),boxes:b.map(x=>({id:x.id,x:x.x,y:x.y,w:x.w,h:x.h,opacity:x.opacity})),inspect:v.inspectUntil>performance.now()?v.inspectId:null,pinned:v.pinnedId,focus:document.getElementById('riderFocusPanel')?.innerText,ridersVisible:v.drawn.length,inside:b.every(x=>x.x>=0&&x.y>=0&&x.x+x.w<=rect.width+1&&x.y+x.h<=rect.height+1)};}"""
TARGET="""() => {const T=__TOUR_TEST__,v=T.view(),rect=document.getElementById('raceCanvas').getBoundingClientRect();const list=v.drawn.filter(o=>o.r.id!==0&&o.x>35&&o.x<rect.width-35&&T.App.race.followEligibility(o.r.id).ok).sort((a,b)=>b.x-a.x||b.z-a.z);const o=list[0]||v.drawn.filter(o=>o.r.id!==0&&o.x>35&&o.x<rect.width-35).sort((a,b)=>b.z-a.z)[0];return {id:o.r.id,x:rect.left+o.x+3*o.scale,y:rect.top+o.y-26*o.scale,eligible:T.App.race.followEligibility(o.r.id).ok};}"""
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=BROWSER_EXE,headless=True,args=BROWSER_ARGS)
 # Same production state, not the old coincident-core artificial test fixture.
 # SETUP advances 120 ticks after first draw. Let the initial 2.6s dwell and
 # fades settle before sampling a supposedly unchanged scene; its first legal
 # reprioritization is not periodic churn. Both versions get the same wait.
 if OLD and OLD.exists():
  c=browser.new_context(viewport={'width':1600,'height':1000});p=c.new_page();open_game(p,OLD);report['beforeState']=p.evaluate(SETUP);p.wait_for_timeout(3300)
  before=p.evaluate(STATS);report['before']=before;p.locator('.canvas-wrap').screenshot(path=str(OUT/'labels-before-v11.png'));c.close()
 for width,height in [(1600,1000),(390,844),(320,740)]:
  c=browser.new_context(viewport={'width':width,'height':height});p=c.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)));p.on('console',lambda m:report['errors'].append(m.text) if m.type=='error' else None)
  try:
   open_game(p,GAME);state=p.evaluate(SETUP);p.wait_for_timeout(3300)
   check(f'{width}: correct page, meaningful Canvas, no error overlay','环法' in p.title() and p.locator('#raceScreen').is_visible() and p.locator('#fatalError').is_hidden())
   check(f'{width}: no page horizontal overflow',p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
   samples=[]
   for _ in range(16):samples.append(p.evaluate(STATS));p.wait_for_timeout(90)
   check(f'{width}: hard cap includes fading cards',all(s['labels']<=s['budget'] for s in samples),{'maximum':max(s['labels'] for s in samples),'budget':samples[-1]['budget']})
   check(f'{width}: every label inside canvas and zero pair overlap',all(s['inside'] and s['overlaps']==0 for s in samples))
   check(f'{width}: unchanged scene does not rotate names or slots',len({json.dumps(s['boxes']) for s in samples})==1)
   check(f'{width}: player always retained',all(0 in s['ids'] for s in samples))
   calm=samples[-1];report['viewports'].append({'viewport':[width,height],'productionState':state,'calm':calm})
   p.locator('.canvas-wrap').screenshot(path=str(OUT/f'race-peloton-{width}.png'))
   if width==1600:
    p.screenshot(path=str(OUT/'race-desktop.png'));report['after']=calm
    if 'beforeState' in report:check('Before/after use identical production seed, time and rider count',report['beforeState']==state)
   # Detail mode adds only one slot, not expanded prose on every cyclist.
   p.locator('#labelDensity').select_option('standard');p.wait_for_timeout(500);s=p.evaluate(STATS)
   check(f'{width}: detailed mode still strictly capped',s['labels']<=s['budget'] and s['overlaps']==0,{'labels':s['labels'],'budget':s['budget']})
   # Player-only mode still admits an explicitly hovered rider.
   p.locator('#labelDensity').select_option('player');p.mouse.move(1,1);p.wait_for_timeout(600);check(f'{width}: player-only really has one name',p.evaluate(STATS)['ids']==[0])
   target=p.evaluate(TARGET);p.mouse.move(target['x'],target['y']);p.wait_for_timeout(500);s=p.evaluate(STATS);hit=s['inspect']
   check(f'{width}: actual pointer resolves rider and updates useful details',hit is not None and hit!=0 and p.locator('#riderFocusContent').is_visible() and 'm' in p.locator('#riderFocusDistance').inner_text(),{'pointerTarget':target,'selected':hit,'details':s['focus']})
   check(f'{width}: focused exception is exactly two cards',s['budget']==2 and s['labels']==2 and 0 in s['ids'] and hit in s['ids'])
   seq=[]
   for n in range(20):p.mouse.move(target['x']+(n%3-1)*1.5,target['y']+(n%2)*1.5);p.wait_for_timeout(22);seq.append(p.evaluate(STATS)['inspect'])
   check(f'{width}: 20 small pointer jitters retain same target',all(x==hit for x in seq),seq)
   unchanged=p.evaluate('JSON.stringify(__TOUR_TEST__.App.race.snapshot())')
   p.mouse.click(target['x'],target['y']);p.mouse.move(1,1);p.wait_for_timeout(600)
   check(f'{width}: click pins detail when pointer leaves canvas',p.evaluate(STATS)['inspect']==hit and p.evaluate(STATS)['pinned']==hit)
   p.locator('#raceCanvas').focus();p.keyboard.press('Escape');p.wait_for_timeout(500)
   check(f'{width}: Escape clears pin and focus',p.evaluate(STATS)['inspect'] is None and p.evaluate(STATS)['pinned'] is None)
   # Hover expires, including a stationary pointer that moved to empty canvas.
   p.mouse.move(target['x'],target['y']);p.wait_for_timeout(100);r=p.locator('#raceCanvas').bounding_box();p.mouse.move(r['x']+r['width']-12,r['y']+r['height']-25);p.wait_for_timeout(650)
   check(f'{width}: empty canvas expires hover instead of self-renewing',p.evaluate(STATS)['inspect'] is None)
   check(f'{width}: all annotation interactions leave simulation and RNG unchanged',p.evaluate('JSON.stringify(__TOUR_TEST__.App.race.snapshot())')==unchanged)
   p.locator('#labelDensity').select_option('calm');p.wait_for_timeout(350);target=p.evaluate(TARGET);p.mouse.move(target['x'],target['y']);p.wait_for_timeout(500);hit=p.evaluate(STATS)['inspect']
   p.locator('.canvas-wrap').screenshot(path=str(OUT/f'race-focus-canvas-{width}.png'));p.screenshot(path=str(OUT/f'race-focus-{width}.png'),full_page=width<550)
   # Details rail reaches the existing modal, preserving prior pause state.
   p.locator('#riderFocusDetails').click();check(f'{width}: focus details open real rider modal and pause race',p.locator('#riderBackdrop').is_visible() and p.evaluate('__TOUR_TEST__.App.race.paused'))
   p.locator('[data-close="riderBackdrop"]').click();check(f'{width}: closing details resumes previous running state',not p.evaluate('__TOUR_TEST__.App.race.paused'))
   # Use a real enabled follow control; no direct call to requestWheel.
   p.locator('#riderFocusClear').click();p.mouse.move(1,1);p.wait_for_timeout(500)
   btn=p.locator('#riderActionLayer [data-follow]:not(:disabled)').first
   if btn.count()==0:
    # Explicitly focus a valid wheel to place its accessible button in the cap.
    target=p.evaluate(TARGET);p.mouse.move(target['x'],target['y']);p.wait_for_timeout(500);btn=p.locator('#riderActionLayer [data-follow]:not(:disabled)').first
   check(f'{width}: at least one valid wheel action remains reachable',btn.count()>0)
   ident=int(btn.get_attribute('data-follow'));btn.click();p.wait_for_timeout(250)
   check(f'{width}: label arrow sets real selectedWheel',p.evaluate('__TOUR_TEST__.App.race.selectedWheel')==ident and p.locator(f'#riderActionLayer [data-follow="{ident}"]').get_attribute('aria-pressed')=='true')
   check(f'{width}: focused transition never breaks cap or collision rule',(lambda s:s['labels']<=s['budget'] and s['overlaps']==0)(p.evaluate(STATS)))
  except Exception:
   report['checks'].append({'name':f'{width}: execution','pass':False,'error':traceback.format_exc()});print(traceback.format_exc(),flush=True);save()
  c.close()
 # Touch events on a genuinely touch-enabled narrow viewport.
 c=browser.new_context(viewport={'width':390,'height':844},has_touch=True);p=c.new_page()
 try:
  open_game(p,GAME);p.evaluate(SETUP);p.wait_for_timeout(600);t=p.evaluate(TARGET);p.touchscreen.tap(t['x'],t['y']);p.wait_for_timeout(500);s=p.evaluate(STATS)
  check('390 touch: tap pins a rider without a stale synthetic hover',s['inspect'] is not None and s['pinned']==s['inspect'] and p.evaluate('__TOUR_TEST__.view().pointer===null'))
 except Exception:report['checks'].append({'name':'touch execution','pass':False,'error':traceback.format_exc()})
 c.close()
 # Normal entry, no exposed test API, no opt-in testing helpers.
 c=browser.new_context(viewport={'width':1280,'height':900});p=c.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)))
 try:
  open_game(p,GAME,test=False);check('Production build exposes no test API',p.evaluate('typeof __TOUR_TEST__')=='undefined');p.locator('#chooseStage').click();p.locator('#stageRows [data-stage="4"]').click();p.locator('#startRace').click();p.wait_for_timeout(1800)
  check('Production home → choose stage → preparation → running race works',p.locator('#raceScreen').is_visible() and p.locator('#fatalError').is_hidden());p.screenshot(path=str(OUT/'production-race.png'))
 except Exception:report['checks'].append({'name':'production execution','pass':False,'error':traceback.format_exc()})
 c.close();browser.close()
check('No application console errors or uncaught exceptions',not report['errors'],report['errors']);report['passed']=sum(x['pass'] for x in report['checks']);report['failed']=sum(not x['pass'] for x in report['checks']);save();print('RESULT',report['passed'],'PASS',report['failed'],'FAIL');sys.exit(1 if report['failed'] else 0)
