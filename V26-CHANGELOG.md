# Grand Tour V26 — ceremony overhaul and presentation polish

Built from `Grand-Tour-V25.html`, which stays frozen as the baseline. V26
changes only the presentation layer. The simulation, AI, data and save
families are byte-identical in source (see `tests/v26/core-parity.cjs`), and
the save key and V9 schema do not change. Only `CONFIG.buildVersion` moves from
250 to 260.

## Post-race ceremony

- **Tighter pacing.** Each individual award now lasts 10.5 s (was 20.8 s), a
  team award 9 s and the final GC podium 16 s. An ordinary stage ceremony runs
  about 58 s (was about 1 min 50 s) and the final stage about 74 s. Reduced
  motion keeps the short static version.
- **Fixed shot list for every award.** A whip-pan in, then a wide low shot as
  the rider jogs in from the wing and hops onto the podium. The camera pushes
  in to a medium shot with a slight orbit for the hand-off and jersey reveal,
  then holds a hero close-up (zoom about 1.45) for the celebration. It eases
  back while the rider waves. The rider stays on stage and jogs off as the next
  one arrives.
- **One continuous camera.** A single keyframe track covers the whole
  programme, using monotone Hermite curves for x, y, zoom and roll. Nothing
  resets between awards. The 96% black dip is gone; a whip-pan with
  motion-blur streaks and a diagonal wipe in the award colour replaces it. The
  intro is a crane move down from the sky with a "GRAND TOUR · STAGE" title.
- **GC finale.** Riders enter in the order 3 → 2 → 1. The champion and
  presenter share the trophy grip, then the champion lifts it overhead with a
  stretch. The runners-up spray champagne (original unlabelled bottles), gold
  streamers fall, and the camera ends on a wide shot.
- **Bright cartoon art.** The set is drawn in three parallax layers: sky and
  clouds (0.2), mountains and town (0.5, cached) and the stage (1.0, cached),
  plus a live crowd foreground at 1.25. The art adds a sky gradient with
  drifting clouds, sun rays, bunting, a balloon arch and a yellow and green
  stage. Podium blocks are bold, outlined and numbered. The final stage adds an
  original Paris skyline silhouette. There are no real sponsor marks.
- **Cartoon cast.** Characters are about four heads tall, with thick outlines,
  two-tone cel shading, large eyes with highlights, blinks, brows and smile,
  cheer, grit and surprise mouths. They squash on landing and stretch on the
  lift, and the hem and hair move with them. Legs stay fixed-length IK chains
  on the existing `CeremonyGeometry` footsteps, so feet do not slide or sink.
  Each award has its own celebration: a fist-pump jump for the stage winner,
  open arms for yellow, a sprint crouch and "zoom" pop for green, pointing to
  the mountains for polka, a shy wave for white, synchronized jumps for the
  team and the trophy lift for GC. A wipe changes the team kit into the award
  jersey.
- **Particles and post effects.** Confetti cannons, streamers and champagne
  droplets are worked out from fixed seeds and the elapsed time, so pausing and
  seeking give the same frame, with at most 220 live particles. The finish also
  has photographer flashes with bloom, a hero glow and a vignette.
- **Overlay.** An award title card slams in. The lower third slides in behind
  a colour bar, the name pops, and the result rolls in like slot digits before
  settling on the recorded value. GC name cards flip in as each rider arrives,
  and the champion's card has a pulsing gold border. The progress bar is split
  into one segment per award.
- **Player.** Darker theatre with a glow in the award colour. The header shows
  the current award. Chapter buttons have colour dots and per-award progress,
  and the "next" button shows progress too. Keyboard, focus trap, `inert`, Esc
  to skip and Space to pause behave as before.

The ceremony still only reads the frozen snapshot. It never calls `Race.tick`,
writes the ledger or uses the race RNG, and `Ceremony.plan` award selection has
not changed.

## Front-end polish (DOM/CSS only)

- Buttons lift on hover and press down on click. They have a yellow
  `:focus-visible` ring, a light sheen sweeps across primary buttons, and
  disabled buttons are clearer.
- Home screen: the hero text rises in stagger, the tour facts count up, and
  featured stage cards lift and tilt on hover.
- Race HUD: speed, power and W/kg ease between updates. This is display-only;
  the simulation values are unchanged. Gauge bars move smoothly and pulse when
  low, the final kilometre is highlighted, and the attack button shows a
  cooldown bar.
- Results: the place number counts up, metric cards appear in stagger, the
  podium blocks rise in order 3 → 2 → 1, and the blocks have gold, silver and
  bronze accents.
- Dialogs scale in over a blurred backdrop.
- Every animation respects `prefers-reduced-motion`.

## Verification

See `tests/v26/README.md` and `tests/v26/evidence/v26-summary.json`. The
`v26-verify.yml` workflow runs only when the V26 file, the V25 baseline,
`tests/v26` or the workflow itself changes, and it does not deploy.
