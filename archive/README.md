# Grand Tour 历史版本

当前正式版本在仓库根目录：[V24 HTML](../Grand-Tour-V24.html) · [最终交付包](../Grand-Tour-V24-Final.zip) · [报告](../V24-REPORT.md)。

| 版本 | 独立 HTML | 原始报告 |
| --- | --- | --- |
| V12 | [grand-tour-v12.html](v12/grand-tour-v12.html) | [V12-REPORT.md](v12/V12-REPORT.md) |
| V18.3.1 | [Grand-Tour-V18.3.1.html](v18.3.1/Grand-Tour-V18.3.1.html) | — |
| V19 | [Grand-Tour-V19.html](v19/Grand-Tour-V19.html) | [V19-REPORT.md](v19/V19-REPORT.md) |
| V20 | [Grand-Tour-V20.html](v20/Grand-Tour-V20.html) | [V20-REPORT.md](v20/V20-REPORT.md) |
| V21 | [Grand-Tour-V21.html](v21/Grand-Tour-V21.html) | [V21-REPORT.md](v21/V21-REPORT.md) |
| V22 | [Grand-Tour-V22.html](v22/Grand-Tour-V22.html) | [V22-REPORT.md](v22/V22-REPORT.md) |
| V23 | [Grand-Tour-V23.html](v23/Grand-Tour-V23.html) | [V23-REPORT.md](v23/V23-REPORT.md) |

历史 HTML 和报告保留原始字节。报告中的“当前版本”、入口及本地证据路径描述的是当时发布状态；`evidence/`、`verification/` 和清单引用按相应原始交付包理解。V12 的已有截图、验证记录与复核脚本整体保留在 [v12/](v12/README.md)。顶层 `tests/v22/`、`tests/v23/`、`tests/v24/` 保持原测试体系，仅将仓库中的历史基线路径更新到本目录。V22 的旧包入口/清单检查应在原始 V22 交付包内执行。

## 恢复历史 Final ZIP

V21/V22/V23 ZIP 已从当前 tree 移除；删除前逐一核对工作区 SHA-256 与 Git blob 完全一致。完整文件仍在远端已有提交 `9b3ea8c67b69f8b86398d36d1baf0426ea94807d`，无需改写历史或长期保留重复二进制。

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| Grand-Tour-V21-Final.zip | 17,317,855 | `81467e8b5499c2fc950024e99ee20a18ed73c30dd3f06fa1bf761887a9df12f2` |
| Grand-Tour-V22-Final.zip | 23,134,920 | `226d13c9e0a5ef9440b05804f299b0c6534e1ee026f683d018458f7631f70f81` |
| Grand-Tour-V23-Final.zip | 37,776,084 | `547cbaffd41a3e4e1d8512b372540864bf326009dcede93d554607f223185500` |

从仓库根目录执行以下命令，将三个原始文件恢复到临时目录。使用 Python 的二进制输出，避免旧版 PowerShell 重定向改变 ZIP 字节：

```powershell
@'
import os, subprocess
from pathlib import Path
commit = '9b3ea8c67b69f8b86398d36d1baf0426ea94807d'
target = Path(os.environ['TEMP']) / 'grand-tour-historical-zips'
target.mkdir(exist_ok=True)
for version in (21, 22, 23):
    name = f'Grand-Tour-V{version}-Final.zip'
    with (target / name).open('xb') as output:
        subprocess.run(['git', 'show', f'{commit}:{name}'], stdout=output, check=True)
    print(target / name)
'@ | python -
```

恢复后按上表核对 SHA-256。这些文件不需要恢复到当前工作树，V24 最终 ZIP 的原始包内目录与字节保持不变。
