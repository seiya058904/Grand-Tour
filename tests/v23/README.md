# V23 验证

从仓库或解压包根目录运行。需要 Node.js、Python，以及已安装 Chromium 的 Python Playwright；游戏自身不需要这些工具。默认使用真正的离线 `file://` 页面，测试拥有独立浏览器上下文，不使用个人浏览器资料。

```powershell
$evidence = Join-Path $env:TEMP 'grand-tour-v23-checks'
New-Item -ItemType Directory -Force -Path $evidence | Out-Null
python tests/v23/static_verify.py --out "$evidence/static.json"
node tests/v23/focused.cjs Grand-Tour-V23.html Grand-Tour-V22.html "$evidence/focused.json"
python tests/v23/browser_verify.py --out "$evidence/browser"
python tests/v23/presentation_verify.py --out "$evidence/ui"
python tests/v23/finish_motion_verify.py --out "$evidence/finish"
python tests/v23/downhill_verify.py --out "$evidence/downhill"
node tests/v23/tour-simulation.cjs Grand-Tour-V23.html "$evidence/tour.json" 314159
python tests/v23/sequence_verify.py --record "$evidence/browser/stage-05-physical.json" --tour "$evidence/tour-tour.json" --out "$evidence/sequence" --play
node tests/v23/showcase.cjs "$evidence/showcase" "$evidence/tour-tour.json"
python tests/v23/live_play_verify.py --evidence "$evidence/showcase" --out "$evidence/live"
```

性能探针应在上述工作结束后单独运行，避免并行测试干扰：

```powershell
python tests/v23/performance_probe.py --out "$evidence/performance.json"
# 仅解压交付包中存在清单：
python tests/v23/static_verify.py --manifest
```

`focused.cjs` 检查 33 项有针对性的回归，包括真实故障快照。`browser_verify.py` 在实际页面运行全部赛段开局与四类完整比赛；为压缩等待时间，完整比赛部分推进生产模拟的固定步长。`live_play_verify.py` 则以正常墙钟时间操作跟轮、Auto、进攻、补给、暂停和 Race Centre，并播放自然产生的局势快照。局势快照不是可独立导入的完整环法存档，因此该测试禁止把它们写入测试页面的存储。

`tour-simulation.cjs` 使用公开玩家控制完成 21 站，每 30 个模拟秒检查一次快照恢复；它不是人工连续游玩。`sequence_verify.py --play` 使用真实赛段和完整环法成绩，以 1 倍速播放普通领奖、TTT 车队领奖及最终典礼，另做肢体/道具接触、移动布局、键盘、重播和账本不变检查。

`showcase.cjs` 只保存自然运行到达的比赛状态，不修改车手位置、功率、成绩或时钟。若指定种子没有出现预期 GC 进攻，它会失败，不制造进攻画面。

`--injected` 只供不支持本地文件的受限环境诊断，不作为本版本离线运行或持久化验收证据。性能结果仅代表所记录环境的一次短采样，不能外推到真实手机。

颁奖迭代以 V22 舞台为基线。`sequence_verify.py` 另从完整环法存档打开第 18 站档案，检查四种领骑衫穿着、各章节选中状态、GC 入场/穿着和最后持续举杯；421 个连续姿态检查双肘朝向、抬杯连续性、固定臂长（按深度投影）和双手握柄。包内 `verification/racing-baseline/` 是颁奖迭代前的比赛与性能证据；证据来源与适用范围见 `verification/VERIFICATION-PROVENANCE.md`。本轮重跑范围见报告，不能把旧 JSON 的源文件哈希当作当前 HTML 哈希。

## V23 多页面存储回归（Issues #2 / #3）

```sh
node tests/v23/storage-ownership.cjs
# 在另一个终端从仓库根目录启动 python -m http.server 4187
python tests/v23/storage-browser.py
```

进度提交在同一 Web Lock 内读取最新存档，比较本页已加载/已提交的进度指纹与 revision；设置仅合并本次字段，不接管其他页面的进度。无 Web Locks 时，同步回退保护顺序发生的陈旧写入，不保证跨进程完全同时写入的原子性。导入和恢复须保留备份，冲突后本页仍保留可导出的内存进度。

关闭页面前先捕获最新比赛快照；异步提交未完成或保存失败/冲突时请求浏览器离开确认。请取消离开、等待保存或先导出。忽略浏览器警告、强制结束进程，以及系统未发送生命周期事件时，不能保证保存最后一刻的进度。

仅修复 V23；默认 index.html / V22 与历史 HTML 不变，仍可能写相同的 tour-cycling-2026-cinematic-v10 键。这些旧写入者不遵守新协议，无法由新 V23 严格控制。未发现本仓库 V23/index 注册 service worker 或 PWA 缓存；更新时关闭旧页面并备份，不假设旧代码已自动失效。
