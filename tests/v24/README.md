# V24 验证

游戏只需打开 `Grand-Tour-V24.html` 或 `index.html`。下列命令用于工程复核，需要 Node.js、Python 和已安装 Chromium 的 Python Playwright。测试使用隔离资料，不接触玩家的浏览器存档。

下列命令从仓库根目录运行，历史基线位于 `archive/`。V24 封板 ZIP 保持原始字节和内部目录，解压后请使用包内原有验证指南（基线 HTML 在包根目录）。先在仓库外或忽略的 `output/` 下创建输出目录；`$evidence` 是该目录的绝对路径。

```powershell
python tests/v24/static_verify.py --out "$evidence/static.json"
node tests/v24/core-parity.cjs archive/v23/Grand-Tour-V23.html Grand-Tour-V24.html "$evidence/core-parity.json"
node tests/v24/focused.cjs Grand-Tour-V24.html archive/v22/Grand-Tour-V22.html "$evidence/focused.json"
python tests/v24/browser_verify.py --out "$evidence/browser"
python tests/v24/presentation_verify.py --out "$evidence/ui"
node tests/v23/ttt-wheel.cjs Grand-Tour-V24.html "$evidence/ttt-wheel.json"
node tests/v23/storage-ownership.cjs Grand-Tour-V24.html
```

保留 V23 的公共测试工具和真实故障快照，不复制第二套比赛引擎。35 项定向回归包含自然终点冲刺的姿态/标签与呼吸相位连续性。浏览器检查覆盖 504 个路线坐标、6144 个骑行骨架姿态、全部 21 站开局、四类完整比赛、真实离线文件、V9 恢复和移动布局。

实际两个页面的进度所有权测试需要先从根目录运行 `python -m http.server 4187 --bind 127.0.0.1`，再运行 `python tests/v24/storage-browser.py --out "$evidence/storage-browser"`。本轮只回归 #2/#3/#6，未重做已关闭问题。

## 多种子与完整巡回赛

```powershell
node tests/v23/tour-simulation.cjs archive/v23/Grand-Tour-V23.html "$evidence/baseline-tour.json" 314159
node tests/v23/tour-simulation.cjs Grand-Tour-V24.html "$evidence/v24-tour.json" 314159
node tests/v24/race-audit.cjs archive/v23/Grand-Tour-V23.html "$evidence/baseline-audit.json" - "$evidence/baseline-tour-tour.json"
node tests/v24/race-audit.cjs Grand-Tour-V24.html "$evidence/v24-audit.json" "$evidence/baseline-audit.json" "$evidence/baseline-tour-tour.json"
node tests/v24/tactics_probe.cjs archive/v23/Grand-Tour-V23.html "$evidence/tactics.json"
```

`race-audit.cjs` 对三个种子 × 第 1/3/5/7/16/19/21 站逐场比较整个结果 JSON 的 SHA-256，包含成绩和 AI 审计。第 19 站承接真实第 18 站成绩；其他场景是明确的新建单站条件。每 60 个模拟秒对原始/紧凑快照继续推进 50 步并比较物理状态。生成的 `scenes/` 全部来自自然比赛。

`tour-simulation.cjs` 使用公开玩家控制和生产固定步长，输出完整 V9 环法存档；比较两份 `*-tour.json` 的解析对象即可复核所有 21 站记录完全相同。它不是人工连续游玩 21 站。多种子样本用于回归与诊断，不证明长期职业胜率平衡。

## 实际播放、画面与领奖

```powershell
python tests/v24/scene_verify.py --scenes "$evidence/scenes" --out "$evidence/scenes-played"
node tests/v23/showcase.cjs "$evidence/natural-scenes" "$evidence/v24-tour-tour.json"
python tests/v24/live_play_verify.py --evidence "$evidence/natural-scenes" --out "$evidence/live"
python tests/v24/finish_motion_verify.py --out "$evidence/finish"
python tests/v24/downhill_verify.py --out "$evidence/downhill"
python tests/v24/weather_verify.py --out "$evidence/weather"
python tests/v24/sequence_verify.py --record "$evidence/browser/stage-05-physical.json" --tour "$evidence/v24-tour-tour.json" --out "$evidence/sequence" --play
```

`live_play_verify.py` 以正常墙钟 1× 操作点名跟车、Auto、进攻、补给、暂停和 Race Centre，随后播放五段自然局势。`scene_verify.py` 另检查九种真实局势的动作连续性、公共投影、渲染纯度，以及全部 21 站环境确定性；只在隔离画布上做几何采样，不修改车手位置或天气。

`sequence_verify.py` 检查暂停切章可读性及账本不变，以 1× 完整播放普通和最终颁奖，保留 V23 的人物/道具接触、GC 台位、421 个举杯姿态、键盘和减少动态效果回归。

## 性能与交付包

在其他测试结束后单独运行：

```powershell
python tests/v24/performance_probe.py --scenes "$evidence/scenes" --out "$evidence/performance.json"
# 解压后的交付包附完整清单：
python tests/v24/static_verify.py --manifest
python tests/v24/package_verify.py Grand-Tour-V24-Final.zip --out "$evidence/package-check"
```

性能使用同机全画质 1440×1000、DPR 1、三种自然场景，每种按 V23/V24/V24/V23 顺序采样，分别报告 p95/p99/max、超过 33/50 ms 的帧、CPU 与模拟欠账。不要同时运行其他测试；结果不能外推到真实手机。

包内 `verification/VERIFICATION-PROVENANCE.md` 记录每份证据的源文件哈希和适用范围。旧版 HTML 仅作为可离线复核的基线，游戏入口始终为 V24。

`package_verify.py` 的 ZIP 参数可使用下载文件的绝对路径；输出目录必须不存在。它校验 ZIP 的 CRC、完整清单和游戏字节，然后在新浏览器中打开解压后的离线入口，操作比赛与移动布局。

## 发布回归

`.github/workflows/v23-verify.yml` 保留 V23 回归，并新增 V24 任务。相关文件的 pull request 与 `main` 推送均执行 V24 静态检查、14 组核心签名、35 项定向回归、TTT/存档所有权、两版完整 21 站 Tour 存档对照、浏览器比赛、移动布局、领奖几何和交付 ZIP 的离线试玩。性能采样和完整 1× 领奖播放在本地单独运行。

当前官方入口为根目录 `index.html`，跳转到 `Grand-Tour-V24.html`；GitHub Pages 从 `main` 根目录发布。发布后还需核对对应提交的 Actions/Pages 状态、线上 HTML/ZIP 哈希，并在实际网站复核入口、比赛控件及同源 V23 存档续玩。
