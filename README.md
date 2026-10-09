# 🚴 Grand Tour

**A stage race you can actually play — inside a single HTML file.**

An unofficial road-cycling stage-racing simulation built around the tension between pacing, terrain, tactical roles and the final sprint.

**[▶ Play V24](https://seiya058904.github.io/Grand-Tour/)** · [Download single-file HTML](Grand-Tour-V24.html) · [Frozen V24 package](Grand-Tour-V24-Final.zip) · [What's in V24](#v24-and-historical-builds)

<img width="760" alt="Grand Tour cycling project artwork" src="https://github.com/user-attachments/assets/300cdadc-19bd-47db-8b60-7d4928db8afa" />


## 🏁 The race

Across a stage race, a sprinter's priorities are not those of a climber or overall contender. Reading the terrain and controlling effort matter as much as a finishing burst.

Grand Tour is not a static visualization of cycling. It simulates a multi-stage road race in which rider strengths, race situations and your tactical decisions affect how the competition unfolds.

| Race dimension | In the game |
| --- | --- |
| **Stages & terrain** | Different courses, elevation changes and racing situations |
| **Rider specialties** | GC, sprinting, climbing, all-round ability and time-trial strengths |
| **Race dynamics** | Groups, pursuit, pace, fatigue and late-race finishing decisions |
| **Classification** | Stage results and overall race standings |
| **Presentation** | Rider motion, regional scenery, race information and podium sequences |

V24 concentrates on riding motion, scenery, camera framing and race information while retaining the prior simulation contracts. Those presentation upgrades should not be confused with an unverified rewrite of race physics.

## Play online or offline

**Online:** Open [GitHub Pages](https://seiya058904.github.io/Grand-Tour/). The `index.html` page is an entry/redirect to the current official game.

**Offline:** Download [`Grand-Tour-V24.html`](Grand-Tour-V24.html) and open it in a modern browser. It is self-contained and does not require npm, a package build or external runtime libraries.

**Packaged version:** [`Grand-Tour-V24-Final.zip`](Grand-Tour-V24-Final.zip) is a frozen release artifact with its own historical byte identity. Later edits to the standalone HTML do **not** silently update the ZIP.

## V24 and historical builds

| Resource | Why it matters |
| --- | --- |
| [`Grand-Tour-V24.html`](Grand-Tour-V24.html) | Current standalone game |
| [`V24-REPORT.md`](V24-REPORT.md) | Iteration and verification scope |
| [`tests/v24/README.md`](tests/v24/README.md) | Reproduction of current checks |
| [Verification workflow](https://github.com/seiya058904/Grand-Tour/actions/workflows/v23-verify.yml) | Continued regression checks, including retained earlier-version baselines |
| [`archive/README.md`](archive/README.md) | Historical versions and recoverable ZIPs |

**Compatibility matters:** V24 retains prior V23 simulation behavior and V9 save compatibility. Historic V21/V22/V23 packages and baselines are documented through the archive and Git history; they are not disposable merely because the homepage focuses on V24.

## Development and checks

The canonical source is an HTML document, not a conventional npm application. Serve the repository locally if you need a browser-based test environment:

```powershell
python -m http.server 4187 --bind 127.0.0.1
```

Additional Node/Python checks, save-boundary regressions and browser acceptance commands are documented in [`tests/v24/README.md`](tests/v24/README.md) and [`AGENTS.md`](AGENTS.md). Verification evidence should be written outside the repository or to an ignored output directory; do not modify the frozen release ZIP for documentation work.

## Independent project / rights

This is an **independent, unofficial** project. It is not affiliated with Tour de France organizers, cycling teams or represented riders. No project-wide open-source license has been selected; public source access alone does not confer a redistribution license.
