# 可选复核脚本

游戏本体直接打开 HTML，不需要这些脚本，也没有新增运行依赖。

## 定向检查（Node.js）

在完整包目录执行：

```sh
node tests/v12-focused.cjs grand-tour-v12.html
```

默认运行 19 项自包含检查。提供原 V11 HTML 路径后，增加导入、TT 同轨迹和基础函数一致性检查，共 23 项：

```sh
node tests/v12-focused.cjs grand-tour-v12.html ../grand-tour-v11.html
```

输出 `evidence/v12-focused.json`。脚本内明确区分构造的分组、GC 威胁、响应和积分点场景与真实连续模拟；构造场景的结果不是自然发生的赛果。

## 完整多日赛对照（Node.js）

```sh
node tests/tour-simulation.cjs grand-tour-v12.html evidence/recheck-314159.json 314159
node tests/tour-simulation.cjs grand-tour-v12.html evidence/recheck-271828.json 271828
```

每次运行完整 21 赛段，生成每赛段指标、末赛段记录和完整多日赛备份。控制的是 0 号玩家，使用相同的标准 GC 公开输入策略，不能当作无玩家干预的全 AI 排名实验。替换 HTML 路径可对照原 V11。

## 浏览器交互与录制（Python + 已安装的 Playwright / Chromium）

```sh
python tests/ui-browser.py
python tests/ui-browser.py ../grand-tour-v11.html
python tests/record-flow.py
```

没有安装浏览器工具也可以直接玩游戏。浏览器路径可通过 `CHROMIUM_EXECUTABLE` 指定。交互脚本检查真实 DOM、Canvas、鼠标、键盘、触屏和三个视口；第二条额外截图对比 V11。脚本使用显式内存 Storage 适配器，不证明原生本地存储可用。录制还需要本机已有 `ffmpeg` / `ffprobe`。

录制先用真实引擎推进到终点附近，开始取帧后按正常 RAF 运行，经过冲线、领奖和结算。原始临时帧位于 `evidence/video-frames/`，录制后可删除；交付包已删除这些中间帧，仅保留 MP4、时间戳和结果。

## 既有测试的处理

本轮实际复用了旧版的物理/存档/计时、连续运动和领奖生命周期脚本，对当前候选版分别运行 37、13、113 项检查；结果保留在证据中。为避免将历史 HTML、存档夹具和全部旧工程再次打包，这些旧脚本未重复附带；它们仍在原 V11 完整包中。

唯一刻意替换的旧契约是集团阈值：原测试要求 50m 的明显分离也等待、并在 10m 回并；新规则改为 24m 中等分离需持续确认、5m 接触需持续确认，并另测明显加速分离与低速爬坡 4.4m 轮距的正确合并。不是静默跳过失败。
