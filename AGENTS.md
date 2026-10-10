# Grand Tour 仓库指南 · V25

## 入口与设计边界

- 当前发布入口为 `Grand-Tour-V25.html`。该版本已合并进入 `main` 并部署到 GitHub Pages；线上 `index.html` 跳转到它。自包含、离线运行，无 npm 构建、外部运行时库或在线服务依赖。
- `Grand-Tour-V24.html` 是本次交接的最新 V24 基线，源自 commit `3e92128c0cb353d267c12ceeaf143bda663a7b26`；不能用旧封板 HTML 替换。V20–V23、V24 报告及 V22–V24 测试共 65 个文件由 `tests/v25/baseline-hashes.json` 保护。
- 冻结的历史交接包没有 `.git`，也没有旧 `Grand-Tour-V24-Final.zip`；这是交接包的既定裁剪。V25 打包器不依赖旧 ZIP，不要修改历史基线以掩盖失败。
- 保持单 HTML 产品形态、固定 0.05 秒步长、V9 保存键/格式、确定性物理和 AI。局部修复须有根因和回归；不为结构美观重写成熟模块。
- V25 已通过 PR #13 合并进入 `main`（合并提交 `735cdabcd5e82623ba0ba4ffcf32df8ab6fb35e4`）并部署到 GitHub Pages。不得改写既有历史；后续远端变更仍须获得明确授权。

## 必须保留的存档边界

- `Race.restore` 的完赛校验交叉检查车手完赛字段、赛事时钟、首末锚点及存在的终点过点账本；不能猜测或重建损坏锚点。
- 合法 OTL 过线仍可留在终点账本，而车手完赛字段已清空；部分公路/TT 路线没有终点 checkpoint；V4/V7 迁移末锚点可早于后续 OTL 过点；原生 `legacy-sim` 首锚点可为空。
- 旧档可以没有 `cutoff` 或其 `timeModel`。仅对存在的关门线验证形状、首位实际过线人和用时、截止时间及 FINISHED 合法性；不要重新计算历史百分比或改写旧结果。
- 严格导入遇到损坏 active 仍原子拒绝。恢复模式仅在外层存档重新迁移成功后隔离坏 active，保留逐站验证通过的成绩前缀；loadStore 在可写回前保留原始字节备份。
- `progressRevision:0` 且无 tour/active/pending 的纯设置档才与无进度同义。已有 canonical 的设置合并不得接管另一页进度；写失败不得更新所有权。无 Web Locks 的跨进程同时写不保证原子 CAS，不得宣称已解决。

## 运行与验证

从根目录执行，证据放仓库外。完整说明见 `tests/v25/README.md`。测试需要 Node.js、Python；真实浏览器另需 Python Playwright 和 Chromium；游戏本身不需要这些依赖。

```bash
mkdir -p /tmp/gt-v25
python tests/v25/static_verify.py --out /tmp/gt-v25/static.json
node tests/v25/core-parity.cjs Grand-Tour-V24.html Grand-Tour-V25.html /tmp/gt-v25/core.json
node tests/v25/focused.cjs Grand-Tour-V25.html archive/v22/Grand-Tour-V22.html /tmp/gt-v25/focused.json
node tests/v24/save-finish-boundary.cjs Grand-Tour-V25.html /tmp/gt-v25/boundary.json
node tests/v25/storage-validation.cjs Grand-Tour-V25.html /tmp/gt-v25/storage.json /tmp/gt-v25/fixtures
python tests/v24/browser_verify.py --source Grand-Tour-V25.html --out /tmp/gt-v25/browser
```

原 35 项定向回归只通过薄适配器更新版本断言，行为断言不变。V25 核心签名门禁要求 13 族完全相等，SaveCodec 仅允许已审查的 decode 恢复入口文本差异；不是笼统豁免整个编解码器。

完整 Tour 比较必须新跑两版并比较整份 V9 对象；不能拿历史 PASS 当新版本结果。场景播放、领奖和性能分别验证，状态断言不等于视觉质量。ABBA 性能采样必须停止其他模拟/浏览器测试，画质固定 full，记录环境和源码哈希。

## 目录、CI 与交付

- 新测试在 `tests/v25/`，紧凑机器证据在其 `evidence/`；截图、录像、自然快照、大日志、依赖和临时文件在仓库外。
- `tests/v25/package_source.py` 构建新的轻量 ZIP，`tests/v25/package_verify.py` 核验解压清单、基线、正式入口和实际离线存档/控件。禁止覆盖原始 V24 包。
- `.github/workflows/v25-verify.yml` 只执行验证、不含部署步骤（线上由 `main` 的 GitHub Pages 流程发布）。旧 V23/V24 工作流保留；仅依赖被裁剪旧 ZIP 的历史打包步骤明确标注可选输入缺失，不伪造 PASS。
- 完成前核验最终 diff、空白错误、入口、README、报告、CI 和打包引用。有 Git 时运行 `git diff --check`；本交接目录没有 Git 时与原 ZIP 逐文件对照。所有未跑或失败的验收须如实记录。
