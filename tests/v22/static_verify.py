"""Verify standalone V22, preserved V21/V20 and optional extracted ZIP manifest."""
import argparse,collections,hashlib,json,re,subprocess,tempfile
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class Inventory(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.remote=[];self.scripts=[];self.in_script=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.append(a['id'])
  if tag=='script':self.in_script=True;self.scripts.append('')
  keys=['src'] if tag in ['script','img','audio','video','source','iframe'] else ['href'] if tag=='link' and a.get('rel')=='stylesheet' else []
  for key in keys:
   if re.match(r'^(https?:)?//',a.get(key,'')):self.remote.append(a[key])
 def handle_endtag(self,tag):
  if tag=='script':self.in_script=False
 def handle_data(self,data):
  if self.in_script:self.scripts[-1]+=data
def main(args):
 src=ROOT/'Grand-Tour-V22.html';text=src.read_text(encoding='utf-8');old=(ROOT/'Grand-Tour-V21.html').read_text(encoding='utf-8')
 inv=Inventory();inv.feed(text)
 checks={
  'markers':'data-build="2200"' in text and 'buildVersion:220' in text and '<title>环法 · Grand Tour V22' in text,
  'index':'./Grand-Tour-V22.html' in (ROOT/'index.html').read_text(encoding='utf-8'),
  'unique_dom_ids':len(inv.ids)==len(set(inv.ids)),
  'offline_assets':not inv.remote,
  'v21_original':hashlib.sha256((ROOT/'Grand-Tour-V21.html').read_bytes()).hexdigest()=='b33b017dd0b1692f4dc16d0470b58fb1c417b65a03a69ce49c925daa60a762cf',
  'v20_original':hashlib.sha256((ROOT/'Grand-Tour-V20.html').read_bytes()).hexdigest()=='3d7d013d61c6d01459a8d3185fb4ff2b30983a4a172245190d858311325e2581',
  'core_engine_and_save_unchanged':text[text.index('const clamp='):text.index('function fitCanvas')]==old[old.index('const clamp='):old.index('function fitCanvas')],
  'route_data_unchanged':all(line in text for line in old.splitlines() if line.startswith(('const OFFICIAL_PROFILE_DATA_V182=','const V181_STAGE_DATA=','const STAGE_DATA='))),
  'no_external_font_css':not re.search(r'@import\s+|url\([\'"]?https?://',text[:text.index('</style>')]),
 }
 with tempfile.TemporaryDirectory(prefix='grand-tour-v22-syntax-') as td:
  for i,script in enumerate(inv.scripts):
   p=Path(td)/f'inline-{i}.js';p.write_text(script,encoding='utf-8');subprocess.run(['node','--check',str(p)],check=True,capture_output=True)
 checks['javascript_syntax']=True
 if args.manifest:
  for line in (ROOT/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
   digest,name=line.split('  ',1);assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
  checks['package_manifest']=True
 report={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'checks':checks,'pass':all(checks.values())}
 if args.out:args.out.write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report,indent=2));assert report['pass']
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--manifest',action='store_true');p.add_argument('--out',type=Path);main(p.parse_args())
