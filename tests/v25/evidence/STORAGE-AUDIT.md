# V25 存档专项审计与验证

## 基线与范围

V24 权威 HTML SHA-256：`b5d0899fad82ed6576f416e12267ec6d369405a4dfa56559e5629e6fcf00fa1f`。最终验证对象 V25 SHA-256：`558fdfbae82449fe4fbdcd55e1ce61bb3de6be4ec7997bbc0a49ed20dbcccc95`。历史 HTML、历史测试均未修改；所有补丁先在独立副本验证，再由主代理合入。

已读 CLOUD-HANDOFF、AGENTS、README、V24-REPORT、tests/v24/README；分析了 V9 编解码、V4/V7/V8 迁移、Race.restore 的终点/过点状态、normalizeRecord、保存队列、Web Locks 和无锁路径、loadStore/严格导入/导出、beforeunload/pagehide、赛段结算与领奖索引。

## 发现与修复

### S1（建议 P2）：首次设置保存导致本页失去新进度所有权

正常操作复现：清空隔离测试上下文 → 在主页打开音乐面板并调整音量 → 开始首个 Tour。V24 设置已落盘，但后续比赛保存误报“另一页面已更新进度”；canonical 的 tour 仍为 null。真实浏览器有/无 Web Locks、1440 与 390 宽度均复现。

根因：不存在存档时 `progressStamp(null)` 为 null；首次设置写入的空 V9 存档签名却是 `[0,null,null,null]`。设置合并为避免采用其他页面进度而不更新本页 `savedProgress`，随后本页自己的第一场比赛也被 CAS 拒绝。

同一边界还影响旧存储键载入后的首次 canonical 提升：先改设置会写入本页已经载入的旧 Tour，但后续保存仍误判冲突。另确认 canonical 被外部移除后，旧页设置补丁会从内存重发旧 Tour，缺少创建时的所有权检查。

最小修复：仅将 revision=0、tour/active/pendingCeremony 均为空的设置档归一为无进度；revision>0 的空档仍有独立所有权。所有首次 canonical 创建都须仍拥有其“尚不存在”的状态，防止旧页复活被删除的进度。只有本页成功首次创建（包括旧键提升）才更新其拥有的签名；合并进入已存在 canonical 的设置仍绝不采用他页的进度。

证据：`v24-first-settings.json` 为 2/10，8 个业务失败；正式 `v25-first-settings-final.json` 为 10/10。V24 真实 UI 8 组均复现；正式 V25 同类 8 组通过，包含刷新后续玩和旧存储键字节不变。

### S2（建议 P2）：损坏的关门线可通过严格恢复并淘汰整场车手

这是损坏输入防线缺口；没有将正常模拟结果定性为计时 Bug。

从自然第 1 站首次过线快照（t=270.5 秒，1 人完赛、0 OTL）仅把 `active.cutoff.deadline` 改为 1。V24 严格解码返回零 issues；恢复后推进一个 tick 即变成 0 人完赛、184 人 OTL，最终记账再因关门线损坏抛错。历史已完成记录也可带合法公式但明显错误的冠军时间/身份，通过旧严格解码。

根因：Race.restore 的初始 cutoff 模板为 null，通用 shape 校验不会检查其中字段；normalizeRecord 的旧检查只保证字段有限与 deadline 公式，没有与实际完赛者交叉验证。

修复：共享 `validateCutoff` 校验已有 cutoff 的对象类型、数值、正时间/均速、百分比范围、公式、可选时间口径，以及冠军属于最早实际到达者、冠军赛事时间一致、所有 FINISHED 均不晚于关门线。Race.restore 通过已有外围 `validateFinishState` 调用；normalizeRecord 使用同一 helper 替换旧检查。

兼容策略：不重新计算或调整关门百分比，不改变比赛计算；允许历史 cutoff 缺省及 cutoff.timeModel 缺省。TTT 的 cutoff 冠军按实际第一个过线者处理，团队分类保持独立。合法 OTL 的终点账本、后续清空的 rider 完赛字段、无终点 checkpoint、legacy-sim/V4/V7 的首末锚点例外均保留。缺少 FINISHED 的非空 cutoff 不符合经过验证的生产路径：合法非负百分比下最早过线者不会由同一关门线淘汰。

### S3（建议 P2）：active 迁移失败阻止恢复已完成有效成绩

自然完成第 1 站并进入第 2 站后，仅把 active.seed 改为 -1。V24 的 recover=true 仍直接抛“比赛种子无效”，无法暴露仍完整有效的第 1 站成绩；错误出现在 migrateStore 的 active 迁移，早于 decode 中原有的局部恢复捕获。

