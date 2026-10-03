from pathlib import Path
import json,os,shutil
ROOT=Path(__file__).resolve().parent
BROWSER_EXE=os.environ.get('CHROMIUM_EXECUTABLE') or shutil.which('chromium') or shutil.which('chromium-browser')
BROWSER_ARGS=['--mute-audio']+(['--no-sandbox'] if hasattr(os,'getuid') and os.getuid()==0 else [])
def open_game(page,path=None,data=None,test=True):
 path=Path(path or ROOT.parent/'grand-tour-v12.html')
 page.goto('about:blank')
 html=path.read_text()
 if test: html=html.replace("const TEST_MODE=new URLSearchParams(location.search).has('test');",'const TEST_MODE=true;')
 encoded=json.dumps(data or {},ensure_ascii=True).replace('<','\\u003c')
 bootstrap='<script>window.Storage=class Storage{constructor(data){this._data=data}getItem(k){return this._data[k]??null}setItem(k,v){this._data[k]=String(v)}removeItem(k){delete this._data[k]}clear(){this._data={}}};Object.defineProperty(window,"localStorage",{configurable:true,value:new Storage('+encoded+')});</script>'
 html=html.replace('<script>',bootstrap+'<script>',1)
 page.set_content(html,wait_until='load')
def reload_game(page,path=None):open_game(page,path,page.evaluate('localStorage._data'))
