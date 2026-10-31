# V26 verification

V26 (`Grand-Tour-V26.html`) changes presentation only: the post-race ceremony
(director, camera, set, cartoon cast, particles, overlay, player chrome) and
DOM/CSS polish on the home, race HUD and results screens. `Grand-Tour-V25.html`
is the frozen baseline. The 14 engine/data families are source-identical to V25.

Run from the repository root. Write output outside the repository.

```bash
OUT="$(mktemp -d -t gt-v26-XXXXXX)"
node tests/v26/core-parity.cjs Grand-Tour-V25.html Grand-Tour-V26.html "$OUT/core.json"
node tests/v26/focused.cjs Grand-Tour-V26.html archive/v22/Grand-Tour-V22.html "$OUT/focused.json"
node tests/v24/save-finish-boundary.cjs Grand-Tour-V26.html "$OUT/boundary.json"
node tests/v25/storage-first-settings.cjs Grand-Tour-V26.html "$OUT/first-settings.json"
node tests/v25/storage-validation.cjs Grand-Tour-V26.html "$OUT/storage.json" "$OUT/fixtures"
node tests/v25/render-continuity.cjs Grand-Tour-V26.html "$OUT/continuity.json"
node tests/v25/render-score-parity.cjs Grand-Tour-V25.html Grand-Tour-V26.html "$OUT/score.json"
node tests/v26/ceremony.cjs Grand-Tour-V26.html "$OUT/ceremony.json"
python tests/v25/ceremony-transport-browser.py --source Grand-Tour-V26.html --out "$OUT/transport"
python tests/v26/ceremony_browser.py --source Grand-Tour-V26.html --out "$OUT/browser" --final-stage
```

The browser scripts need Python Playwright and Chromium. Both accept
`--executable-path` for an already installed Chromium.

| Script | What it checks |
| --- | --- |
| `core-parity.cjs` | `Race`, `Physics`, `Physiology`, `Fatigue`, `Weather`, `RaceTiming`, `TeamClassification`, `Classification`, `TimeLimits`, `CompactCourse`, `SaveCodec`, `SimulationClock`, `RIDER_DATA` and `STAGE_DATA` are identical to V25, with no exceptions. `CONFIG` differs only in `buildVersion` (250 → 260); the save key and V9 schema do not change. |
| `focused.cjs` | Runs the 35 V24 regressions in memory through the same kind of adapter V25 used. It makes three identity swaps (build 260, test name, default file) and one reviewed timing swap: the award probe moves from `start+13` to `start+8`. V26 awards last 10.5 s, so `+13` now falls inside the next award. All assertions stay the same. Pass the V22 baseline so the three `if(O)` history checks run. |
| `ceremony.cjs` | New timing (10.5 / 9 / 16 s; complete 3 or 4 s); award identities, jerseys and bouquets; GC entry order 3 → 2 → 1 and left/right placement; the presenter and rider holding the same grip; props drawn at the solved hand; standing feet staying on their surface; one continuous camera track (no per-award reset, hero zoom ≥ 1.4); whip-pan instead of the black dip; identical scene and paint call-stream hashes in any seek order and after a cache rebuild; confetti capped at ≤ 220 with no `Math.random`, RNG or simulation calls; record and RNG unchanged. |
| `ceremony_browser.py` | Plays the real offline flow from home through stage 5, quick finish, ceremony, results and replay. It also covers keyframe screenshots, paint cost and frame gaps (1280×900 and 390×844), pixel hashes in any seek order, Space, playback rate, Esc, the narrow layout, reduced motion (short static awards, fixed camera) and optional finale frames. The finale frames use a synthetic stage-20 record and go through the painter only. |

## Expected differences from V25 tests

The unmodified `tests/v25/focused.cjs` fails two checks on V26, both on
purpose: the build identity check (expects 250) and the award probe at `+13`.
`tests/v26/focused.cjs` covers both, and `tests/v26/ceremony.cjs` adds the new
timing checks. The historical test files are not edited.

## Performance note

`ceremony_browser.py` records the JavaScript paint time per frame and the
spacing between RAF frames. Both are taken in headless Chromium, so GPU raster
time is not included and the numbers are only indicative. The local run is in
`evidence/v26-ceremony-browser.json`. Its maximum paint time includes the first
frame, which builds the cached parallax layers.

`evidence/` holds compact JSON from the local acceptance run. Screenshots and
logs stay outside the repository.
