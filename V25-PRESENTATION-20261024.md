# V25 presentation review — 2026-10-24

This iteration starts at `a1207148a8a4ec93c7b03cbb23a92db2d01f6a9f` on `main`.
It refines the existing offline Canvas ceremony, not the race rules or save format.
The original V25 audit and changelog remain historical records and are unchanged.

## Changes

- The stage masthead is quieter, the recognition camera retains more of the
  stage, and the backdrop adds restrained warm illumination behind the athlete.
- Leg contours follow the existing articulated skeleton rather than changing
  limb lengths or foot placement. A brief nod, gaze and smile acknowledge the
  audience after the award; reduced-motion presentation remains static.
- Ceremony controls write text and ARIA attributes only when their visible
  state changes. Every mount resets the read model, including replay.
- A paused Canvas frame is retained until its time, record, plan, saved state,
  dimensions, pixel size, motion preference or playback instance changes.
  Unmount releases the retained frame reference.
- A new offline browser regression covers normal quick finish, pause, seek,
  resume, resize, replay, keyboard focus and unchanged results. The existing
  candidate CI runs it, and the source packager includes this review.

## Evidence-driven audit

The review followed the production race, finish/settlement, frozen result,
ceremony schedule, actors, IK, camera and transport paths. It also checked the
existing AI pursuit, support, sprint and GC decision regressions, source-family
parity, storage/recovery gates and normal offline browser flows.

No new blocking race-rule or save defect was confirmed in that coverage. The
presentation work is a design improvement, and the redundant rendering work is
a measured optimization; neither is presented as a newly discovered data-loss bug.

The fresh baseline survey ran seeds 42 and 2026 on stages 1, 5, 7 and 16:
8 natural races, 493 invariant samples and 8 restore comparisons passed. The
four flat races again had no Sprinter winner. Late samples showed sprinters
behind the leading riders and sometimes low on energy. This remains an existing
balance signal, not proof of a specific incorrect rule. No forced winner,
role multiplier, AI heuristic, physics, RNG or save schema was changed.

## Measured scope

With the same naturally generated result, paused chapter and viewport, 240
repeated transport updates previously produced 1,440 DOM mutations. The new
transport produces zero with identical time, pause and selected-chapter values.
The same 240 paused draw requests previously painted the scene 240 times; the
new renderer paints zero. A changed presentation time and a resized viewport
still repaint, and a new replay resets the controls.

These are deterministic work-count measurements, not an FPS, GPU or battery-life
claim. No independent ABBA race-performance improvement is claimed. Tests used
isolated browser storage; real player data was not read or changed.

## Verification

Final HTML SHA-256: `29417c79c80e767ba94cb6d5c5d78765f21cbe74e80efcc346023a222b8905f0`.

- All 11 final static, core, AI, boundary, ownership, TTT, storage, first-save,
  live-ceremony, continuity and scoring gate processes passed.
- A fresh complete 21-stage Tour (seed 314159) exercised 367 snapshot restores.
  Its entire V9 object exactly matches the fresh pre-change V25 run, including
  every result and rider array; both serialized objects have SHA-256
  `3e83c50c18c06d77f0f41abd871c0c28d08b36ef8c0aec6077ac7a6601575fed`.
- Final real-time stage, GC and TTT ceremony playback passed all 20 sequence
  checks, including limb/contact, award attachment and reduced-motion checks.
- Final transport regression passed all nine checks; final browser storage and
  first-save regression passed all 12 cases.
- Earlier broad presentation and UI checks covered widths 320 through 3840,
  focus, interrupted modals, reduced motion and offline persistence. These ran
  before the paused-frame optimization; the final sequence, transport and
  storage suites above were rerun after the source was frozen.

The source archive is separately built and verified from its extracted offline
entry. Its receipt is retained with the external evidence batch.

Local environment: Windows, Node.js, installed Python Playwright 1.63.0 with an
explicit path to installed Chromium 1248 (156.0.8078.4). The historical local
default browser revision is absent. No dependencies were installed or updated;
the existing CI retains its own pinned browser environment.

Not covered: physical mobile devices, Safari/Firefox, listening to audio,
screen-reader speech, all AI seeds, or every possible save corruption. Native
browser playback and sampled screenshots do not constitute human viewing of
every frame or a complete manual 21-stage playthrough. The four flat samples
do not settle the retained Sprinter balance question.

Detailed local logs, natural fixtures, videos and screenshots are kept outside
this repository in the dashboard's `output/grand-tour-20261024/` evidence batch.
Intermediate runs are retained separately and are not substituted for final
source verification. Publication and deployed bytes are checked after independent
review of the committed candidate; local passing checks alone are not deployment proof.
