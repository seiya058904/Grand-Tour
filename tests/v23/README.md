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

颁奖迭代以 V22 舞台为基线。`sequence_verify.py` 另从完整环法存档打开第 18 站档案，检查四种领骑衫穿着、各章节选中状态、GC 入场/穿着和最后持续举杯；421 个连续姿态检查双肘朝向、抬杯连续性、固定臂长（按深度投影）和双手握柄。包内 `verification/racing-baseline/` 是颁奖迭代前的比赛与性能证据；`verification/ceremony-scope.json` 记录比赛代码保持一致的逐段校验。本轮重跑范围见报告，不能把旧 JSON 的源文件哈希当作当前 HTML 哈希。
