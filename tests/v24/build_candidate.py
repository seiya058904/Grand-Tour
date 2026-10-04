"""Build a local V24 repair candidate without changing the sealed release ZIP.
Only canonical payload, GT-01 tests, baseline aliases and provenance are updated.
The caller must choose a new output path outside the source checkout.
"""
import argparse, hashlib, json, zipfile
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parents[2]
PREFIX='Grand-Tour-V24/'
UPDATED=['Grand-Tour-V24.html','tests/v24/core-parity.cjs','tests/v24/static_verify.py',
 'tests/v24/README.md','tests/v24/save-finish-boundary.cjs','tests/v24/save-finish-browser.py',
 'tests/v24/build_candidate.py']

def sha(data):return hashlib.sha256(data).hexdigest()

def main(args):
 output=args.out.resolve();template=args.template.resolve()
 assert not output.is_relative_to(ROOT.resolve()),'candidate output must be outside the checkout'
 assert not output.exists(),'candidate output already exists'
 with zipfile.ZipFile(template) as sealed:
  names=sealed.namelist();assert len(names)==len(set(names)),'duplicate sealed ZIP members'
  assert all(n.startswith(PREFIX) and not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts for n in names),'unsafe sealed ZIP member'
  assert sealed.testzip() is None,'sealed ZIP CRC failure'
  contents={n:sealed.read(n) for n in names if not n.endswith('/')}
  metadata={i.filename:i for i in sealed.infolist()}
 manifest=PREFIX+'SHA256SUMS.txt'
 expected={name:digest for digest,name in (line.split('  ',1) for line in contents[manifest].decode('utf8').splitlines())}
 assert set(contents)=={PREFIX+n for n in expected}|{manifest},'sealed manifest coverage mismatch'
 assert all(sha(contents[PREFIX+n])==digest for n,digest in expected.items()),'sealed manifest hash mismatch'
 # Explicit paths prevent local caches, diagnostics or environment files entering a candidate.
 for name in UPDATED:contents[PREFIX+name]=(ROOT/name).read_bytes()
 for version in [22,23]:
  name=f'archive/v{version}/Grand-Tour-V{version}.html';data=(ROOT/name).read_bytes()
  assert data==contents[PREFIX+f'Grand-Tour-V{version}.html'],'historical baseline differs'
  contents[PREFIX+name]=data
 provenance={'kind':'unpublished-local-GT-01-repair-candidate','sealed_zip_sha256':sha(template.read_bytes()),
  'canonical_sha256':sha(contents[PREFIX+'Grand-Tour-V24.html']),
  'updated_files':{name:sha(contents[PREFIX+name]) for name in UPDATED},
  'baseline_aliases':['archive/v22/Grand-Tour-V22.html','archive/v23/Grand-Tour-V23.html'],
  'historical_evidence':'Existing reports and verification evidence retain their original bytes and source hashes; they do not verify this repair.',
  'release_state':'The original sealed ZIP is unchanged. This candidate is not a published release.'}
 contents[PREFIX+'verification/local-fix/PROVENANCE.json']=(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n').encode('utf8')
 contents[manifest]=''.join(f'{sha(data)}  {name[len(PREFIX):]}\n' for name,data in sorted(contents.items()) if name!=manifest).encode('utf8')
 output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as candidate:
  for name,data in sorted(contents.items()):
   info=metadata.get(name) or zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
   candidate.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
 with zipfile.ZipFile(output) as candidate:assert candidate.testzip() is None,'candidate ZIP CRC failure'
 print(json.dumps({'output':str(output),'sha256':sha(output.read_bytes()),'files':len(contents),'sealed_zip_sha256':provenance['sealed_zip_sha256']},indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--template',type=Path,default=ROOT/'Grand-Tour-V24-Final.zip')
 parser.add_argument('--out',type=Path,required=True)
 main(parser.parse_args())
