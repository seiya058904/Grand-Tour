#!/usr/bin/env python3
"""Build a reproducible lightweight V25 source ZIP from the handoff tree.

No frozen V24 ZIP, git history, installed dependency, cache, screenshot or video
is needed. Retained historical payload is selected by its immutable hash list.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
PREFIX = 'Grand-Tour-V25/'
ROOT_FILES = ['Grand-Tour-V25.html', 'index.html', 'README.md', 'AGENTS.md',
              'CLOUD-HANDOFF.md', 'V25-AUDIT-REPORT.md', 'V25-CHANGELOG.md', '.gitignore', '.gitattributes']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main(args):
    output = args.out.resolve()
    assert not output.is_relative_to(ROOT.resolve()), 'ZIP must be outside source tree'
    assert not output.exists(), 'Refusing to overwrite an existing delivery'
    baseline = json.loads((ROOT / 'tests/v25/baseline-hashes.json').read_text(encoding='utf-8'))
    names = set(ROOT_FILES) | set(baseline)
    for folder, suffixes in [(ROOT / 'tests/v25', {'.cjs', '.py', '.md', '.json'}),
                             (ROOT / '.github/workflows', {'.yml', '.yaml'})]:
        for p in folder.rglob('*'):
            if p.is_file() and p.suffix in suffixes and '__pycache__' not in p.parts:
                assert not p.is_symlink(), 'No symlinks in source payload'
                names.add(p.relative_to(ROOT).as_posix())
    payload = {}
    for name in sorted(names):
        assert not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts, name
        p = ROOT / name
        assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(ROOT.resolve()), name
        data = p.read_bytes()
        if name in baseline:
            assert sha(data) == baseline[name], 'Historical baseline changed: ' + name
        payload[name] = data
    provenance = {'kind': 'Grand Tour V25 released source',
                  'authoritativeV24Commit': '3e92128c0cb353d267c12ceeaf143bda663a7b26',
                  'inputZIP': 'Grand-Tour-V24-Cloud-Handoff-20261009.zip',
                  'inputZIP_SHA256': '2cecea547fb5290284a58a6e6a79fe2fbdb3f35c028f1658e30824a11771f9c8',
                  'V24_SHA256': baseline['Grand-Tour-V24.html'],
                  'V25_SHA256': sha(payload['Grand-Tour-V25.html']),
                  'historicalFilesPreserved': len(baseline),
                  'entry': 'index.html -> Grand-Tour-V25.html', 'saveSchema': 9,
                  'deployment': 'Released. V25 was merged into main via pull request #13 (merge commit '
                                '735cdabcd5e82623ba0ba4ffcf32df8ab6fb35e4) and deployed to GitHub Pages at '
                                'https://seiya058904.github.io/Grand-Tour/. The pre-release candidate source ZIP '
                                '(4619981 bytes, sha256 22cca5118a8813d63620d332728bc705e45f5bd3d2f089e35d57fbaf024867b9) '
                                'remains a frozen historical artifact and is not reproduced by this packager.',
                  'evidence': 'V25-AUDIT-REPORT.md and tests/v25/evidence document the pre-release candidate '
                              'acceptance; historical reports are baseline evidence only.'}
    payload['PROVENANCE.json'] = (json.dumps(provenance, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    payload['SHA256SUMS.txt'] = ''.join(f'{sha(data)}  {name}\n' for name, data in sorted(payload.items())).encode('utf-8')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(PREFIX + name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None, 'ZIP CRC check'
        assert len(archive.namelist()) == len(set(archive.namelist())) == len(payload)
    print(json.dumps({'path': str(output), 'bytes': output.stat().st_size,
                      'sha256': sha(output.read_bytes()), 'files': len(payload),
                      'htmlSHA256': provenance['V25_SHA256'], 'historicalFiles': len(baseline)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args())
