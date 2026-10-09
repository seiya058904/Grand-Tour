# V25 验证与复现指南

正式入口是根目录 `index.html`，跳转到 `Grand-Tour-V25.html`。游戏本身仍为单 HTML、自包含、可离线运行；下面的依赖只服务于工程验证。

V24 对照必须使用交接包根目录的最新 `Grand-Tour-V24.html`，对应权威提交 `3e92128c0cb353d267c12ceeaf143bda663a7b26`，HTML SHA-256 为 `b5d0899fad82ed6576f416e12267ec6d369405a4dfa56559e5629e6fcf00fa1f`。`archive/v20` 至 `archive/v23` 和 `tests/v22` 至 `tests/v24` 保持历史字节；`baseline-hashes.json` 是保留清单。

## 环境与证据约定

从项目根目录运行。验证配置使用 Node.js 24、Python 3.12、Python Playwright 1.56.0 与其 Chromium。Node 脚本使用内置模块和包内引擎加载器，不需要 npm/Vite。Python 浏览器脚本需要在运行它们的同一 Python 环境安装 Playwright、Chromium 及浏览器系统依赖；中文截图还需要系统中文字体。Linux 的安装示例：

```bash
python -m pip install playwright==1.56.0
python -m playwright install --with-deps chromium
```

`render_cache_pixels.py` 另需 Pillow（本次使用 12.3.0，可用 `python -m pip install Pillow==12.3.0` 安装），用于把浏览器 PNG 解码成 RGBA 后逐字节比较。它不属于游戏依赖。

安装验证工具可能需要联网；已安装后，游戏离线验收不依赖外部资源。浏览器使用独立 context/profile；多标签存档测试自建 `127.0.0.1` 临时端口服务，其他原生入口检查使用 `file://`。不连接玩家正在使用的浏览器。

以下 Bash 示例将输出放在项目外的新目录。PowerShell 可把 `GT25_EVIDENCE` 设置为项目外的绝对路径，并先创建该目录。

```bash
GT25_EVIDENCE="$(mktemp -d -t grand-tour-v25-evidence-XXXXXX)"
```

JSON 保存该次运行的源文件哈希、条件和结果；部分历史脚本逐场写入中间报告，因此文件存在不等于运行完成。检查退出码、最终 `pass`/`failed` 和完整 case/stage 数量。没有统一计数结构的历史脚本应保留日志，并按实际断言范围汇总，不能把缺席的检查记为通过。

交付时选入的轻量证据位于 `tests/v25/evidence/`；详细适用范围见 `V25-AUDIT-REPORT.md` 与包内 `PROVENANCE.json`。重新运行产生的截图、视频、自然大快照、日志和临时解压目录应留在外部证据目录。V24/V23 旧报告中的 PASS 只说明旧版本当时的验证，不能代替本次运行。

## 1. 基线、35 项回归与 14 族签名

```bash
python tests/v25/static_verify.py --out "$GT25_EVIDENCE/static.json"
node tests/v25/core-parity.cjs Grand-Tour-V24.html Grand-Tour-V25.html "$GT25_EVIDENCE/core-parity.json"
node tests/v25/focused.cjs Grand-Tour-V25.html archive/v22/Grand-Tour-V22.html "$GT25_EVIDENCE/focused.json"
node tests/v24/save-finish-boundary.cjs Grand-Tour-V25.html "$GT25_EVIDENCE/save-finish-boundary.json"
node tests/v23/ttt-wheel.cjs Grand-Tour-V25.html "$GT25_EVIDENCE/ttt-wheel.json"
node tests/v23/storage-ownership.cjs Grand-Tour-V25.html > "$GT25_EVIDENCE/storage-ownership.log" 2>&1
```

`focused.cjs` 在内存中载入未修改的 V24 原测试，只替换 build 版本断言 `240 → 250`、对应测试名称和默认 HTML 文件名。所有 35 项行为断言、历史故障快照和加载路径保留。**必须传入 V22 基线**，否则原测试会不执行三个由 `if(O)` 包围的历史兼容/TT 轨迹检查，不能报告 35 项完整回归。

