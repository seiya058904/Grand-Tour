# Grand Tour 仓库指南

## 入口与边界

- 当前权威游戏为根目录 `Grand-Tour-V24.html`：自包含、离线可运行的 HTML，无 npm 构建或外部运行时库。`index.html` 只是跳转入口；GitHub Pages 从 `main` 根目录发布。
- `Grand-Tour-V24-Final.zip` 是保留原始字节的封板交付包；当前 HTML 的后续修复不等于包内历史 HTML。不要覆盖原包或把旧证据当作新修复的验证。
- 历史 HTML、报告在 `archive/<版本>/`，索引与旧 ZIP 的 Git 恢复方法见 `archive/README.md`。`archive/v22/`、`archive/v23/` 仍是核心回归基线，不能当作过期产物删除。
- 保持单 HTML 结构、比赛物理、AI、计时、排名、路线、V9 存档与确定性。纯整理须保持正式 HTML/ZIP 字节不变；发现新 Bug 只记录，除非任务授权修复。

## 运行与验证

从仓库根目录运行；需要 Node.js、Python，浏览器测试另需已安装 Chromium 的 Python Playwright。先创建仓库外的证据目录，以下 `$evidence` 为其绝对路径。

```powershell
python -m http.server 4187 --bind 127.0.0.1
# 另一个终端运行所需回归：
python tests/v24/static_verify.py --out "$evidence/static.json"
node tests/v24/core-parity.cjs archive/v23/Grand-Tour-V23.html Grand-Tour-V24.html "$evidence/core-parity.json"
node tests/v24/focused.cjs Grand-Tour-V24.html archive/v22/Grand-Tour-V22.html "$evidence/focused.json"
node tests/v24/save-finish-boundary.cjs Grand-Tour-V24.html "$evidence/save-finish-boundary.json"
python tests/v24/save-finish-browser.py --out "$evidence/save-finish-browser"
python tests/v24/browser_verify.py --out "$evidence/browser"
```

- 按变更选测试；完整 Tour 对照、存档所有权、TTT、领奖、性能与离线打包命令见 `tests/v24/README.md`。性能采样单独运行，避免并行测试干扰。
- CI 为 `.github/workflows/v23-verify.yml`，同时保留 V23/V24 回归。发布后核对对应提交的 CI/Pages 与线上 HTML/ZIP，而不是旧成功记录。
- 修复候选包使用 `tests/v24/build_candidate.py --out <仓库外新ZIP>`，再用 `tests/v24/package_verify.py <候选ZIP> --out <新目录>`。它们校验原包、生成清单并试玩离线入口；`static_verify.py --manifest` 只用于带清单的解压包。
- 完成前检查 `git diff --check`、最终 diff/status、入口和关键引用；说明未运行的验证。

## 目录与交付卫生

- 根目录只保留当前 HTML/Final ZIP/报告、入口、README、`AGENTS.md`、必要配置、`.github/`、`tests/`、`archive/`。历史资料优先按版本归档，不为美观重构成熟测试体系。
- 旧 Final ZIP 只有在确认无有效引用、可从 Git 历史完整恢复并记录恢复依据后，才从当前 tree 移除；唯一历史副本保留。
- 新截图、日志、缓存、临时验证产物放仓库外或忽略的 `output/`；已归档的正式验证证据保留。
- 新版本封板同步核对入口、README、报告、ZIP、`.gitignore` 当前包例外和 CI/Pages 引用。提交、推送、发布和部署须有明确授权；不改正式 tag/Release，不改写历史。
