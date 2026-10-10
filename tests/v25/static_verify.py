#!/usr/bin/env python3
"""V25 offline/source identity and preservation of the supplied baselines."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests' / 'v23'))
from static_verify import Inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    src = ROOT / 'Grand-Tour-V25.html'
    text = src.read_text(encoding='utf-8')
    prior = (ROOT / 'Grand-Tour-V24.html').read_text(encoding='utf-8')
    inv = Inventory()
    inv.feed(text)
    baseline_hashes = json.loads((ROOT / 'tests/v25/baseline-hashes.json').read_text())
    preserved = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
        for name, digest in baseline_hashes.items()
    }
    core = lambda s: s[s.index('class Race {'):s.index('/* ENVIRONMENT')]
    checks = {
        'v25_identity': all(x in text for x in (
            'data-build="2500"', 'buildVersion:250',
            '<title>环法 · Grand Tour V25', 'build-stamp">V25 ·')),
        'latest_v24_preserved': hashlib.sha256((ROOT / 'Grand-Tour-V24.html').read_bytes()).hexdigest()
            == 'b5d0899fad82ed6576f416e12267ec6d369405a4dfa56559e5629e6fcf00fa1f',
        'historical_sources_tests_preserved': all(preserved.values()),
        'unique_dom_ids': len(inv.ids) == len(set(inv.ids)),
        'offline_assets': not inv.remote,
        'no_remote_css': not re.search(r'@import\s+|url\([\'"]?https?://', text[:text.index('</style>')]),
        'original_race_class_preserved': core(text) == core(prior),
        'v9_storage_identity': "saveKey:'tour-cycling-2026-cinematic-v10',saveVersion:9" in text,
        'finish_guard_preserved': '  validateFinishState(s,race.stage.length);\n' in core(text),
        'entry_targets_v25': '"./Grand-Tour-V25.html"' in (ROOT / 'index.html').read_text()
            and 'Grand-Tour-V24.html' not in (ROOT / 'index.html').read_text(),
    }
    with tempfile.TemporaryDirectory(prefix='grand-tour-v25-syntax-') as td:
        for i, script in enumerate(inv.scripts):
            path = Path(td) / f'inline-{i}.js'
            path.write_text(script, encoding='utf-8')
            subprocess.run(['node', '--check', str(path)], check=True, capture_output=True)
    checks['javascript_syntax'] = True
    report = {
        'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
        'checks': checks, 'preserved_files': len(preserved),
        'changed_baselines': [name for name, ok in preserved.items() if not ok],
        'passed': sum(checks.values()), 'failed': sum(not v for v in checks.values()),
        'skipped': 0, 'pass': all(checks.values()),
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    if not report['pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