`core-parity.cjs` 对下列 14 族比较源签名：

`Race`、`Physics`、`Physiology`、`Fatigue`、`Weather`、`RaceTiming`、`TeamClassification`、`Classification`、`TimeLimits`、`CompactCourse`、`SaveCodec`、`SimulationClock`、`RIDER_DATA`、`STAGE_DATA`。

其中 13 族要求完全一致。唯一例外为 `SaveCodec.decode` 中精确列明的恢复入口：`recover:true` 遇到 active 迁移失败时，先用同一迁移流程校验去除 active 后的外层存档，再保留已验证的历史赛段。严格导入仍拒绝错误。脚本要求新旧入口各出现一次，仅将这一段还原后比较整个族签名；它不会忽略任意其他差异。

签名范围不覆盖所有全局辅助函数。V25 的关门线校验辅助函数、实时积分榜读模型、存储写入与渲染分别由下面的专项回归覆盖。不要把 14 族签名通过解释为所有源码完全相同。原 `tests/v24/core-parity.cjs` 保留其 V23/V24 历史规则，未为 V25 改写。

`static_verify.py` 同时检查 V25 标识、离线资源、JavaScript 语法、唯一 DOM ID、正确入口、V9 存储身份和全部保留文件哈希。`save-finish-boundary.cjs` 直接运行原 V24 存档终点边界断言，未删改。

## 2. V25 最小故障回归与存档浏览器边界

```bash
node tests/v25/storage-first-settings.cjs Grand-Tour-V25.html "$GT25_EVIDENCE/storage-first-settings.json"
node tests/v25/storage-validation.cjs Grand-Tour-V25.html "$GT25_EVIDENCE/storage-validation.json" "$GT25_EVIDENCE/validation-fixtures"
node tests/v25/simulation-live-standings.cjs Grand-Tour-V25.html "$GT25_EVIDENCE/live-standings.json"
node tests/v25/render-continuity.cjs Grand-Tour-V25.html "$GT25_EVIDENCE/render-continuity.json"
node tests/v25/render-score-parity.cjs Grand-Tour-V24.html Grand-Tour-V25.html "$GT25_EVIDENCE/render-score-parity.json"
python tests/v25/storage-first-settings-browser.py --source Grand-Tour-V25.html --validation-fixtures "$GT25_EVIDENCE/validation-fixtures" --out "$GT25_EVIDENCE/storage-first-settings-browser"
python tests/v24/save-finish-browser.py --source Grand-Tour-V25.html --out "$GT25_EVIDENCE/save-finish-browser"
```

| 脚本 | 精确范围与输入 |
| --- | --- |
| `storage-first-settings.cjs [source] [out]` | 执行生产存储处理函数，检查首次设置写入后的进度所有权、同页首次 Tour、旧页冲突和有/无 Web Locks 分支。失败写入和重试由原 `storage-ownership.cjs` 另行覆盖。默认 source 为 V25。 |
| `storage-validation.cjs [source] [out] [fixtureDir]` | 自然 TTT/公路/ITT 首位过线、完整成绩、两套时间模型、合法 OTL 和历史迁移；逐字段损坏 cutoff、active 迁移恢复、原始备份与有效成绩保留。默认 source 为 V25。 |
| `simulation-live-standings.cjs source [out]` | 六个定向读模型条件，检查当日赛段胜场计入临时绿衫同分排序、TTT 例外、重复读取幂等及 prior 不变。它是明确构造的最小读模型测试，不是自然比赛采样。 |
| `render-continuity.cjs [source] [out]` | 五项检查；31 对由 V24 自然轨迹记录的场景坐标、终点观众边界和渲染纯度。默认 source 为 V25。 |
| `render-score-parity.cjs [baseline] [candidate] [out]` | 两版真实 `RaceView` 观察同一条自然比赛轨迹，比较平路、山地、TTT、ITT 的完整视图状态与物理不变性，约束评分复用的行为等价性。默认根目录 V24/V25。 |
| `render-harness.cjs` | 供连续性测试使用的生产 painter 提取与 Canvas 调用记录助手；没有独立 CLI。 |

