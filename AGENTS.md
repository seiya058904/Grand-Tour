# Grand Tour 仓库指南 · V26

## 入口与冻结边界
- 现行入口为 `Grand-Tour-V26.html`（离线单 HTML、无构建/无外链，根 `index.html` 跳转至它）；`Grand-Tour-V25.html` 冻结为 V26 基线，`Grand-Tour-V24.html` 及 V20–V24 共 65 文件由 `tests/v25/baseline-hashes.json` 保护，严禁覆盖或改写历史基线/旧交接包。
- **V26 仅改表现层**：14 个核心族（`Race`…`STAGE_DATA` 含 `SaveCodec`）必须与 V25 源码逐字一致（`CONFIG` 仅 `buildVersion` 250→260）；颁奖只读冻结快照，不调 `Race.tick`/不写账本/不碰 RNG，粒子仅用 `sceneNoise`。
- 保持单 HTML、0.05s 固定步长、V9 存档格式、确定性物理与 AI；不为美观重写成熟模块。历史提交不可改写。

## 必须保留的存档边界
- `Race.restore` 完赛校验交叉核对完赛字段、时钟、首末锚点与终点账本；严禁猜测或重建损坏锚点。
- 允许合法 OTL 留账本而完赛字段清空、无终点 checkpoint 路线、V4/V7 末锚点早于 OTL、原生 `legacy-sim` 首锚点为空、旧档缺 `cutoff`/`timeModel`（不重算历史百分比或改旧结果）。
- 严格导入遇损坏 active 原子拒绝；恢复模式仅外层重迁移成功后隔离坏 active，`loadStore` 写回前保留原始字节备份。
- 仅 `progressRevision:0` 且无 tour/active/pending 为纯设置档；设置合并不得接管另一页进度，写失败不更新所有权；无 Web Locks 跨进程同时写不保证原子 CAS，不得宣称已解决。

## 验证与 CI 最小测试原则
- 完整 V26/V25 门禁命令、ABBA 性能采样与源码打包校验见 `.agents/skills/grand-tour-verification/SKILL.md`（所有测试证据放仓库外，严禁覆盖原始 V24 包）。
- **CI 最小测试原则（2026-10-27 决定）**：不恢复宽泛 push 触发；纯文档改动不启动验证；改 `v25-verify.yml` 种子须同步缓存键与命令；保留 `v23-verify.yml` 月度/手动回归。
