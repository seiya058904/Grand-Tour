# 最终 Canvas 复用候选 · 模拟复验

生产源码：`Grand-Tour-V25.html`，**1,783,282 bytes**。开始和结束 SHA-256 均为：

`1f5a338355180489b53e2c8fbe3cb8537103ebbf20bf79a1bc45054a3dfee4ec`

本目录是合入 Canvas 复用后的独立复测证据，不覆盖此前 `558fdf...` 候选的任何结果。V24 基线沿用本轮已完成的真实 21 站记录，没有重新生成或改写。

| 验证 | 实际结果 |
| --- | --- |
| seed 314159 完整 Tour | 21/21 站完成 |
| 自然 `Race.restore` | 367 次通过 |
| 每站生产 `normalizeRecord` | 21 次通过 |
| 整份 V9 Tour 对象与 V24 比较 | 深度相等，未剔除任何比赛字段 |
| 编码 V9 文件字节比较 | 相同 SHA-256 |
| 运行时模拟源码家族 | 18/18 一致 |
| `liveSeason` 回归 | 6/6 通过，0 失败、0 跳过 |
| 最后一站人员 | 162 人发车并完赛；22 人此前退出 |

两个完整 V9 Tour JSON 的共同 SHA-256：

`3e83c50c18c06d77f0f41abd871c0c28d08b36ef8c0aec6077ac7a6601575fed`

运行时核对包含 Race 构造器及最终 prototype 覆盖、物理、天气、计时、分类、疲劳/生理、赛道、身份/种子函数与车手/赛段数据。CONFIG 的唯一区别仍为产品版本号 `240 → 250`。此次检查不包含外围未导出的存档辅助函数或实际发生优化的 RaceView Canvas 缓存；后者的像素与性能验证另由主任务记录。

原样使用 `tests/v23/tour-simulation.cjs` 运行完整 Tour；整份 V9 对照使用 `tests/v25/simulation-tour-parity.cjs`；实时榜单使用 `tests/v25/simulation-live-standings.cjs`。所有生产 `normalizeRecord` 与自然恢复检查均未拒绝合法比赛状态。对照的 21 站排名、计时、分类、体能与人员状态保持一致，未因 Canvas 复用改变模拟结果。

此复验仅代表该固定种子完整 Tour，不宣称覆盖所有随机比赛。Node 的机器运行耗时不作为浏览器性能证据。28 场平路职业调查仍明确属于 V24 基线调查，没有将旧数据改名为新候选的实测。