Canvas 身体缓存复用的像素回归需要第四节生成的自然场景：

```bash
python tests/v25/render_cache_pixels.py --source Grand-Tour-V25.html --reference Grand-Tour-V24.html --scenes "$GT25_EVIDENCE/scenes" --out "$GT25_EVIDENCE/cache-pixels"
```

`--source`/`--reference` 分别默认根目录 V25/最新 V24。助手 `render_cache_source.py` 只从 V24 提取旧 `cachedCyclistBody` 函数，替换进当前 V25 的临时对照页；其余源码包括景物、模拟、布局和身体 painter 都保持当前 V25。**这是隔离缓存变更的混合测试对照，不是完整 V24 画面。** 两个输入文件不改写；报告保存它们、提取函数、临时对照页和快照的哈希。

测试对平路集团/山地各 48 个完整 Canvas 帧进行 RGBA 逐字节比较，并比较命中、未命中、重画和淘汰计数。两项压力检查在一次 JavaScript 任务中绘制 320 个不同 key，超过 256 容量，最后才读取像素；其中一项先污染被淘汰画布的 clip、transform、透明度、合成、虚线、阴影和 filter，验证宽高重置清除状态。共 98 项像素检查及整体计数/纯度门槛。测试固定展示时钟、手动推进自然比赛，用于内容等价性，不能据此报告实时性能。

`storage-validation.cjs` 的 `fixtureDir` 参数可选；提供时生成 `natural-first-finish.json`、`natural-completed-record.json` 和 `natural-second-stage-save.json`。浏览器的 `--validation-fixtures` 使用第一、第三个文件，通过真正的文件导入、刷新和按钮操作检查严格拒绝、备份保护及损坏 active 后继续下一站，覆盖有/无 Web Locks 与桌面/390 宽度。**省略该参数会缺少这一组新增浏览器边界**，仍能运行首次设置/多页面基础流程，但不代表完整存档验收。

## 3. 两版完整 21 站及结果精确对照

下列是计算量较大的自然固定步长模拟。两版使用同一公开 GC 玩家策略和种子；生成的整份 V9 对象必须逐字段相等。

```bash
node tests/v23/tour-simulation.cjs Grand-Tour-V24.html "$GT25_EVIDENCE/v24-tour-314159.json" 314159
node tests/v23/tour-simulation.cjs Grand-Tour-V25.html "$GT25_EVIDENCE/v25-tour-314159.json" 314159
node tests/v25/simulation-tour-parity.cjs "$GT25_EVIDENCE/v24-tour-314159-tour.json" "$GT25_EVIDENCE/v25-tour-314159-tour.json" "$GT25_EVIDENCE/v24-tour-314159.json" "$GT25_EVIDENCE/v25-tour-314159.json" "$GT25_EVIDENCE/tour-parity.json"
node tests/v25/full-tour-compatibility.cjs Grand-Tour-V24.html Grand-Tour-V25.html "$GT25_EVIDENCE/v24-tour-314159-tour.json" "$GT25_EVIDENCE/full-tour-compatibility.json"
```

`tour-simulation.cjs source report.json [seed]` 默认种子为 `314159`，同时生成 `report-record.json`（末站成绩）和 `report-tour.json`（完整 V9）。请使输出文件名以 `.json` 结尾。它沿用原公开操作策略、实际疲劳/分类继承并定期恢复自然快照，不等于人工连续游玩 21 站。

`simulation-tour-parity.cjs baseline-tour candidate-tour baseline-report candidate-report [out]` 校验同种子、两版各 21 个完整赛段与恢复记录，然后比较**整个解析后的 V9 对象**。墙钟运行耗时、源路径等只存在驱动报告中，不参与成绩对象比较；没有删去成绩字段以求一致。

