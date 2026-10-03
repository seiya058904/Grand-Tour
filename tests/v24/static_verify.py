"""Standalone V24, immutable main baseline, simulation signatures and manifest."""
import argparse,hashlib,json,re,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v23'))
from static_verify import Inventory
ROOT=Path(__file__).resolve().parents[2]
def main(a):
 src=ROOT/'Grand-Tour-V24.html';old=ROOT/'Grand-Tour-V23.html';text=src.read_text(encoding='utf8');baseline=old.read_text(encoding='utf8');inv=Inventory();inv.feed(text)
 # This range includes the constructor, fixed-step integrator and original AI.
 def core(s):return s[s.index('class Race {'):s.index('/* ENVIRONMENT')]
 checks={'version':'data-build="2400"' in text and 'buildVersion:240' in text and '<title>环法 · Grand Tour V24' in text,
  'main_v23_original':hashlib.sha256(old.read_bytes()).hexdigest()=='9d59a207b8b7a88fdeb0a24978e28074f241498610f25ebae043d68839bb0d89',
  'unique_dom_ids':len(inv.ids)==len(set(inv.ids)), 'offline_assets':not inv.remote,
  'race_class_identical':core(text)==core(baseline),
  'route_data_identical':all(line in text for line in baseline.splitlines() if line.startswith(('const OFFICIAL_PROFILE_DATA_V182=','const V181_STAGE_DATA=','const STAGE_DATA='))),
  'no_remote_css':not re.search(r'@import\s+|url\([\'"]?https?://',text[:text.index('</style>')])}
 with tempfile.TemporaryDirectory(prefix='grand-tour-v24-syntax-') as td:
  for i,script in enumerate(inv.scripts):
   p=Path(td)/f'inline-{i}.js';p.write_text(script,encoding='utf8');subprocess.run(['node','--check',str(p)],check=True,capture_output=True)
 checks['javascript_syntax']=True
 if a.manifest:
  for line in (ROOT/'SHA256SUMS.txt').read_text(encoding='utf8').splitlines():
   digest,name=line.split('  ',1);assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
  checks['package_manifest']=True
 report={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'checks':checks,'pass':all(checks.values())};print(json.dumps(report,indent=2));assert report['pass']
 if a.out:a.out.write_text(json.dumps(report,indent=2),encoding='utf8')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',action='store_true');ap.add_argument('--out',type=Path);main(ap.parse_args())
