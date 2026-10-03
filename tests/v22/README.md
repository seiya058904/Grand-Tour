# V22 validation

Run these commands from the repository root; historical HTML is under `archive/`. For a recovered V22 ZIP, use its original validation guide and scripts, whose baseline paths are at the package root. These scripts execute the canonical HTML. Node.js, Python 3.10+ and an existing Playwright Chromium installation are required; the game itself has no runtime dependencies.

```powershell
# The original V22 entry/manifest check runs inside the recovered V22 package.
node tests/v22/focused.cjs archive/v22/Grand-Tour-V22.html archive/v21/Grand-Tour-V21.html D:/tmp/v22-focused.json
python tests/v22/browser_verify.py --out D:/tmp/v22-browser
python tests/v22/presentation_verify.py --out D:/tmp/v22-presentation
python tests/v22/extended_verify.py --out D:/tmp/v22-extended
python tests/v22/finish_motion_verify.py --out D:/tmp/v22-finish
python tests/v22/downhill_verify.py --out D:/tmp/v22-downhill
python tests/v22/radio_overlay_verify.py --source archive/v22/Grand-Tour-V22.html --out D:/tmp/v22-radio
node tests/v22/tour-simulation.cjs archive/v22/Grand-Tour-V22.html D:/tmp/v22-tour.json 314159
python tests/v22/tour_final_verify.py --tour D:/tmp/v22-tour-tour.json --out D:/tmp/v22-tour-final
python tests/v22/performance_probe.py --out D:/tmp/v22-performance.json
```

Use a fresh output directory for `presentation_verify.py`: it creates a test-owned persistent Chromium profile and interaction video there. No user browser profile is accessed. Choose any writable output paths outside the source tree or under ignored `output/`. In an extracted final ZIP, its original `python tests/v22/static_verify.py --manifest` also verifies the V22 entry and all packaged files; the current repository entry is V24.

The baseline browser, extended, descent, finish, radio and performance scripts came from the V21 final package. The engine loader, focused suite and 21-stage pilot came from the repository's V12 tests. V22 changes their paths/version expectations and adds presentation regressions, function-source parity and final-tour replay checks. The old instant-response fixture is replaced with the current physical predecessor contract: V17 introduced reaction latency and delegated GC protection. Function-source comparisons normalize CRLF/LF only.

`browser_verify.py` and the natural sprint/descent tests advance the real fixed-step engine to reach scenes. `tour-simulation.cjs` uses a scripted pilot calling public controls, not a human playing all 21 stages. The focused suite includes explicitly synthetic isolated boundary fixtures. The radio overlay test injects a UI-only test notification and in-memory storage. Its screenshots do not establish that notification's natural tactical occurrence.

The other browser scripts use native `file://` and real browser storage by default. `--injected` is an optional fallback in inherited scripts, and must be disclosed if used. New presentation checks run offline, import a genuine V21 snapshot through the file control, close Chromium, reopen the same test-owned profile, then verify physical-state equality.

Automated PASS does not establish human aesthetic acceptance, device-wide FPS or tactical balance across all seeds. Evidence and exact limitations are in `archive/v22/V22-REPORT.md` and the ZIP's `evidence/` directory.
