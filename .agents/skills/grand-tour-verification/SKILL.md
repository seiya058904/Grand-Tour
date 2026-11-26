---
name: grand-tour-verification
description: Use when running V26/V25 verification gates, browser ceremony tests, full Tour comparisons, ABBA performance sampling, or source packaging/verification in Grand Tour.
---

# Grand Tour Verification & Packaging Gates

Run from repo root; store all evidence/screenshots/logs outside the repo (`tests/v26/README.md`, `tests/v25/README.md`).

## 1. V26 Gates
```bash
mkdir -p /tmp/gt-v26
node tests/v26/core-parity.cjs Grand-Tour-V25.html Grand-Tour-V26.html /tmp/gt-v26/core.json
node tests/v26/focused.cjs Grand-Tour-V26.html archive/v22/Grand-Tour-V22.html /tmp/gt-v26/focused.json
node tests/v24/save-finish-boundary.cjs Grand-Tour-V26.html /tmp/gt-v26/boundary.json
node tests/v25/storage-validation.cjs Grand-Tour-V26.html /tmp/gt-v26/storage.json /tmp/gt-v26/fixtures
node tests/v26/ceremony.cjs Grand-Tour-V26.html /tmp/gt-v26/ceremony.json
python tests/v26/ceremony_browser.py --source Grand-Tour-V26.html --out /tmp/gt-v26/browser --final-stage
```
*(Unmodified `tests/v25/focused.cjs` intentionally fails 2 assertions on V26: `buildVersion 250` and ceremony `start+13`.)*

## 2. V25 Engine Gates & Packaging
```bash
mkdir -p /tmp/gt-v25
python tests/v25/static_verify.py --out /tmp/gt-v25/static.json
node tests/v25/core-parity.cjs Grand-Tour-V24.html Grand-Tour-V25.html /tmp/gt-v25/core.json
node tests/v25/focused.cjs Grand-Tour-V25.html archive/v22/Grand-Tour-V22.html /tmp/gt-v25/focused.json
node tests/v24/save-finish-boundary.cjs Grand-Tour-V25.html /tmp/gt-v25/boundary.json
node tests/v25/storage-validation.cjs Grand-Tour-V25.html /tmp/gt-v25/storage.json /tmp/gt-v25/fixtures
python tests/v24/browser_verify.py --source Grand-Tour-V25.html --out /tmp/gt-v25/browser
```
- Full Tour comparisons must freshly run both versions and diff complete V9 objects (old PASS ≠ new PASS). ABBA performance runs must stop other simulations/browsers, pin `full` quality, and record environment + source hash.
- Packaging: `tests/v25/package_source.py` + `tests/v25/package_verify.py` (embeds original V25 entry; **never overwrite original V24 package**).
