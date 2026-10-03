"""Native offline award playback, geometry, transport and responsive checks.

Records come from real engine runs; only presentation time is sampled for the
geometry sweep. --play additionally watches every award at normal speed.
"""
import argparse,asyncio,json,hashlib
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]
GEOMETRY=r"""()=>{
 const f=App.finishFlow,canvas=document.createElement('canvas'),c=canvas.getContext('2d');
 const out={samples:0,limbError:0,plantedError:0,handError:0,staffError:0,details:[]};
 for(const width of [1280,390,320]){
  const m=CeremonyStage.metrics(width,width<550?width*1.125:width*9/16,f.plan.final);
  for(const b of f.plan.beats){if(['arrival','complete'].includes(b.kind))continue;
   const q=CeremonyStage.cue(b);
   for(let age=.05;age<b.seconds;age+=.11){
    const scene=CeremonyStage.scene(f.plan,b.start+age,m),results={};
    for(const a of [...scene.actors,...(scene.staff?[scene.staff]:[])]){
     const result=CeremonyStage.person(c,a,b.start+age,age,a.walking,a.alpha);results[a.role==='presenter'?'staff':a.id]=result;
     if(!result)continue;out.samples++;
     for(const limb of result.limbs){const A=Math.hypot(limb.joint[0]-limb.a[0],limb.joint[1]-limb.a[1],limb.depth||0),B=Math.hypot(limb.b[0]-limb.joint[0],limb.b[1]-limb.joint[1],(limb.handDepth||0)-(limb.depth||0));out.limbError=Math.max(out.limbError,Math.abs(A-limb.lengths[0]),Math.abs(B-limb.lengths[1]));}
     for(const foot of a.feet||[])if(foot.plant)out.plantedError=Math.max(out.plantedError,Math.abs(foot.world[1]+3*a.height/180-foot.surface));
    }
    const p=scene.prop,actor=scene.actors[0];
    if(p&&p.owner==='rider'&&age<q.exit-.8){
     const rr=results[p.id],hand=p.side?rr.right:rr.left,g=p.grips[p.side];
     const error=Math.hypot(hand[0]-g[0],hand[1]-g[1]);
     if(error>out.handError){out.handError=error;out.details[0]={width,kind:b.kind,age,error};}
     if(p.twoHand){const other=1-p.side,h=other?rr.right:rr.left,target=p.grips[other],e=Math.hypot(h[0]-target[0],h[1]-target[1]);if(e>out.handError){out.handError=e;out.details[0]={width,kind:b.kind,age,error:e,other:true};}}
    }
    if(p?.shared&&results.staff){const hand=p.staffHand?results.staff.right:results.staff.left,g=p.grips[b.kind==='gc-final'?1:0],error=Math.hypot(hand[0]-g[0],hand[1]-g[1]);if(error>out.staffError){out.staffError=error;out.details[1]={width,kind:b.kind,age,error};}}
   }
  }
 }
 return out;
}"""
async def main(args):
 out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
 source=ROOT/'archive/v23/Grand-Tour-V23.html'
 report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'tour':str(args.tour),'errors':[],'console':[],'checks':{},'screenshots':[]}
 def check(name,data):
  report['checks'][name]=data
  (out/'sequence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
  print(name,json.dumps(data,ensure_ascii=False)[:1000],flush=True)
  assert data.get('pass',True),(name,data)
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  options={'viewport':{'width':1440,'height':1000},'device_scale_factor':1}
  if args.play:options.update(record_video_dir=str(out/'video'),record_video_size={'width':1440,'height':1000})
  ctx=await browser.new_context(**options);await ctx.set_offline(True)
  p=await ctx.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)));p.on('console',lambda m:report['console'].append(m.text) if m.type in ['error','warning'] else None);p.on('dialog',lambda d:d.accept())
  await p.goto(source.as_uri()+'?test');await p.evaluate('App.testingFreeze=true')
  async def shot(name):
   await p.screenshot(path=str(out/name));report['screenshots'].append(name)
  async def sample(kind,age,name):
   index=await p.evaluate("""({kind,age})=>{const f=App.finishFlow,b=f.plan.beats.find(b=>b.kind===kind);f.paused=true;f.elapsed=b.start+age;CeremonyPlayer.update(f);Ceremony.draw(f);return f.plan.beats.indexOf(b)}""",{'kind':kind,'age':age})
   assert await p.locator('.ceremony-chapter[aria-current="step"]').get_attribute('data-beat')==str(index)
   await p.wait_for_timeout(220) # Let the existing chapter colour transition finish before capture.
   await shot(name)
  async def replay():
   await p.locator('#replayCeremony').click();await p.locator('#ceremonyPause').click()
  record=json.loads(args.record.read_text(encoding='utf8'))['record']
  await p.evaluate("""r=>{App.race=null;App.result=normalizeRecord(r,r.stage,null);App.resultMode='single';showResults(true)}""",record)
  before=await p.evaluate('JSON.stringify(App.result)');await replay()
  geometry=await p.evaluate(GEOMETRY);check('stage_geometry',{**geometry,'pass':geometry['limbError']<1e-6 and geometry['plantedError']<1e-6 and geometry['handError']<2.2 and geometry['staffError']<2.2})
  for kind,age in [('winner',7.75),('winner',13.4),('green',13.4),('polka',13.4),('white',13.4),('yellow',13.4)]:
   if await p.evaluate('kind=>App.finishFlow.plan.beats.some(b=>b.kind===kind)',kind):await sample(kind,age,'stage-'+kind+'-'+str(age)+'.png')
  if args.play:
   await p.locator('[data-beat="0"]').click();await p.locator('#ceremonySpeed').select_option('1');await p.locator('#ceremonyPause').click()
   duration=await p.evaluate('App.finishFlow.plan.duration')
   await p.wait_for_function('!App.finishFlow',timeout=int(duration*1100+20000));check('whole_stage_playback',{'pass':await p.evaluate('App.screen==="results"'),'seconds':duration,'rate':1})
  else:await p.locator('#ceremonySkip').click()
  check('stage_ledger_unchanged',{'pass':before==await p.evaluate('JSON.stringify(App.result)')})
  ttt=json.loads((args.record.parent/'stage-01-physical.json').read_text(encoding='utf8'))['record']
  await p.evaluate("""r=>{App.race=null;App.result=normalizeRecord(r,r.stage,null);App.resultMode='single';showResults(true)}""",ttt)
  await replay();geometry=await p.evaluate(GEOMETRY)
  check('ttt_geometry',{**geometry,'pass':geometry['limbError']<1e-6 and geometry['plantedError']<1e-6 and geometry['handError']<2.2 and geometry['staffError']<2.2})
  await sample('team-stage',11,'ttt-team-stage.png')
  if args.play:
   index=await p.evaluate('App.finishFlow.plan.beats.findIndex(b=>b.kind==="team-stage")');await p.locator(f'[data-beat="{index}"]').click();await p.locator('#ceremonyPause').click()
   await p.wait_for_function('App.finishFlow.elapsed>App.finishFlow.plan.beats.find(b=>b.kind==="team-stage").end+.2',timeout=35000)
   check('ttt_team_playback',{'pass':True,'rate':1})
  await p.locator('#ceremonySkip').click()
  # The complete tour is imported using the actual product's file control.
  await p.locator('#saveFile').set_input_files(str(args.tour.resolve()));await p.wait_for_function('Store.tour?.results.length===21');await p.locator('#continueTour').click()
  # User-reported venue: retain V22's detailed wall and wear each awarded jersey.
  await p.locator('#nextStage').click();await p.locator('[data-archive-detail="17"]').click();await replay()
  outfits=[]
  for kind in ['yellow','green','polka','white']:
   await sample(kind,13.4,'stage-18-'+kind+'.png')
   outfits.append(await p.evaluate("""kind=>{const f=App.finishFlow,m=CeremonyStage.metrics(1280,720),scene=CeremonyStage.scene(f.plan,f.elapsed,m);return {kind,worn:scene.actors[0].jersey,prop:scene.prop.type,pass:scene.actors[0].jersey===kind&&scene.prop.type==='flowers'}}""",kind))
  check('four_jerseys_worn',{'pass':all(x['pass'] for x in outfits),'outfits':outfits})
  await p.set_viewport_size({'width':390,'height':844});await sample('white',13.4,'stage-18-white-mobile.png');await p.set_viewport_size({'width':1440,'height':1000})
  await p.locator('#ceremonySkip').click();await p.evaluate("()=>{App.race=null;App.result=Store.tour.results.at(-1);App.resultMode='tour';showResults(true)}")
  before=await p.evaluate('JSON.stringify(Store.tour.results)');await replay()
  check('gc_order',await p.evaluate("""()=>{const f=App.finishFlow,b=f.plan.beats.at(-2),truth=Classification.gcOrder(f.snapshot.season).slice(0,3);return {pass:b.kind==='gc-final'&&JSON.stringify(b.ids)===JSON.stringify(truth),order:b.ids,kinds:f.plan.beats.map(b=>b.kind),seconds:f.plan.duration}}"""))
  geometry=await p.evaluate(GEOMETRY);check('final_geometry',{**geometry,'pass':geometry['limbError']<1e-6 and geometry['plantedError']<1e-6 and geometry['handError']<2.2 and geometry['staffError']<2.2})
  for age in [5.5,7.2,9.2,10.8,12.6,12.9,13.2,13.5,13.8,14.4,15.5,21.5,26.5]:await sample('gc-final',age,'gc-'+str(age)+'.png')
  check('gc_trophy_arm_posture',await p.evaluate("""()=>{
   const f=App.finishFlow,b=f.plan.beats.find(b=>b.kind==='gc-final'),q=CeremonyStage.cue(b),c=document.createElement('canvas').getContext('2d'),m=CeremonyStage.metrics(1280,720,true);
   let previous=null,maxElbowStep=0,maxElbowStepAt=null,minElbowOut=Infinity,minElbowRise=Infinity,minForearmRise=Infinity,maxGripError=0,count=0;
   for(let age=q.chest;age<=q.display+1;age+=1/120){
    const s=CeremonyStage.scene(f.plan,b.start+age,m),a=s.actors[0],r=CeremonyStage.person(c,a,b.start+age,age,a.walking,a.alpha),arms=r.limbs.filter(l=>l.kind==='arm');count++;
    arms.forEach((arm,j)=>{
     if(previous){const step=Math.hypot(arm.joint[0]-previous[j][0],arm.joint[1]-previous[j][1]);if(step>maxElbowStep){maxElbowStep=step;maxElbowStepAt={age,side:j};}}
     if(age>=q.display){minElbowOut=Math.min(minElbowOut,(j?1:-1)*(arm.joint[0]-arm.a[0]));minElbowRise=Math.min(minElbowRise,arm.a[1]-arm.joint[1]);minForearmRise=Math.min(minForearmRise,arm.joint[1]-arm.b[1]);}
     const hand=j?r.right:r.left,grip=s.prop.grips[j];maxGripError=Math.max(maxGripError,Math.hypot(hand[0]-grip[0],hand[1]-grip[1]));
    });previous=arms.map(a=>a.joint);
   }
   return {pass:minElbowOut>5&&minElbowRise>12&&minForearmRise>12&&maxElbowStep<1.5&&maxGripError<.01,count,minElbowOut,minElbowRise,minForearmRise,maxElbowStep,maxElbowStepAt,maxGripError};
  }"""))
  check('gc_clothing_and_final_hold',await p.evaluate("""()=>{const f=App.finishFlow,m=CeremonyStage.metrics(1280,720),b=f.plan.beats.at(-2),end=CeremonyStage.scene(f.plan,b.end-.01,m),held=CeremonyStage.scene(f.plan,b.end+.3,m);return{pass:b.ids.every((id,i)=>end.actors[i].jersey===(i===0?'yellow':['green','polka','white'].find(k=>f.snapshot.season.leaders[k]===id)||null))&&held.prop.type==='trophy'&&Math.hypot(held.prop.anchor[0]-end.prop.anchor[0],held.prop.anchor[1]-end.prop.anchor[1])<.001,jerseys:end.actors.map(a=>a.jersey),trophyHeld:held.actors[0].pose.lift}}"""))
  await sample('team-final',11,'team-final.png');await sample('complete',1.5,'tour-complete.png')
  for width,height in [(390,844),(320,740),(768,560)]:
   await p.set_viewport_size({'width':width,'height':height});await p.wait_for_timeout(220)
   await sample('gc-final',22,'gc-'+str(width)+'.png')
   check('layout_'+str(width),await p.evaluate("""()=>{const c=$('ceremonyCanvas').getBoundingClientRect(),n=$('ceremonyNext').getBoundingClientRect(),box=document.querySelector('.ceremony-theatre').getBoundingClientRect();return {pass:document.documentElement.scrollWidth<=innerWidth+1&&box.left>=0&&box.right<=innerWidth+1&&n.bottom<=innerHeight+1,canvas:[c.width,c.height],overflow:document.documentElement.scrollWidth-innerWidth,controlsBottom:n.bottom}}"""))
  await p.set_viewport_size({'width':1440,'height':1000})
  if args.play:
   await p.locator('[data-beat="0"]').click();await p.locator('#ceremonySpeed').select_option('1');await p.locator('#ceremonyPause').click()
   duration=await p.evaluate('App.finishFlow.plan.duration');await p.wait_for_function('!App.finishFlow',timeout=int(duration*1100+20000));check('whole_final_playback',{'pass':await p.evaluate('App.screen==="results"'),'seconds':duration,'rate':1})
  else:await p.keyboard.press('Escape')
  check('tour_ledger_unchanged',{'pass':before==await p.evaluate('JSON.stringify(Store.tour.results)')})
  await replay();await p.locator('#ceremonyNext').click();await p.keyboard.press('Escape')
  check('keyboard_return_focus',await p.evaluate("({pass:!App.finishFlow&&!$('resultsScreen').inert&&document.activeElement.id==='replayCeremony',focus:document.activeElement.id})"))
  await p.locator('#nextStage').click();check('archive',await p.evaluate("({pass:App.screen==='history'&&Store.tour.results.length===21,screen:App.screen})"))
  await ctx.close()
  reduced=await browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce');await reduced.set_offline(True)
  p=await reduced.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)));p.on('dialog',lambda d:d.accept());await p.goto(source.as_uri()+'?test');await p.evaluate('App.testingFreeze=true');await p.locator('#saveFile').set_input_files(str(args.tour.resolve()));await p.wait_for_function('Store.tour?.results.length===21');await p.locator('#continueTour').click();await replay()
  check('reduced_motion_static_pose',await p.evaluate("""()=>{const f=App.finishFlow,m=CeremonyStage.metrics(390,438,true),b=f.plan.beats.find(b=>b.kind==='gc-final'),a=CeremonyStage.scene(f.plan,b.start+.1,m),c=CeremonyStage.scene(f.plan,b.start+3,m);return {pass:reducedMotion&&JSON.stringify(a.actors)===JSON.stringify(c.actors)&&a.actors.every(a=>a.walking===0),seconds:f.plan.duration}}"""))
  await sample('gc-final',2,'gc-reduced.png');await p.locator('#ceremonySkip').click();await reduced.close();await browser.close()
 report['pass']=not report['errors'] and not report['console'];check('console',{'pass':report['pass'],'errors':report['errors'],'console':report['console']})
 (out/'sequence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--record',type=Path,required=True);ap.add_argument('--tour',type=Path,required=True);ap.add_argument('--play',action='store_true');asyncio.run(main(ap.parse_args()))
