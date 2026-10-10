# V25 存储所有权补丁独立复查

本次复查只读 `Grand-Tour-V25.html` 中 `progressStamp`、`loadStore`、`persist`、`saveActive`、`beforeUnloadSave`、新环法与导入入口，以及新旧存储所有权测试。未改共享源码，也未重复宣称已有测试的 PASS。

## 结论

未发现当前首次设置保存修复引入新的进度覆盖或队列竞争风险。修复的权限范围与原有“设置可合并，但不能因此接管另一页面进度”的所有权规则一致。

## 逐项推演

1. **空档等价范围受限**：仅 `progressRevision === 0` 且没有 `tour/active/pendingCeremony` 的设置档与无档使用相同 stamp。带 revision 的空档仍与从未保存区分，旧页面不能把被拥有过的空状态当作初始状态覆盖。
2. **已有 canonical 的设置合并不接管进度**：`patch` 在存在 raw 时保留原始 canonical 的进度，只合并 settings；此分支不更新 `savedProgress`。旧页面即使成功调节设置，下一次保存自己的旧比赛仍会冲突并拒绝。
3. **首次创建 canonical 才允许本页取得相应 stamp**：`!raw` 时还必须通过先前加载的进度 stamp 对照；只有 `setItem` 成功后，才记录该次本页自己写出的进度。由本页加载的 legacy-key 进度通过首次设置提升至 canonical 后，后续保存不会自冲突。
4. **删除已有 canonical 不授予旧页面新权限**：旧页面的 `savedProgress` 非空，`!raw` 令设置分支也执行 stamp 检查，从而拒绝复活旧进度。已覆盖的初始无档场景与此不同。
5. **队列时序不失效**：候选快照在调用时捕获，但同页面 Web Locks 队列依旧串行；本页前一次写入成功后更新 stamp，后续保存对照最新 raw。重载、新环法或替换导致 `storeEpoch` 改变，旧排队工作仍会在提交前退出。
6. **写失败不提前接管**：备份或 canonical 的写操作抛异常时，不会执行其后的 `savedProgress` 更新；下一次可按原所有权重试。备份在 canonical 之前写入，保留原数据。
7. **损坏数据保护仍先于写入**：宽松 stamp 的空值处理本身不把非法 raw 视作合法存档；提交仍会先通过 `SaveCodec.decode`，且仍有 recovery backup / explicit import 限制。
8. **设置与备份政策未被扩大**：修复没有修改 V9 编码字段、旧版本迁移规则、导入备份路径或进度 revision 递增公式。

## 边界

没有 Web Locks 时，`localStorage` 的读—校验—写不是跨浏览器进程原子 CAS，原有注释已明确这一边界。此补丁只能保留既有顺序陈旧写入防护，并未引入或声称具备新的跨进程原子性。

本报告是独立代码/时序复查；执行测试结果以主任务实际运行的存储测试 JSON 和浏览器证据为准。
