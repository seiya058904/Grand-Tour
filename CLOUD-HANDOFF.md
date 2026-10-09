# CLOUD-HANDOFF — Grand Tour V25 源码候选

## 1. 打开与继续开发

解压后直接打开 `Grand-Tour-V25.html` 或 `index.html`。游戏仍是一个原生 JavaScript、Canvas、HTML/CSS 自包含文件；不需要联网、安装 npm 或启动服务。

当前产品为 V25 源码候选，没有部署到 GitHub Pages、OpenAI Sites 或其他服务器。阅读 `AGENTS.md`、`README.md`、`V25-AUDIT-REPORT.md`、`V25-CHANGELOG.md` 和 `tests/v25/README.md` 后再修改。

## 2. 权威基线与版本关系

- 本次输入：`Grand-Tour-V24-Cloud-Handoff-20261009.zip`。
- 权威 V24 commit：`3e92128c0cb353d267c12ceeaf143bda663a7b26`。
- 输入 ZIP SHA-256：`2cecea547fb5290284a58a6e6a79fe2fbdb3f35c028f1658e30824a11771f9c8`。
- 最新 V24 HTML SHA-256：`b5d0899fad82ed6576f416e12267ec6d369405a4dfa56559e5629e6fcf00fa1f`，在本包根目录原样保留。
- V25 HTML SHA-256：`1f5a338355180489b53e2c8fbe3cb8537103ebbf20bf79a1bc45054a3dfee4ec`。

V24 在 10 月 4 日封板后仍有终点计时锚点、存档和弹窗修复。本次从上面的最新 HTML 派生 V25，未使用旧封板 HTML。`V24-REPORT.md` 中的旧结果只属于其标明的版本。

旧 V24 Final ZIP、非必要历史归档与 Git 历史原本就不随交接包提供。原 `tests/v24/build_candidate.py` 实际需要旧封板 ZIP 作为模板；原交接说明对此过于乐观。V25 新增独立源码打包器解决当前交付，未伪造或重建旧封板证据。

## 3. 目录

| 路径 | 用途 |
| --- | --- |
| `Grand-Tour-V25.html` / `index.html` | 当前游戏与跳转入口 |
| `Grand-Tour-V24.html` / `V24-REPORT.md` | 未改动的最新基线与历史报告 |
| `archive/v20`–`archive/v23` | 必要旧 HTML、报告；不可随意移除 |
| `tests/v22`–`tests/v24` | 原始回归套件，文件字节保持不变 |
| `tests/v25` | 新缺陷回归、明确版本适配器、性能和打包工具 |
| `tests/v25/evidence` | 本次实际运行的紧凑证据和汇总；不包含大型录像/快照 |
| `.github/workflows` | 保留旧验证及新增 V25 验证配置，不负责部署 |
| `V25-AUDIT-REPORT.md` | 审计方法、复现、修复、结果、未解决限制 |
| `V25-CHANGELOG.md` | 简洁变更记录 |
| `PROVENANCE.json` / `SHA256SUMS.txt` | 打包时生成的来源与完整文件校验清单 |

## 4. V25 变更边界

修复首次设置保存与进度所有权、非法关门线接受、active 迁移错误隔离、实时积分榜平分规则；村落、林线、终点观众使用稳定的景物世界位置；去除重复深度候选评分；复用满额身体精灵缓存淘汰的 Canvas，保留完整状态重置与画质；扩大大屏布局。未改比赛物理、AI、职业能力、随机数、压缩路线、计时、正式分类和存档格式。

`SaveCodec.decode` 的异常恢复入口是明确记录的源码签名例外，其余编解码逻辑保持逐字对照。V25 与新跑 V24 的完整 Tour 对照及实际通过/失败数量见审计报告，不能仅凭文字说明假定测试通过。

## 5. 已知限制与下一步价值

- 28 场新平路调查仍显示 Sprinter 胜率偏低；没有人为增加职业倍率或指定冠军。样本为固定 GC 玩家公开 Auto/补给策略，Auto 终点行为仍保留，并非全 AI、随机玩家或所有能力分布的代表样本。
- 无 Web Locks 时的跨进程同时写入不是原子 CAS。现有所有权校验降低误覆盖，但不能承诺绝对跨进程事务隔离。
- 本轮真实浏览器为 Linux Chromium；视口覆盖不等于真实手机硬件验证。性能数字不能外推到不同浏览器/GPU，短时堆测量不能证明不存在长期泄漏。
- 合法 OTL 账本、缺少终点 checkpoint、历史 legacy-sim 锚点和可选 cutoff 元数据必须继续兼容。

## 6. 重复验证和打包

完整命令见 `tests/v25/README.md`。生成证据前先建仓库外目录；性能测试与其他重负载严格分开。包可用以下命令从当前源码直接生成：

```bash
python tests/v25/package_source.py --out /tmp/Grand-Tour-V25-Source.zip
python tests/v25/package_verify.py /tmp/Grand-Tour-V25-Source.zip --out /tmp/gt-v25-package-check
```

输出 ZIP 与验收目录必须是新路径。所有报告和本次证据仍保留源码哈希；后续修改后必须重跑相关门禁，不能把本轮 PASS 当作新修改的验证。
