#!/usr/bin/env python3
"""Same-origin two-page persistence and actual Race Centre DOM regression.
Run a static server from the repository at http://127.0.0.1:4187 first.
Only race pacing is accelerated through the production tick(true).
"""
import asyncio,json
from playwright.async_api import async_playwright
async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,args=['--no-sandbox'])
  for locks in [True,False]:
   ctx=await browser.new_context();errors=[]
   if not locks: await ctx.add_init_script("Object.defineProperty(navigator,'locks',{value:undefined})")
   a=await ctx.new_page();b=await ctx.new_page()
   for p in [a,b]:p.on('pageerror',lambda e:errors.append(str(e)))
   url='http://127.0.0.1:4187/archive/v23/Grand-Tour-V23.html?test'
   await a.goto(url);await a.evaluate('App.testingFreeze=true')
   await a.locator('#newTour').click();await a.locator('#startRace').click();await a.evaluate('saveQueue')
   await b.goto(url);await b.evaluate('App.testingFreeze=true');await b.locator('#continueTour').click()
   await a.evaluate('async()=>{while(!App.race.complete)App.race.tick(true);await finalizeRace()}')
   before=await a.evaluate('JSON.parse(localStorage.getItem(CONFIG.saveKey))')
   await b.locator('#visualQuality').select_option('low');await b.evaluate('saveQueue')
   after=await b.evaluate('JSON.parse(localStorage.getItem(CONFIG.saveKey))')
   assert len(after['tour']['results'])==1 and after['active'] is None and after['pendingCeremony']==before['pendingCeremony']
   assert after['settings']['quality']=='low'
   stale=await b.evaluate('async()=>await persist()');assert stale is False
   assert '导出' in await b.locator('#storageWarning').inner_text()
   # Active threat fixture rendered by the actual table; no AI/physics changes.
   target=await b.evaluate("""()=>{const r=new Race(18);for(const y of r.riders){y.x=0;y.v=10}const x=r.riders.find(x=>x.d.teamId!==0&&!r.gcIds.includes(x.id)&&x.d.role==='GC'&&x.d.climb>=90);x.x=300;x.inBreak=true;r.relations();initializeRace(r);r.paused=true;Desk.tab='gc';updateDesk(r,true);return x.id}""")
   assert await b.locator(f'#deskContent tr[data-id="{target}"]').count()==1
   await b.locator('#deskFreeze').click();await b.locator('#deskFreeze').click()
   await b.screenshot(path=f'/tmp/gt-evidence/two-page-locks-{locks}.png')
   assert not errors, errors
   print(json.dumps({'locks':locks,'results':1,'active':None,'quality':'low','staleRejected':True,'gcRow':target,'errors':errors}))
   await ctx.close()
  await browser.close()
asyncio.run(main())
