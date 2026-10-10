<h1 align="center">🚴 GRAND TOUR</h1>

<p align="center">
  <strong>One tour. Twenty-one stages. Every decision carries forward.</strong>
</p>

<p align="center">
  An independent road-cycling simulation where terrain, timing, fatigue, and race craft<br>
  turn a grand stage race into something you can actually play.
</p>

<p align="center">
  <a href="Grand-Tour-V25.html"><strong>▶ Open V25 Offline</strong></a>
  &nbsp;·&nbsp;
  <a href="#inside-the-race">🏁 The Race</a>
  &nbsp;·&nbsp;
  <a href="#read-the-road">🗺️ Race Tactics</a>
  &nbsp;·&nbsp;
  <a href="#play-online-or-offline">💻 Play Offline</a>
  &nbsp;·&nbsp;
  <a href="#for-developers">⚙️ Development</a>
</p>

<p align="center">
  <sub>21 STAGES &nbsp;·&nbsp; 184-RIDER START LIST &nbsp;·&nbsp; SIX RIDER ROLES &nbsp;·&nbsp; ONE SELF-CONTAINED HTML GAME</sub><br>
  <sub>CURRENT RELEASE: V25 · LIVE ON GITHUB PAGES</sub>
</p>

<p align="center">
  <img width="760" alt="Grand Tour — original cycling simulation project artwork" src="https://github.com/user-attachments/assets/300cdadc-19bd-47db-8b60-7d4928db8afa" />
</p>

---

> **A race is more than its finish line.**
>
> A sprinter wants a clean run-in. A climber waits for the road to rise. A general-classification contender has to think beyond today. In Grand Tour, the result emerges from the road, the riders, and the choices made between the start and the line.

<a id="inside-the-race"></a>
## 🏁 Inside the Race

Grand Tour is a **playable, multi-stage road-racing simulation**, not a static cycling animation. Its race engine tracks riders, groups, timing, effort, and results over a complete 21-stage tour.

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>🗺️ Twenty-One Stages</h3>
      <p><sub>FLAT ROADS · MOUNTAINS · ITT · TTT</sub></p>
      <p>Move between different terrain profiles and racing formats. A flat-stage finish demands different decisions from a summit battle or a time trial.</p>
    </td>
    <td width="50%" valign="top">
      <h3>🎽 Six Rider Roles</h3>
      <p><sub>GC · SPRINTER · CLIMBER · PUNCHEUR · ALL-ROUNDER · TT</sub></p>
      <p>Rider strengths and objectives shape how each race unfolds. There is no universal strategy that works for every specialty.</p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>🚴 A Living Peloton</h3>
      <p><sub>GROUPS · BREAKAWAYS · CHASES · LEADOUTS</sub></p>
      <p>Watch riders separate, regroup, cooperate, respond to attacks, and organize for a finish. Position and group behavior are part of the race.</p>
    </td>
    <td width="50%" valign="top">
      <h3>⚡ Effort Has a Cost</h3>
      <p><sub>PACING · POWER · ENERGY · FATIGUE</sub></p>
      <p>Choose when to spend energy, when to follow, and when to recover. The strongest move is not always the earliest one.</p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>🌦️ The Road Changes</h3>
      <p><sub>GRADIENT · WEATHER · DESCENTS</sub></p>
      <p>Climbs, descents, shifting conditions, and stage environments influence the situation and how the race looks from the roadside.</p>
    </td>
    <td width="50%" valign="top">
      <h3>🏆 Every Result Matters</h3>
      <p><sub>STAGE WINS · OVERALL STANDINGS · JERSEYS</sub></p>
      <p>Follow stage classifications, the general classification, and the familiar yellow, green, polka-dot, and white jersey contests.</p>
    </td>
  </tr>
</table>

<a id="read-the-road"></a>
## 🧭 Read the Road. Make the Move.

<p align="center"><code>STUDY THE STAGE &nbsp;→&nbsp; MANAGE EFFORT &nbsp;→&nbsp; RESPOND TO THE RACE &nbsp;→&nbsp; FINISH</code></p>