修复：严格导入路径继续原样拒绝。仅在 recover=true 且原输入有 active 时，尝试以 active:null 再执行同一完整外层迁移；外层或 tour 仍不合法则继续抛错。只有外层迁移合法后，报告 active 丢弃原因，并按原 normalizeRecord 流程验证/保留有效成绩前缀。未猜测任何 seed，没有修改输入对象或原始 raw。loadStore 必须先备份原始 raw，才公开恢复后的 Store 并允许后续保存。

对抗检查确认：不支持的顶层版本、无效 Tour seed、无效 progressRevision 仍拒绝；损坏的成绩后缀仍被原成绩验证发现，只保留之前的合法成绩；设置保留。严格文件导入在确认弹窗前拒绝，canonical 和既存两份备份均未被触碰。

## 最终实跑结果

| 验证 | 最终结果 | 证据 |
| --- | --- | --- |
| 新增存档验证专项 | 43/43，0 失败；启动 SHA 与结束 SHA 相同 | v25-validation-final.json |
| 首次设置与所有权专项 | 10/10，0 失败；启动 SHA 与结束 SHA 相同 | v25-first-settings-final.json |
| 原 V24 完赛边界 | 25/25，0 失败 | v25-save-finish-boundary-final.json |
| 原存储所有权/设置回调/失败重试套件 | 有锁、无锁、附带 GC 共 3 组 PASS | v25-storage-ownership-final.log |
| 生产浏览器完整存档专项 | 12/12；0 page errors、0 console errors、0 外部请求 | v25-browser-final/storage-first-settings-browser.json |
| V24 自然 21 站存档兼容 | 全 21 站严格解码无 issues，最终 162 人完赛；V24/V25 解码再编码的对象完全一致 | v25-full-tour-compatibility.json |

43 项包含 TTT / 普通公路 / ITT 的 race-world-v1 与 legacy-sim 自然比赛；原始/紧凑快照、实际完赛记录、单字段损坏、合法迟到 OTL、V4/V7/V8 迁移、有效成绩前缀保留及 raw 备份。保留原 25 项的 V22/V23 实际快照与终点锚点回归。

21 站兼容对照使用模拟代理刚运行的 V24 Tour，不复用旧报告。其导出的 settings 为 `{}`；V24 与 V25 都会补充同样的默认设置。因此对照的是两版完整规范化输出，未把既有默认设置补全误判为进度变化。

## 真实浏览器证据

环境：Chromium 141.0.7390.37，Python Playwright 1.56，隔离浏览器上下文，本进程临时 HTTP server；没有 Browser plugin/skill，使用仓库现有 Playwright 工作方式。全程正常生产入口，无 `?test`。服务器从启动时捕获的 HTML 字节提供所有页面，保证双页与每次刷新使用相同的最终源文件。

界面操作：主页音量真实键盘调整、Tour 开始、暂停/保存回主页、刷新与继续、双页进度竞争、旧键续玩；真实 file input 导入自然合法存档及三类损坏存档。已有自然快照用于缩短等待，不改物理、车手位置或胜者。

有/无 Web Locks × 1440/390 布局均测试了三类损坏导入（active cutoff、active migration seed、历史 cutoff），均在确认前拒绝，canonical / before-import / recovery-backup 的已有字节完整保留。随后通过同一页面刷新正常触发 recover：第 1 站成绩与设置保留、active 丢弃、原始 raw 先备份、可以从合法 Tour seed 启动第 2 站并保存为严格可解码档。

已实际查看 390 截图：原版顶部错误显示他页更新；修复后比赛可保存且无该误报；损坏 active 刷新后首页清楚显示“进行中比赛无法恢复…原数据已备份”，摘要仍为已完成 1/21、下一站 STAGE 02。截图是表现证据，业务结论同时由生产 Store/canonical 断言验证。

## 未修改或剩余边界

- 模拟积分、GC、功率、AI、路线和时间计算未在本专项修改。严格存档验证只拒绝已证明与结果矛盾的输入，不修正或覆盖比赛结果。
- pendingCeremony 非法索引保留有效成绩并丢弃可选演出索引，属于既有恢复设计，未改为把整份存档当作损坏。
- Web Locks 对合作页面提供序列化；无锁路径仅验证顺序发生的旧页写入检测，无法宣称 localStorage 在跨浏览器进程中具有原子 CAS。
- 浏览器强制终止、用户忽略 beforeunload 提示离开、浏览器不发送生命周期事件时，不能保证尚未完成的异步 Web Locks 写入。这是平台边界，未伪造持久性保证。
- 未运行 Safari/Firefox 或真实手机；本专项未测性能，因此不宣称新增验证提升帧率。

新增可交付测试：`tests/v25/storage-first-settings.cjs`、`tests/v25/storage-validation.cjs`、`tests/v25/storage-first-settings-browser.py`。测试/截图/日志来源与候选、原版、正式验证分别标识；最终结论以上述正式 558fdfb…文件实跑为准。
