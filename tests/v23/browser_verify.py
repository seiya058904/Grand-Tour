#!/usr/bin/env python3
"""Run the canonical HTML, never a duplicate engine.
Requires Python 3.10+, Playwright and Chromium. Example:
 python tests/browser_verify.py --injected --out /tmp/grand-tour-qa
Omit --injected to use native file://. Injected mode is ONLY an environment
fallback: exact HTML + TEST-ONLY in-memory Storage, not browser persistence QA.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, shutil, statistics
from pathlib import Path
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]
STORAGE="""()=>{const d=new Map();Object.defineProperty(window,'localStorage',{value:{getItem:k=>d.has(String(k))?d.get(String(k)):null,setItem:(k,v)=>d.set(String(k),String(v)),removeItem:k=>d.delete(String(k)),clear:()=>d.clear(),key:i=>[...d.keys()][i]??null,get length(){return d.size}},configurable:true})}"""
STEP="""count=>{const r=qaRace;for(let i=0;i<count&&!r.complete;i++){
 const active=r.riders.filter(isRacing);r.tick();for(const p of active)if(p.status==='FINISHED')qaCrossings.push({id:p.id,t:r.t,power:p.power,cp:Physics.sustainable(p),energy:p.energy,w:p.w/p.d.wCapacity,sprintStarted:p.sprintStarted,ai:p.aiState});
 if(r.stepCount%100===0){const p=r.player,q=r.teams[p.d.teamId].relay,live=q?.order.map(id=>r.riders[id]).filter(isRacing)||[];qaSamples.push({t:r.t,x:p.x,power:p.power,energy:p.energy,w:p.w/p.d.wCapacity,grade:p.grade,groups:r.groups.length,rank:p.rank,ai:p.aiState,front:p.frontId,draft:p.draft,follow:r.followState,ttt:live.length?{count:live.length,returning:q.returning.length,pairs:live.slice(1).map((p,i)=>({gap:live[i].x-p.x,lateral:Math.abs(live[i].drawLane-p.drawLane)}))}:null});}
 if(r.player.grade>.04&&!qaShots.climb)qaShots.climb=r.snapshot();
 const first=r.order.find(isRacing);if(first&&r.stage.length-first.x<200&&!qaShots.finale)qaShots.finale=r.snapshot();
 if(r.t>=40&&!qaShots.early)qaShots.early=r.snapshot();
 }return{t:r.t,complete:r.complete,finished:r.finishedCount,exited:r.removedCount}}"""

async def main(args):
 out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
 report={'sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'mode':'exact-html-injection-memory-storage' if args.injected else 'native-file','checks':{},'stages':{},'errors':[],'screenshots':[]}
 def check(name,data):
  report['checks'][name]=data;print(name,json.dumps(data,ensure_ascii=False)[:1200],flush=True)
 async with async_playwright() as pw:
  exe=args.chromium or shutil.which('chromium')
  browser=await pw.chromium.launch(**({'executable_path':exe} if exe else {}),headless=True,args=['--no-sandbox'])
  async def load(w=1440,h=1000,reduce=False,source=None):
   ctx=await browser.new_context(viewport={'width':w,'height':h},device_scale_factor=1,reduced_motion='reduce' if reduce else 'no-preference')
   p=await ctx.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)))
   if args.injected:
    await p.goto('about:blank?test');await p.evaluate(STORAGE);await p.set_content((source or args.source).read_text(encoding='utf-8'),wait_until='load')
   else:await p.goto((source or args.source).as_uri()+'?test',wait_until='load')
   await p.evaluate("App.testingFreeze=true;window.stableJSON=o=>JSON.stringify(o,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v)");return ctx,p
  async def shot(p,name):
   await p.wait_for_timeout(650);await p.screenshot(path=str(out/name));report['screenshots'].append(name)
  ctx,p=await load()
  check('identity',await p.evaluate("({title:document.title,build:document.documentElement.dataset.build,internal:CONFIG.buildVersion,fatal:!document.querySelector('#fatalError').hidden})"))
  check('profiles',await p.evaluate("""()=>{let cases=0;for(const s of STAGE_DATA)for(const w of [320,390,768,1440]){const g=profileGeometryV181(w,150,s,true);for(const d of [-100,0,s.length*.5,s.length,s.length+100,NaN]){const q=profilePositionV181(g,s,d);if(!Number.isFinite(q.x+q.y)||q.x<g.dataLeft||q.x>g.dataRight)throw Error('profile bounds');cases++;}}return{stages:STAGE_DATA.length,cases,pass:true}}"""))
  check('rig',await p.evaluate("""()=>{let cases=0,limb=0,spine=0;for(let k=0;k<128;k++)for(const stand of [0,.5,1])for(const tuck of [0,1])for(const climb of [0,1])for(const celebrate of [0,1]){const q=CyclistRigV21.pose(k*Math.PI/64,{stand,tuck,climb,celebrate,sprint:stand,surge:1,fatigueDrop:1});spine=Math.max(spine,Math.abs(Math.hypot(q.shoulder[0]-q.hip[0],q.shoulder[1]-q.hip[1])-25.2));for(const l of q.legs){limb=Math.max(limb,Math.abs(Math.hypot(l.knee[0]-q.hip[0],l.knee[1]-q.hip[1])-24.8),Math.abs(Math.hypot(l.knee[0]-l.ankle[0],l.knee[1]-l.ankle[1])-24.4));cases++;}}if(!Number.isFinite(limb)||limb>1e-8||spine>1e-8)throw Error('rig');return{cases,limbError:limb,spineError:spine,pass:true}}"""))
  starts=[]
  for stage in range(21):
   starts.append(await p.evaluate("""stage=>{const r=new Race(stage,0,'single',null,seedForStage(2026001,stage));for(let i=0;i<100;i++)r.tick();for(const p of r.riders)if(![p.x,p.v,p.power,p.energy,p.w,p.drawLane].every(Number.isFinite)||p.energy<0||p.energy>100.0001||p.w<-.0001||p.w>p.d.wCapacity+.001)throw Error('invalid state');return{stage:stage+1,type:r.stage.type,t:r.t,pass:true}}""",stage))
  check('all_stage_starts',starts)
  check('restore_determinism',await p.evaluate("""()=>{const a=new Race(4,0,'tour',null,123456),b=new Race(4,0,'tour',null,123456);for(let i=0;i<500;i++){a.tick();b.tick();}const repeat=stableJSON(a.snapshot())===stableJSON(b.snapshot()),c=Race.restore(a.snapshot());for(let i=0;i<400;i++){a.tick();c.tick();}const resume=stableJSON(a.snapshot())===stableJSON(c.snapshot());let reject=false;const bad=a.snapshot();bad.rngState=0;try{Race.restore(bad)}catch(e){reject=true}if(!repeat||!resume||!reject)throw Error('restore');return{repeat,resume,reject,pass:true,ticks:900}}"""))
  check('render_purity',await p.evaluate("""()=>{const r=new Race(4,0,'single',null,2058765);for(let i=0;i<800;i++)r.tick();initializeRace(r);r.paused=true;viewFor(r).alpha=1;const before=JSON.stringify(r.snapshot()),raw=JSON.stringify(r.riders);for(let i=0;i<40;i++)drawRace();const v=viewFor(r);let error=0;for(const o of v.drawn)error=Math.max(error,Math.abs(o.x-(v.projection.anchor+(o.v.world-v.projection.playerX)*v.projection.scaleX)));const pure=before===JSON.stringify(r.snapshot())&&raw===JSON.stringify(r.riders);if(!pure||error>1e-9)throw Error('render purity');return{pure,projectionError:error,frames:40,visible:v.drawn.length,pass:true}}"""))
  await shot(p,'desktop-peloton.png')
  await p.evaluate('App.race.paused=false');await p.locator('#attackButton').click()
  check('attack_control',await p.evaluate("""()=>{const r=App.race;for(let i=0;i<50;i++)r.tick();updateHud(true);drawRace();if(r.player.attackUntil<=r.t||r.player.power<=Physics.sustainable(r.player))throw Error('attack input');r.paused=true;return{power:r.player.power,cp:Physics.sustainable(r.player),ai:r.player.aiState,pass:true}}"""))
  for stage in [4,0,15,2]:
   setup=await p.evaluate("""stage=>{App.testingFreeze=true;window.qaRace=new Race(stage,0,'single',null,seedForStage(2026001,stage));window.qaCrossings=[];window.qaSamples=[];window.qaShots={};return{type:qaRace.stage.type,seed:qaRace.seed,length:qaRace.stage.length}}""",stage)
   for chunk in range(60):
    state=await p.evaluate(STEP,1500);print('stage',stage+1,state,flush=True)
    if state['complete']:break
   if not state['complete']:raise RuntimeError('stage timeout')
   result=await p.evaluate("""()=>({crossings:qaCrossings,samples:qaSamples,attacks:qaRace.audit.attacks,rotations:qaRace.audit.rotations,record:qaRace.result()})""")
   (out/f'stage-{stage+1:02}-physical.json').write_text(json.dumps(result,ensure_ascii=False,indent=2), encoding='utf-8')
   report['stages'][str(stage+1)]={**setup,**state,'rotations':len(result['rotations']),'top10Watts':statistics.mean(x['power'] for x in result['crossings'][:10]),'top10PowerCp':statistics.mean(x['power']/x['cp'] for x in result['crossings'][:10]),'invariantFailures':result['record'].get('audit',{}).get('invariantFailures',[])}
   for label in (['early','finale'] if stage in [4,0] else ['climb' if stage==2 else 'early']):
    snap=await p.evaluate('qaShots.'+label)
    if not snap:continue
    # Replay a real run: only the unsupported single-stage *save mode* is
    # adapted to tour. Rider positions, power, reserves and results unchanged.
    snap['mode']='tour';(out/f'stage-{stage+1:02}-{label}-snapshot.json').write_text(json.dumps(snap,ensure_ascii=False), encoding='utf-8')
    await p.evaluate("""s=>{const r=Race.restore(s);initializeRace(r);r.paused=true;viewFor(r).alpha=1;updateHud(true);drawRace()}""",snap)
    await shot(p,f'stage-{stage+1:02}-{label}.png')
   if stage==4:
    await p.evaluate('initializeRace(qaRace)');await p.wait_for_timeout(1600)
    check('ceremony',await p.evaluate("({recorded:App.race.recorded,settleCount:App.finishFlow?.settleCount,visible:!document.querySelector('#ceremonyLayer').hidden,pending:!!Store.pendingCeremony})"))
    await shot(p,'ceremony.png');await p.locator('#ceremonySkip').click();await p.wait_for_timeout(600)
    check('results',await p.evaluate("({screen:App.screen,rows:document.querySelectorAll('#resultsRows tr').length,title:document.querySelector('#resultTitle').textContent,pass:App.screen==='results'})"))
    await shot(p,'results.png');await p.locator('#nextStage').click()
    check('next_stage',await p.evaluate("({index:App.prep.index,visible:!document.querySelector('#prepBackdrop').hidden})"))
    await p.evaluate('closeDialogs();App.race=null;App.finishFlow=null;showScreen("home")')
  check('tour_storage_roundtrip',await p.evaluate("""()=>{Store.tour={id:'v23-qa',playerId:0,seedBase:2026001,seedOrigin:'test',timeModel:'race-world-v1',results:[]};initializeRace(new Race(0,0,'tour',null,seedForStage(2026001,0)));for(let i=0;i<300;i++)App.race.tick();const original=App.race;saveActive();if(!JSON.parse(localStorage.getItem(CONFIG.saveKey)).active)throw Error('storage backing');App.race=null;loadStore();continueTour();const restored=App.race;const immediate=original.riders.every((r,i)=>['x','v','power','energy','w','drawLane'].every(k=>r[k]===restored.riders[i][k]))&&original.rng.state===restored.rng.state;for(let i=0;i<200;i++){original.tick();restored.tick();}const equal=stableJSON(SaveCodec.compactSnapshot(original.snapshot()))===stableJSON(SaveCodec.compactSnapshot(restored.snapshot()));if(!equal||!immediate)throw Error('storage roundtrip');return{pass:equal,immediate,continuedTicks:200,t:restored.t}}"""))
  if (ROOT/'Grand-Tour-V22.html').exists():
   bc,bp=await load(source=ROOT/'Grand-Tour-V22.html')
   legacy=await bp.evaluate("""()=>{const r=new Race(4,0,'tour',null,123456);for(let i=0;i<500;i++)r.tick();return r.snapshot()}""")
   check('v22_import',await p.evaluate("""s=>{const r=Race.restore(s);const exact=r.riders.every((p,i)=>p.x===s.riders[i].x&&p.w===s.riders[i].w&&p.energy===s.riders[i].energy)&&r.rng.state===s.rngState;if(!exact)throw Error('legacy');for(let i=0;i<20;i++)r.tick();return{exact,continued:true,pass:true}}""",legacy));await bc.close()
  for reduced in [False,True]:
   mc,mp=await load(390,844,reduced);await mp.locator('#chooseStage').click();await mp.locator('button[data-stage="4"]').click();await mp.locator('#startRace').click()
   await mp.evaluate("""()=>{App.testingFreeze=true;for(let i=0;i<600;i++)App.race.tick();App.race.paused=true;viewFor(App.race).alpha=1;updateHud(true);drawRace()}""")
   suffix='reduced' if reduced else 'mobile'
   check(suffix,await mp.evaluate("""()=>{const overflow=document.documentElement.scrollWidth-document.documentElement.clientWidth,c=document.querySelector('#raceCanvas').getBoundingClientRect();return{overflow,canvas:{x:c.x,y:c.y,width:c.width,height:c.height},reduced:reducedMotion,lens:viewFor(App.race).lens,pass:overflow<=1&&c.width>250&&c.right<=innerWidth}}"""));await shot(mp,suffix+'.png')
   await mp.locator('#raceGC').click();await mp.wait_for_timeout(300)
   check(suffix+'_centre',await mp.evaluate("({visible:!document.querySelector('#mobileDeskBackdrop').hidden,count:document.querySelectorAll('#liveDesk').length,mounted:document.querySelector('#mobileDeskMount').contains(document.querySelector('#liveDesk'))})"));await shot(mp,suffix+'-centre.png');await mc.close()
  await ctx.close();await browser.close()
 report['not_verified']=(['Native file:// and browser-storage persistence across reloads (injected mode only).'] if args.injected else [])+['Physical mobile-device FPS; Safari/Firefox; subjective human audio review.','An uninterrupted human-played 21-stage Tour.']
 report['pass']=not report['errors'] and all(not isinstance(v,dict) or v.get('pass',True) for v in report['checks'].values())
 (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2), encoding='utf-8');print('COMPLETE',report['pass'],flush=True)
 if not report['pass']:raise SystemExit(1)
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,default=ROOT/'Grand-Tour-V23.html');ap.add_argument('--out',default='/tmp/grand-tour-v23-qa');ap.add_argument('--chromium');ap.add_argument('--injected',action='store_true');args=ap.parse_args();args.source=args.source.resolve();asyncio.run(main(args))
