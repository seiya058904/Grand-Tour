#!/usr/bin/env python3
"""Run retained V24 browser assertions against the separately named V25 build.

Only the game filename and exact edition title are retargeted. Assertions,
timeouts, interactions, fixtures and algorithms are otherwise byte-for-byte
the retained suite. The source scripts in tests/v24 are never modified.

Example: python tests/v25/legacy_browser.py presentation --out /tmp/gt-v25-ui
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SUITES = {
    'presentation': 'presentation_verify.py',
    'finish': 'finish_motion_verify.py',
    'downhill': 'downhill_verify.py',
    'scenes': 'scene_verify.py',
    'weather': 'weather_verify.py',
    'sequence': 'sequence_verify.py',
    'live': 'live_play_verify.py',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite', choices=SUITES)
    args, remaining = parser.parse_known_args()
    original = ROOT / 'tests' / 'v24' / SUITES[args.suite]
    source = original.read_text(encoding='utf-8')
    old_name = 'Grand-Tour-V24.html'
    if old_name not in source:
        raise RuntimeError('Retained suite no longer contains its known source target')
    source = source.replace(old_name, 'Grand-Tour-V25.html')
    source = source.replace('环法 · Grand Tour V24 · 公路自行车竞赛游戏',
                            '环法 · Grand Tour V25 · 公路自行车竞赛游戏')
    sys.argv = [str(original), *remaining]
    sys.path.insert(0, str(original.parent))
    print(f'V25 target; unchanged {args.suite} assertions from {original.name}', flush=True)
    exec(compile(source, str(original), 'exec'),
         {'__name__': '__main__', '__file__': str(original)})


if __name__ == '__main__':
    main()
