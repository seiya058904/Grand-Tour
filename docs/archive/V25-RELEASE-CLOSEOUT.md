# Grand Tour V25 — 发布后文档一致性收尾记录（2026-10-10）

本文件记录 V25 正式合并发布后的一次**小范围文档一致性收尾**，只涉及发布状态描述的订正与包清单同步，不修改游戏逻辑、不新增功能、不改写 Git 历史、不重建审计结论。

> 本文件位于仓库根目录，但**不属于源码交付包**：`tests/v25/package_source.py` 的 `ROOT_FILES` 为显式清单，不包含本文件。因此本文件的增删不会改变交付包的 SHA-256。

## 1. 发布身份

| 项目 | 值 |
| --- | --- |
| 线上入口 | <https://seiya058904.github.io/Grand-Tour/> （`index.html` → `Grand-Tour-V25.html`） |
| 合并提交 | `735cdabcd5e82623ba0ba4ffcf32df8ab6fb35e4` （PR #13，普通 Merge Commit） |
| V25 HTML SHA-256 | `1f5a338355180489b53e2c8fbe3cb8537103ebbf20bf79a1bc45054a3dfee4ec` |
| V24 HTML SHA-256 | `b5d0899fad82ed6576f416e12267ec6d369405a4dfa56559e5629e6fcf00fa1f` |

## 2. 冻结的候选源码包（历史交付物，未覆盖）

| 项目 | 值 |
| --- | --- |
| 文件 | `Grand-Tour-V25-Source.zip`（保存在仓库外：`D:/下载/Grand-Tour-V25-Source.zip`） |
| 字节数 | 4,619,981 |
| SHA-256 | `22cca5118a8813d63620d332728bc705e45f5bd3d2f089e35d57fbaf024867b9` |
| 文件数 | 171 |

**可复现性核验：** 在本次文档修改**之前**，用 `tests/v25/package_source.py` 从当时源码树重新打包，得到完全相同的字节数与 SHA-256（`22cca511…`，171 文件）。这证明打包工具、仓库清单与冻结包在冻结点上完全一致，且原包未被覆盖。

## 3. 发布后重新生成的包（与冻结包**不同**）

| 项目 | 值 |
| --- | --- |
| 生成命令 | `python tests/v25/package_source.py --out <仓库外新路径>` |
| 字节数 | 4,621,684 |
| SHA-256 | `15ad8674f89da014bdbcfca74ac51a39b368ef915473cc41ece63987d765d676` |
| 文件数 | 171（与冻结包相同） |
| V25 HTML SHA-256 | `1f5a338355180489b53e2c8fbe3cb8537103ebbf20bf79a1bc45054a3dfee4ec`（未变） |

该哈希**不等于**冻结包，原因是发布后文档收尾修改了打包内的文档与元数据（见第 4 节）。两者不是同一产物，不得互相替代或声称相同。

## 4. 本次改动的文件（仅文档与包元数据）

- `README.md` — 将"未部署 / 源码候选"改为当前发布状态，补线上入口。
- `AGENTS.md` — 同上；并修正 CI 描述（验证工作流不含部署步骤）。
- `CLOUD-HANDOFF.md` — 增加文首「发布状态更新」，把涉及"尚未部署"的原文明确标注为**交接/候选阶段的历史事实**并按原样保留；末尾补充冻结包与再生成包的区别。
- `V25-CHANGELOG.md` — 标明条目为**合并发布前**的候选阶段记录，并注明 CI 工作流合并后已在远端实际通过。
- `PROVENANCE.json` — 由打包工具重新生成：`kind`/`deployment` 更新为已发布状态，并记录冻结包为历史产物；其余历史哈希字段（V24/V25/输入 ZIP、`historicalFilesPreserved: 65`）保持不变。
- `SHA256SUMS.txt` — 由打包工具对更新后的源码树重新生成；`sha256sum -c` 全量通过（170/170）。
- `tests/v25/package_source.py` — 其中内嵌的 `provenance` 字段同步更新，使工具输出与仓库元数据一致。

**未改动（字节不变）：** `Grand-Tour-V25.html`、`Grand-Tour-V24.html`、`index.html`、`V25-AUDIT-REPORT.md`、V20–V23 归档、`tests/v22`–`tests/v24` 原始测试、`.github/workflows/*`、`tests/v25/baseline-hashes.json` 保护的 65 个历史文件，以及所有 V25 测试脚本（除上列 `package_source.py` 的元数据字段外）。

## 5. 历史归档可恢复性复核（结论：未找到，不能声明已存于 GitHub）

再次全盘检查：

- `D:`、`C:`、`E:` 各盘（含回收站 `$Recycle.Bin`，已解码 `$I` 元数据中的原始路径）均**未发现**旧仓库目录（如 `Grand-Tour-old-*`）或历史 Bundle 文件（`*.bundle` / `*history-branches-backup*`）。
- GitHub 仓库 `seiya058904/Grand-Tour` 的公开历史不包含该"本地独有"历史归档；本次未做任何声称其已完整保存在 GitHub 的表述。

**如实标记：本地独有历史归档未验证。** 该归档在本次检查范围内不可从回收站、既有备份或已知路径恢复。V12/V18/V19 等历史归档（如有）此前由远端托管，属另一事项，不在本次可恢复性结论内。

## 6. 一致性核验摘要

- 打包工具 ↔ 仓库清单：冻结点**可逐字节重现**；发布后重新生成得到新哈希，已如实记录。
- 仓库 `SHA256SUMS.txt`：`sha256sum -c` 170/170 通过。
- V25 HTML、V24 HTML 与 65 个基线文件：字节与哈希未变。
- 未修改游戏逻辑、未新增功能、未创建 Issue/PR、未改写 Git 历史。