`full-tour-compatibility.cjs baseline-html candidate-html old-tour.json out.json` 不推进比赛，直接让两版严格解码同一份 V24 自然 Tour，检查零 issues、全部成绩保留、输入不变和完整规范化输出一致。此夹具明确限定上面的 seed `314159` / `standard-GC-v2`，末站 162 人完赛是这一条自然轨迹的预期值，不是其他种子的通用规则。规范化会补齐模拟导出中的默认 settings，因此规范化文件哈希与原始导出哈希分别记录。

## 4. 三种子 × 七赛段、九种自然场景与职业调查

```bash
node tests/v24/race-audit.cjs Grand-Tour-V25.html "$GT25_EVIDENCE/race-audit.json" - "$GT25_EVIDENCE/v24-tour-314159-tour.json"
```

这是未修改的 V24 驱动。固定种子为 `12345,271828,2058765`，赛段为 `1,3,5,7,16,19,21`，共 21 场。第 19 站从提供的完整 Tour 取第 18 站真实成绩，其余为明确的新建单站条件。每 60 个模拟秒检查 raw/compact 快照并各继续 50 步，检查有限数值、生理边界、184 人账本、最终结束和比赛不变量。

第三个参数 `-` 表示本次不读另一份 21 场结果哈希报告，所以该报告的 `parity` 为 `null`，不能将其算作历史结果对照通过。结果一致性由上一节两版完整 Tour 的严格比较覆盖。若未来需要逐场结果比较，先在另一个输出目录用 V24 和相同 prior 运行，再把那份报告作为第三个参数；不要拿其他 prior 或不同玩家策略的报告比较。

驱动在输出 JSON 同级自动创建 `scenes/`，按真实条件保存 `ttt`、`descent`、`peloton`、`breakaway`、`leadout`、`sprint`、`itt`、`climb`、`gc-battle` 的 `*-snapshot.json`。检查报告的 `snapshots` 列表及九个文件；未自然出现某个条件时不能注入局势伪造场景。

职业样本与策略路径调查使用独立脚本：

```bash
node tests/v25/simulation-survey.cjs Grand-Tour-V25.html "$GT25_EVIDENCE/survey-flat.json" 42,2026,65537,3735928559 flat
```

CLI 为 `source out [逗号分隔种子] [flat|逗号分隔的一基赛段编号]`。默认种子即上述四个，`flat` 自动选全部平路。报告记录末段节点、冲刺手资格/位置/体力、车队目标、突围、追击、最先冲线车手、恢复和不变量。该策略是孤立自然赛段中的公开 Auto/补给操作，没有注入胜者。样本受车手能力、赛段和玩家策略影响；不能只凭职业胜率就改平衡，也不能把样本统计的 case 数当作功能测试断言数。

## 5. 真实浏览器、演出与手工画面检查

```bash
python tests/v24/browser_verify.py --source Grand-Tour-V25.html --out "$GT25_EVIDENCE/browser"
python tests/v25/ui_verify.py --source Grand-Tour-V25.html --out "$GT25_EVIDENCE/ui"
python tests/v25/legacy_browser.py presentation --out "$GT25_EVIDENCE/presentation"
python tests/v25/legacy_browser.py scenes --scenes "$GT25_EVIDENCE/scenes" --out "$GT25_EVIDENCE/scenes-played"
python tests/v25/legacy_browser.py finish --out "$GT25_EVIDENCE/finish"
python tests/v25/legacy_browser.py downhill --out "$GT25_EVIDENCE/downhill"
python tests/v25/legacy_browser.py weather --out "$GT25_EVIDENCE/weather"
python tests/v25/legacy_browser.py sequence --record "$GT25_EVIDENCE/browser/stage-05-physical.json" --tour "$GT25_EVIDENCE/v25-tour-314159-tour.json" --out "$GT25_EVIDENCE/sequence" --play
python tests/v25/continuity_browser.py --out "$GT25_EVIDENCE/continuity-playback"
```

