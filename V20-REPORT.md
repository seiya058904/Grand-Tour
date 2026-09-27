# Grand Tour V20

Released 2026-09-27. Open `Grand-Tour-V20.html` directly to play; it is a self-contained offline HTML file with no build step or external runtime dependencies. `index.html` redirects to this file. V19 and V18.3.1 remain unchanged.

## Changes

- Refined continuous rider animation, scenery, lighting, camera behavior, finish presentation, and Race Centre summaries.
- Improved context-based team tactics and persisted decision memory while retaining the existing physics, classification, and save compatibility.
- Added paced, deduplicated race-radio notifications.

## Final playtest fixes

- Preserved torso proportions in the standing attack pose.
- Synchronized road markings and roadside motion with actual rider displacement across changing grades.
- Kept time gaps to a rider name, a clear seconds lead/deficit, and a short observed trend.
- Let eligible front-group riders sprint despite ordinary wheel-follow/support tasks; eased output after the sprint.
- Removed the three stray horizontal rural-scene strokes in every weather and quality mode.
- Kept radio transitions and reduced-motion behavior intact.

## Verification

- Offline Chromium run: home, stage selection, race, finish sprint, ceremony, results, and archive; flat, mountain/GC, ITT, TTT, automatic and designated wheel-follow; desktop and 390 px mobile layout. No fatal browser errors or horizontal overflow.
- Export/import and active-race restore checks passed; restored rider positions matched exactly. Reduced-motion ceremony and radio checks passed.
- Rural-scene regression: 64 combinations of four affected stages, four weather types, two quality levels, and desktop/mobile widths; zero removed-stroke draw calls and no race-state mutation.
- Ceremony geometry: 3,236 samples across eight award types; no invalid coordinates or grip/limb-length errors.
- Short 1440×1000 performance sample: V20 main-loop CPU average 3.29 ms, P95 6.8 ms, maximum 13 ms. This is a local sanity sample, not a device-wide frame-rate guarantee.
- Representative complete stage simulations cover flat, hilly, mountain/GC, ITT, and TTT, with deterministic reruns and save/restore comparisons. All 21 stages also passed initialization and short progression checks.

## Remaining limits and source

No complete continuous 21-stage Tour or physical-phone/Safari acceptance was performed. V20 is the canonical source of truth. The one-off `build_v20.py` and its patch fragments lived in the local Codex visualization workspace, reference machine-specific paths, and were not retained as a supported build chain; no generated-build reproducibility is claimed.

Artifact: `Grand-Tour-V20.html`, internal build version 200, 1,738,562 bytes, SHA-256 `3d9174c6c75e4150a91ff4a49408694d7d4de93678a5ac00f8dc353223bab1b2`.