1. **Understand the course.** The route profile, gradient, race situation, and remaining distance all change what a good move looks like.
2. **Manage your rider.** Balance pacing and recovery against the moments when accelerating or attacking is worth the cost.
3. **React to the peloton.** Use following, attacks, automatic riding, and race information to respond to rivals and moving groups.
4. **Race for the line.** Sprint finishes, climbs, time trials, and team efforts reward different combinations of timing and rider strengths.

The game also provides a **Race Centre**, team-radio-style information, feeding decisions, pause controls, and an animated results and ceremony sequence. These are part of playing the event—not merely watching a pre-rendered video.

### 🏔️ Four Kinds of Race, Different Demands

| Race format | What changes |
| --- | --- |
| **Road stages** | Peloton positioning, attacks, breakaways, and the finish approach |
| **Mountain stages** | Sustained climbing effort, gaps, descending, and GC pressure |
| **Individual Time Trial (ITT)** | A rider's solo effort against the clock |
| **Team Time Trial (TTT)** | Team formation, pacing, and coordinated rotation |

## 🎬 From Roadside to Podium

V25 improves save ownership and recovery, provisional standings, and scenery continuity while preserving the established simulation. The existing riding and award systems have been retained and rechecked.

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>🚴 Riding That Responds</h3>
      <p>Pedaling, body posture, out-of-saddle efforts, descending stance, and finishing motion respond to the rider's actual state rather than being a disconnected loop.</p>
    </td>
    <td width="50%" valign="top">
      <h3>🌄 A Changing Landscape</h3>
      <p>Mountains, fields, forests, villages, lakeside roads, and the Paris finale follow the course, weather, and stage surroundings.</p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>📡 A Clearer Broadcast</h3>
      <p>Camera framing and race information respond to peloton density, gradients, and distance to the finish. The HUD gives the racing room to breathe.</p>
    </td>
    <td width="50%" valign="top">
      <h3>🥇 A Proper Ceremony</h3>
      <p>Stage winners, jersey presentations, and the final overall-classification podium get their own sequences, tied to actual race results.</p>
    </td>
  </tr>
</table>

> [!NOTE]
> **V25 is a released, audited source.** Its local fixes address confirmed storage and presentation faults; the audited candidate was subsequently merged into `main` and deployed to GitHub Pages. Race physics, AI, timing and seeded results remain unchanged, and the expanded flat-stage survey still identifies an unresolved Sprinter balance signal. [V25-AUDIT-REPORT.md](V25-AUDIT-REPORT.md) records the evidence and limits exactly as observed during the **pre-release candidate audit** and is retained unmodified.

<a id="play-online-or-offline"></a>
## 🚀 Play Online or Offline

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>🌐 V25 Release — Play Online</h3>
      <p><sub>GITHUB PAGES · NO BUILD</sub></p>
      <p>V25 is live at <a href="https://seiya058904.github.io/Grand-Tour/"><code>seiya058904.github.io/Grand-Tour</code></a>. The packaged <a href="index.html"><code>index.html</code></a> entry redirects to the released <code>Grand-Tour-V25.html</code>.</p>
      <p><strong><a href="https://seiya058904.github.io/Grand-Tour/">Open the live game →</a></strong></p>
    </td>
    <td width="50%" valign="top">
      <h3>📄 Single HTML — Play Offline</h3>
      <p><sub>SELF-CONTAINED · NO BUILD · NO SERVER</sub></p>
      <p>Open <a href="Grand-Tour-V25.html"><code>Grand-Tour-V25.html</code></a> and open it in a modern browser. The game does not require npm or external runtime libraries.</p>
      <p><strong><a href="Grand-Tour-V25.html">Open the standalone HTML →</a></strong></p>
    </td>
  </tr>
</table>

### 📦 Source Package and Historical Baseline

`Grand-Tour-V25-Source.zip` contains the V25 entry, unchanged latest V24 HTML, required V20–V23 baselines, retained V22–V24 tests, V25 tests and audit documentation. It includes a full SHA-256 manifest and opens at **`Grand-Tour-V25/index.html`** after extraction.

The authoritative V24 input came from commit `3e92128c0cb353d267c12ceeaf143bda663a7b26`; its HTML SHA-256 is `b5d0899fad82ed6576f416e12267ec6d369405a4dfa56559e5629e6fcf00fa1f`. The older sealed V24 Final ZIP was intentionally omitted from the cloud handoff. Its absence is not a missing game dependency. The V25 packager builds directly from this source tree.

