"""Sequential local A/B probe; real 1x frames, full quality, no test races in parallel."""
import argparse,asyncio,hashlib,json,sys
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding='utf8')
async def main(a):
 report={'protocol':'Chromium headless, Windows, 1440x1000 DPR1, full quality, actual 1x; same natural snapshots. ABBA order per scene, 1.5s warm-up + 5s measurement; no concurrent test processes. Local shared machine, not a phone/isolated laboratory benchmark.','runs':[]}
 async with async_playwright() as pw:
  b=await pw.chromium.launch(headless=True);report['browser']=b.version
  for scene in ['peloton','climb','leadout']:
   snap=json.loads((a.scenes/(scene+'-snapshot.json')).read_text(encoding='utf8'))
   for version in ['V23','V24','V24','V23']:
    src=(ROOT if version=='V24' else ROOT/'archive'/version.lower())/('Grand-Tour-'+version+'.html');c=await b.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1);await c.set_offline(True);p=await c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
    await p.goto(src.as_uri()+'?test');await p.evaluate('''s=>{App.testingFreeze=true;App.blockStoreWrite=true;Store.settings.quality='full';initializeRace(Race.restore(s));App.testingFreeze=false}''',snap)
    await p.wait_for_timeout(1500);await p.evaluate('Perf.start()');await p.wait_for_timeout(5000)
    data=await p.evaluate('''()=>{const stat=a=>{const b=a.slice().sort((x,y)=>x-y);return{n:b.length,p50:b[Math.floor((b.length-1)*.5)]||0,p95:b[Math.floor((b.length-1)*.95)]||0,p99:b[Math.floor((b.length-1)*.99)]||0,max:b.at(-1)||0,over33:a.filter(x=>x>33.34).length,over50:a.filter(x=>x>50).length}};return{...Perf.summary(),frames:stat(Perf.frames),cpu:stat(Perf.cpu),quality:Store.settings.quality,effectiveLow:RenderBudget.low()}}''')
    data.update(version=version,scene=scene,sha256=hashlib.sha256(src.read_bytes()).hexdigest(),errors=errors);report['runs'].append(data);print(version,scene,json.dumps({k:data[k] for k in ['frames','cpu','lastDebt','simPerWall','effectiveLow']}),flush=True);await c.close()
  await b.close()
 report['pass']=all(not r['errors'] and not r['effectiveLow'] and r['lastDebt']<.15 for r in report['runs']);a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');assert report['pass']
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--scenes',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);asyncio.run(main(ap.parse_args()))