`ui_verify.py` 检查 320、390、768、1920×1080、3840×2160 和 1920 DPR2，包含主要控件、名牌几何、移动 Race Centre、键盘/嵌套暂停、原生离线入口及 console。`legacy_browser.py suite ...` 只在内存中把保留 V24 浏览器套件的文件目标和精确版本标题替换为 V25，其他断言、等待和交互不变；所有后续参数原样转交。合法 suite 是 `presentation`、`finish`、`downhill`、`scenes`、`weather`、`sequence`、`live`。未列的 suite 会拒绝。

`sequence --play` 用真实 1× 播放普通及 Tour 最终领奖；省略 `--play` 只运行其余断言，不能声称看过整段播放。该命令依赖前面浏览器生成的自然第 5 站成绩和完整 Tour。原 `browser_verify.py`、`finish`、`downhill` 保留可选 `--injected` 诊断模式；正式原生入口验收不要加此开关。

`continuity_browser.py [--snapshots DIR] --out DIR` 在同一浏览器依次播放 V24/V25 的村落、林线和终点人群边界，全画质、1440×1000、DPR1、真实 RAF。默认从生产引擎自然重建 stage 5/19、seed `2058765`、t `9.5/127/268.1`；可选快照目录须含 `natural-village-before.json`、`natural-tree-line-before.json`、`natural-finish-crowd-before.json`。每组输出 `frame-0.png` 至 `frame-6.png` 和视频。样本截取之间的截图开销会使各版时刻略有不同，逐帧像素相等不是这个测试的目标。

若需保留的五段交互/自然局势播放，`live` 还需要专用 showcase 文件名，不能把九场景目录直接替代：

```bash
node tests/v23/showcase.cjs "$GT25_EVIDENCE/showcase-v23" "$GT25_EVIDENCE/v24-tour-314159-tour.json"
python tests/v25/legacy_browser.py live --evidence "$GT25_EVIDENCE/showcase-v23" --out "$GT25_EVIDENCE/live"
```

`showcase.cjs` 保留 V23 生产引擎作为自然快照来源，输出 provenance；V25 在真实浏览器恢复并播放这些历史兼容场景。这组证据应明确标为“V23 来源快照在 V25 播放”，不冒充 V25 新生成场景。

几何、状态和 `pageerror` 断言不能证明动画好看。必须实际查看截图/视频，区分画面内部物体瞬间出现、正常从视口边缘进入、镜头移动、名牌淡入淡出与数据更新。检查骑手踩踏和车身接触、冲线到确认、领奖完整动作及移动布局。静帧不能证明 60 FPS，也不能代替实际设备上的触摸、字体和高 DPI 可读性验收。

## 6. 独占 ABBA 性能与连续运行

**停止其他模拟、浏览器回归、打包和性能任务后，单独运行。** 不要用并发功能测试中的 FPS 与这一结果比较。

```bash
python tests/v25/performance_probe.py --scenes "$GT25_EVIDENCE/scenes" --out "$GT25_EVIDENCE/performance.json" --seconds 8 --soak-seconds 180
```

CLI 的 `--scenes`、`--out` 必填，`--seconds` 默认 8，`--soak-seconds` 默认 180，传 0 可明确省略连续运行。每种 `peloton/climb/leadout` 采用 `V24 → V25 → V25 → V24` 顺序，同一个 Chromium、1440×1000、DPR1、全画质、同一自然快照、2 秒预热，实际 1× RAF 和生产固定步长。两版均只屏蔽周期存储 I/O，存储另测；不冻结比赛获取性能数字，不减少画质或模拟计算。

报告记录源/快照哈希、浏览器/平台、FPS、frame/CPU/debt 的 P50/P95/P99/max、>33.34/50 ms 帧数、Long Tasks、模拟/墙钟比、CDP 堆和缓存。强制 GC 只在 ABBA 采样窗口之外执行；连续山地 soak 每 30 秒保存运行片段，另取前后回收后堆。`pass` 是质量、有限状态、欠账、模拟实际推进和运行健康门槛，并不是 FPS 优于 V24 的声明。性能改善须根据同条件的成对测量解释；Linux headless 共享主机不能代替实体手机/桌面 GPU，180 秒也不能证明数小时无泄漏。

