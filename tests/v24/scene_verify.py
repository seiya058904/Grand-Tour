"""Natural scene playback, camera truth, pose continuity and regional contact sheets.

Snapshots are from race-audit.cjs, without injected rider/terrain/weather state.
Only presentation time is sampled in the isolated cyclist geometry sweep.
"""
import argparse,asyncio,hashlib,json,sys
from pathlib import Path
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf8')
ROOT=Path(__file__).resolve().parents[2]
async def main(a):
 a.out.mkdir(parents=True,exist_ok=True);src=ROOT/'Grand-Tour-V24.html'
 report={'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'browser':None,'scenes':[],'errors':[],'pass':False}
 async with async_playwright() as pw:
  b=await pw.chromium.launch(headless=True);report['browser']=b.version
  c=await b.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1);await c.set_offline(True)
  p=await c.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)))
  await p.goto(src.as_uri()+'?test');await p.evaluate('App.testingFreeze=true;App.blockStoreWrite=true;Store.settings.quality="full"')
  for name in ['peloton','breakaway','leadout','sprint','climb','gc-battle','descent','ttt','itt']:
   snap=json.loads((a.scenes/(name+'-snapshot.json')).read_text(encoding='utf8'))
   initial=await p.evaluate('''s=>{
    const r=Race.restore(s);initializeRace(r);App.testingFreeze=true;App.blockStoreWrite=true;r.paused=false;const v=viewFor(r);v.alpha=1;updateHud(true);drawRace();
    const before=JSON.stringify(r.snapshot());for(let i=0;i<12;i++)drawRace();if(before!==JSON.stringify(r.snapshot()))throw Error('render mutated race');
    window.qaMotion={frames:0,maxProjectionError:0,maxLaneStep:0,maxBreathStep:0,maxLensStep:0,stand:0,tuck:0,coast:0,burstRiders:0,burstStand:0};const original=v.update.bind(v);let previous=null;
    v.update=function(t,w,h){const result=original(t,w,h),q=qaMotion,pr=this.riders.get(0);q.frames++;q.stand=Math.max(q.stand,pr.stand);q.tuck=Math.max(q.tuck,pr.tuck);q.coast=Math.max(q.coast,pr.coast);
     if(previous){q.maxLaneStep=Math.max(q.maxLaneStep,Math.abs(pr.z-previous.z));q.maxBreathStep=Math.max(q.maxBreathStep,(pr.breath-previous.breath+Math.PI*2)%(Math.PI*2));q.maxLensStep=Math.max(q.maxLensStep,Math.abs(this.lens-previous.lens));}
     const committed=result.filter(x=>x.r.sprintStarted!==null&&r.t-x.r.sprintStarted<=Physiology.burstDuration(x.r,true)+2&&x.load>1.02);q.burstRiders=Math.max(q.burstRiders,committed.length);for(const x of committed)q.burstStand=Math.max(q.burstStand,x.stand);
     previous={z:pr.z,breath:pr.breath,lens:this.lens};return result;};
    App.testingFreeze=false;return {stage:r.stageIndex+1,seed:r.seed,t:r.t,environment:r.stage.environment,weather:r.conditions.kind,grade:r.player.grade,alt:r.player.alt,pure:true};
   }''',snap)
   await p.wait_for_timeout(2500)
   state=await p.evaluate('''()=>{const r=App.race,v=viewFor(r),q=qaMotion;r.paused=true;
    for(const o of v.drawn)q.maxProjectionError=Math.max(q.maxProjectionError,Math.abs(o.x-(v.projection.anchor+(o.v.world-v.projection.playerX)*v.projection.scaleX)));
    const data={...q,t:r.t,visible:v.drawn.length,grade:r.player.grade,power:r.player.power,lens:v.lens,physicalGroup:r.groups[r.player.groupId]?.count};
    if(q.maxProjectionError>1e-8||q.maxLaneStep>.091||q.maxBreathStep>.211||q.maxLensStep>.08)throw Error('motion discontinuity '+JSON.stringify(data));return data;}''')
   assert state['t']>initial['t'] and state['frames']>5,(name,state)
   await p.screenshot(path=str(a.out/(name+'.png')));report['scenes'].append({'name':name,**initial,**state});print(name,json.dumps(state),flush=True)
  # Actual route/condition identities across all 21 stages, no fabricated slopes.
  await p.set_viewport_size({'width':1440,'height':1000})
  report['regions']=await p.evaluate('''()=>{const out=[];for(let i=0;i<21;i++){const r=new Race(i,0,'single',null,2058765);for(let j=0;j<800;j++)r.tick();const canvas=document.createElement('canvas');canvas.width=720;canvas.height=330;const c=canvas.getContext('2d'),before=JSON.stringify(r.snapshot());
   const ground=x=>230-(x-280)*Math.max(-.085,Math.min(.085,r.player.grade*.72));
   RaceLandscapeV24.backdrop(c,720,330,r.stage,r.player.x,r.conditions.kind,r.player.alt,ground,120);const pixels=canvas.toDataURL();RaceLandscapeV24.backdrop(c,720,330,r.stage,r.player.x,r.conditions.kind,r.player.alt,ground,120);
   if(before!==JSON.stringify(r.snapshot())||pixels!==canvas.toDataURL())throw Error('regional background not pure/deterministic');out.push({stage:i+1,environment:r.stage.environment,weather:r.conditions.kind,pass:true});}return out;}''')
  for stage,name in [(0,'barcelona'),(6,'forest'),(7,'vineyards'),(20,'paris')]:
   await p.evaluate('''i=>{const r=new Race(i,0,'single',null,2058765);for(let j=0;j<800;j++)r.tick();initializeRace(r);App.testingFreeze=true;r.paused=true;viewFor(r).alpha=1;updateHud(true);drawRace();}''',stage)
   await p.screenshot(path=str(a.out/(name+'.png')))
  await p.set_viewport_size({'width':390,'height':844})
  await p.evaluate('drawRace();updateHud(true)');await p.screenshot(path=str(a.out/'mobile-paris.png'))
  await c.close();await b.close()
 report['pass']=not report['errors'];(a.out/'scenes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');assert report['pass']
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--scenes',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);asyncio.run(main(ap.parse_args()))
