from pathlib import Path
import sys,json,time,base64,subprocess,hashlib,traceback
sys.path.insert(0,str(Path(__file__).resolve().parent))
from browser_common import *
from playwright.sync_api import sync_playwright
B=Path(__file__).resolve().parent.parent;GAME=Path(__file__).resolve().parent.parent/'grand-tour-v12.html';OUT=B/'evidence';frames=OUT/'video-frames';frames.mkdir(exist_ok=True)
pilot=(B/'tests/tour-simulation.cjs').read_text();pilot=pilot[pilot.index('function pilot'):pilot.index('\nconst mean')]
report={'source':str(GAME),'sha256':hashlib.sha256(GAME.read_bytes()).hexdigest(),'environment':'Actual Chromium CDP screencast, no generated frames. about:blank actual HTML with explicit memory Storage. Public-input pilot, fast-forward ONLY before recording; normal RAF throughout recorded finish/ceremony/results. No audio.','frames':[],'states':[],'errors':[]}
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=BROWSER_EXE,headless=True,args=BROWSER_ARGS);c=browser.new_context(viewport={'width':1366,'height':900});p=c.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)));open_game(p,GAME)
 setup=p.evaluate('''pilot=>{const T=__TOUR_TEST__;T.start(4);T.App.testingFreeze=true;const r=T.App.race;window.__drive=new Function('E','return '+pilot)(T);while(T.isRacing(r.player)&&r.stage.length-r.player.x>105){if(r.stepCount%20===0)__drive(r);r.tick();}T.updateHud(true);T.drawRace();return {stage:5,simulationTime:r.t,remainingLocalMetres:r.stage.length-r.player.x};}''',pilot);report['setup']=setup
 p.wait_for_timeout(350);session=c.new_cdp_session(p)
 def frame(event):
  i=len(report['frames']);f=frames/f'{i:06d}.jpg';f.write_bytes(base64.b64decode(event['data']));report['frames'].append({'file':f.name,'timestamp':event['metadata'].get('timestamp',time.monotonic())});session.send('Page.screencastFrameAck',{'sessionId':event['sessionId']})
 session.on('Page.screencastFrame',frame);session.send('Page.startScreencast',{'format':'jpeg','quality':82,'maxWidth':1366,'maxHeight':900,'everyNthFrame':2})
 p.evaluate('''()=>{const T=__TOUR_TEST__;T.App.testingFreeze=false;let sec=-1;function drive(){const r=T.App.race;if(T.App.screen==='race'&&!T.App.finishFlow&&r&&T.isRacing(r.player)){if(Math.floor(r.t)!==sec){sec=Math.floor(r.t);__drive(r);}}if(T.App.screen!=='results')requestAnimationFrame(drive);}requestAnimationFrame(drive);}''')
 start=time.monotonic();finished=None;last=None
 while time.monotonic()-start<55:
  state=p.evaluate("({screen:__TOUR_TEST__.App.screen,phase:__TOUR_TEST__.App.finishFlow?.phase,beat:__TOUR_TEST__.App.finishFlow?.plan?.beats[__TOUR_TEST__.App.finishFlow?.beat]?.kind,t:__TOUR_TEST__.App.race?.t})");key=(state['screen'],state.get('phase'),state.get('beat'))
  if key!=last:report['states'].append({'wall':time.monotonic()-start,**state});last=key
  if state['screen']=='results':
   if finished is None:finished=time.monotonic()
   if time.monotonic()-finished>3:break
  p.wait_for_timeout(100)
 session.send('Page.stopScreencast');p.screenshot(path=str(OUT/'recorded-flow-results.png'));report['elapsedSeconds']=time.monotonic()-start;report['lastScreen']=p.evaluate('__TOUR_TEST__.App.screen');c.close();browser.close()
if len(report['frames'])>=2:
 import bisect,math
 rows=report['frames'];first=rows[0]['timestamp'];last=rows[-1]['timestamp'];report['capturedSeconds']=last-first;report['capturedAverageFps']=(len(rows)-1)/max(.001,last-first)
 stamps=[row['timestamp']-first for row in rows];fps=30;count=math.ceil(report['elapsedSeconds']*fps);target=B/'Grand-Tour-V12-finish-ceremony.mp4'
 command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','image2pipe','-vcodec','mjpeg','-framerate',str(fps),'-i','pipe:0','-c:v','libx264','-preset','fast','-threads','2','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(target)]
 encoder=subprocess.Popen(command,stdin=subprocess.PIPE);previous=-1;buffer=None
 for i in range(count):
  index=max(0,bisect.bisect_right(stamps,i/fps)-1)
  if index!=previous:buffer=(frames/rows[index]['file']).read_bytes();previous=index
  encoder.stdin.write(buffer)
 encoder.stdin.close()
 if encoder.wait()!=0:raise RuntimeError('ffmpeg video encoding failed')
 report['video']=str(target);report['encodedVideo']=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,size:stream=codec_name,width,height,avg_frame_rate,nb_frames','-of','json',str(target)]))
 report['encodingNote']='30fps timestamp resampling by holding the last actual CDP frame, without interpolation or synthetic motion. Encoded duration matches the actual browser observation including three seconds on Results. Encoding rate is not game FPS.'
report['pass']=report['lastScreen']=='results' and not report['errors'] and len(report['frames'])>100 and any(s.get('phase')=='ceremony' for s in report['states']);(OUT/'recorded-flow.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('VIDEO',report['pass'],len(report['frames']),report.get('capturedAverageFps'),report['elapsedSeconds'],flush=True)