下列诊断同样独占运行，且不能和正式 ABBA 的未插桩数值混用：

```bash
python tests/v25/render_cache_probe.py --source Grand-Tour-V25.html --reference Grand-Tour-V24.html --scenes "$GT25_EVIDENCE/scenes" --out "$GT25_EVIDENCE/cache-probe.json" --seconds 6
python tests/v25/render_profile.py --snapshot "$GT25_EVIDENCE/scenes/peloton-snapshot.json" --out "$GT25_EVIDENCE/render-profile" --seconds 5
```

`render_cache_probe.py` 使用与像素测试相同的混合对照，默认 `--scenes-list peloton,climb`、`--order reference,candidate,candidate,reference`，每段预热 2 秒。记录缓存请求、命中/未命中、创建 Canvas 节点、重画次数，以及插桩条件下的实际帧/CPU 时间。复用节点不等于已测得 GPU backing、纹理或内部像素缓冲分配减少；宽高重置后浏览器仍可能重建内部资源。`render_cache_source.py` 是这两个 CLI 的提取助手，没有独立命令。

`render_profile.py` 针对正式 V25、同一 1440×1000 DPR1 全画质自然快照，保存 GPU 信息、CDP CPU profile、timeline 和摘要；`--snapshot`/`--out` 必填，`--seconds` 默认 5。跨线程和嵌套事件耗时不能相加为墙钟占比。采样器会改变时序，适合定位热点，不作为帧率改善证据；原始 trace/profile 体积较大，应留在外部证据目录。

## 7. 可复现源码 ZIP 与真正离线试玩

先完成报告、变更日志和轻量证据整理，再打包到项目外的**新文件**：

```bash
python tests/v25/package_source.py --out "$GT25_EVIDENCE/Grand-Tour-V25-Source.zip"
python tests/v25/package_verify.py "$GT25_EVIDENCE/Grand-Tour-V25-Source.zip" --out "$GT25_EVIDENCE/package-check"
```

`package_source.py --out ZIP` 明确选入 V25 游戏、入口、文档、测试、配置和保留清单中的历史文件，并验证历史字节。它生成固定时间戳/顺序的 ZIP、`PROVENANCE.json` 和完整 `SHA256SUMS.txt`，检查 CRC，不扫描收集任意工作区文件。输出不能在项目树中，也不能覆盖已有文件。

`package_verify.py ZIP --out NEW_DIR` 要求输出目录不存在，检查安全路径、CRC、完整哈希清单和 HTML 与当前源码相等，然后在新浏览器离线打开**解压后的 `index.html`**，操作首次设置、Tour、进攻、暂停、刷新继续和 390/320 Race Centre；保存独立试玩证据。最终交付 SHA-256 和大小以该 ZIP 实际输出为准。

本次 Cloud Handoff 已按交接说明裁掉旧 V24 Final ZIP 与不必要大归档。它们不属于运行/回归缺失项。保留的 `tests/v24/build_candidate.py` 针对旧封板 ZIP 的历史重打包流程，不适用于当前精简交接包；V25 使用上面的 `package_source.py`，不要为了运行旧打包器下载或伪造封板包。

## 8. 本地验证与远端 CI 的边界

`.github/workflows/v25-verify.yml` 提供后续的静态、14 族、35 项、存档、两版 Tour、浏览器与 ZIP 验证配置。配置文件存在不表示已执行；本次交付不声称任何远端 Actions/CI 结果，也不部署 Pages/Sites、不创建 Issue/PR/Release。完整 21 场自然审计、职业调查、独占性能和完整 `--play` 动画应按本指南另行运行；不要把工作流未包含的检查记为 CI 通过。