### 💾 Progress and Compatibility

The game retains its existing **V9-format save compatibility** and historical-tour migration behavior. Browser and file origins may keep different local storage, so preserve a backup before clearing browser data or changing where you play. Current development treats save integrity and recovery as part of the simulation contract.

## 🗂️ Current Source and Preserved Baselines

| Resource | Purpose |
| --- | --- |
| [`Grand-Tour-V25.html`](Grand-Tour-V25.html) | Current released source (also playable offline) |
| [`V25-AUDIT-REPORT.md`](V25-AUDIT-REPORT.md) | Findings, fixes, actual verification and unresolved risks |
| [`V25-CHANGELOG.md`](V25-CHANGELOG.md) | Concise change history |
| [`tests/v25/README.md`](tests/v25/README.md) | Current reproduction and packaging commands |
| [`Grand-Tour-V24.html`](Grand-Tour-V24.html) | Unchanged latest authoritative V24 baseline |
| [`V24-REPORT.md`](V24-REPORT.md) | Original V24 evidence, not V25 acceptance |
| [`archive/README.md`](archive/README.md) | Historical source and report index; some old evidence is intentionally outside this handoff |

All 65 retained historical source, report and test files have explicit baseline hashes in `tests/v25/baseline-hashes.json`. V22/V23 remain necessary compatibility references.

<a id="for-developers"></a>
## ⚙️ For Developers

Grand Tour is built around **one authoritative HTML game file**, not a conventional frontend framework. The current source, previous baselines, and separate verification scripts are maintained in the same repository.

<details>
<summary><strong>🛠️ Expand local verification and engineering boundaries</strong></summary>

### Local preview

For browser-based inspection from the repository root:

```powershell
python -m http.server 4187 --bind 127.0.0.1
```

Open **http://127.0.0.1:4187/**. To use the offline edition itself, simply open `Grand-Tour-V25.html` as a file instead.

### Focused regression checks

The engineering checks use Node.js and Python; real-browser acceptance additionally requires Python Playwright with Chromium. Create an evidence directory outside the repository and set `$evidence` to that absolute path before running tests.

```powershell
python tests/v25/static_verify.py --out "$evidence/static.json"
node tests/v25/core-parity.cjs Grand-Tour-V24.html Grand-Tour-V25.html "$evidence/core-parity.json"
node tests/v25/focused.cjs Grand-Tour-V25.html archive/v22/Grand-Tour-V22.html "$evidence/focused.json"
node tests/v24/save-finish-boundary.cjs Grand-Tour-V25.html "$evidence/save-finish-boundary.json"
python tests/v24/browser_verify.py --source Grand-Tour-V25.html --out "$evidence/browser"
```

Additional checks cover full-tour results, save ownership, TTT positioning, race animation, weather, ceremonies, and offline-package integrity. The exact workflows and prerequisites live in [`tests/v25/README.md`](tests/v25/README.md).

### Engineering priorities

- **Preserve determinism.** Race logic, timing, rider states, classification, and saved results must remain internally consistent.
- **Keep the game standalone.** The current delivery must stay playable without a package manager or network runtime.
- **Respect save history.** Maintain V9 compatibility, the existing restore rules, and prior valid snapshots.
- **Do not rewrite the baseline.** Historical HTML, tests, evidence, and the frozen ZIP are comparison artifacts, not disposable duplicates.
- **Verify presentation separately.** More natural riding or prettier scenery should not silently change the underlying race outcome.

See [`AGENTS.md`](AGENTS.md) for the complete repository-specific guardrails.

</details>

## 📜 Independent Project & Rights

Grand Tour is an **independent, unofficial cycling simulation**. It is not affiliated with the Tour de France organizers, teams, or represented riders. No project-wide open-source license is declared; a publicly viewable repository is not a blanket permission to redistribute the game or its artwork.

---

<p align="center">
  <sub>READ THE ROAD. CHOOSE YOUR MOMENT. RACE THE WHOLE TOUR.</sub><br>
  <sub>Grand Tour · Twenty-one stages of tactics, endurance, and spectacle.</sub>
</p>
