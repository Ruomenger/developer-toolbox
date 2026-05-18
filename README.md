# developer-toolbox (`dbx`)

一个可扩展的命令行工具箱，统一收纳日常开发中零散的辅助命令。基于 Python 3.11 + `uv`，采用子命令架构，新增功能时无需改动主入口。

## 功能特性

- **统一入口**：所有日常小工具收敛到 `dbx <group> <action>` 一条命令下。
- **自动发现**：`src/dbx/commands/` 下的子包只要实现 `register()`，启动时会被自动注册成子命令组。
- **依赖按需引入**：默认优先使用标准库保持轻量；当某个子命令确实能从第三方库受益时，可在 `pyproject.toml` 中加入对应依赖，由 uv 统一管理。
- **跨平台**：在 macOS 与 Linux 上均可工作。
- **uv 驱动**：通过 `uv run` 自动管理 Python 版本与虚拟环境，无需手动激活 venv。

## 当前命令清单

| 命令 | 说明 |
| --- | --- |
| `dbx date diff <date1> <date2>` | 计算两个日期 (`YYYY-MM-DD`) 相隔的天数 |

示例：

```bash
$ dbx date diff 2026-05-13 2024-08-13
[dbx] 2026-05-13 和 2024-08-13 相隔 638 天
```

输入格式错误会给出友好提示并以非零退出码退出：

```bash
$ dbx date diff 2026-05-13 oops
[dbx] 错误：日期格式不正确，要求 YYYY-MM-DD (收到 '2026-05-13' 与 'oops')
```

## 环境要求

- macOS / Linux
- [uv](https://docs.astral.sh/uv/) ≥ 0.4
- Python **3.11+**（由 uv 自动准备，无需系统预装）

## 安装

```bash
# 1) 克隆仓库
git clone https://github.com/<your-name>/developer-toolbox.git
cd developer-toolbox

# 2) 同步依赖与 Python 版本 (uv 会按 .python-version 自动拉取 3.11)
uv sync

# 3) 创建全局软链接 (~/local/bin 需已在 PATH 中)
mkdir -p ~/local/bin
ln -sf "$(pwd)/bin/dbx" ~/local/bin/dbx

# 4) 验证
dbx --help
dbx date diff 2026-05-13 2024-08-13
```

> 提示：如果你习惯使用 `~/.local/bin`（多数发行版的默认约定），把上面命令里的路径相应替换即可。

## 目录结构

```
developer-toolbox/
├── pyproject.toml          # 项目元数据 (requires-python >= 3.11)
├── .python-version         # uv 固定的解释器版本
├── bin/
│   └── dbx                 # bash 入口包装：跟随软链接 + uv run
└── src/
    └── dbx/
        ├── __init__.py     # 版本号
        ├── __main__.py     # 支持 `python -m dbx`
        ├── cli.py          # 主入口：自动发现并注册 commands/ 下的子命令组
        └── commands/
            ├── __init__.py
            └── date/       # 子命令组 (group)
                ├── __init__.py   # 注册 group 并装配各 action
                └── diff.py       # 具体的 action 实现
```

## 扩展指南

### 新增一个 action（在已有 group 下）

以给 `date` 组加一个 `today` 子命令为例：

```python
# src/dbx/commands/date/today.py
from __future__ import annotations
import argparse
from datetime import date

def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("today", help="打印今天的日期")
    p.set_defaults(handler=run)

def run(args: argparse.Namespace) -> int:
    print(date.today().isoformat())
    return 0
```

然后在 `src/dbx/commands/date/__init__.py` 里追加两行：

```python
from . import today          # ← 新增
today.register(actions)      # ← 新增
```

之后即可使用 `dbx date today`。

### 新增一个 group（全新的子命令组）

例如增加 `string` 组：

```bash
mkdir -p src/dbx/commands/string
```

```python
# src/dbx/commands/string/__init__.py
from __future__ import annotations
import argparse
from . import upper

def register(subparsers: argparse._SubParsersAction) -> None:
    g = subparsers.add_parser("string", help="字符串工具")
    a = g.add_subparsers(dest="action", metavar="<action>")
    a.required = True
    upper.register(a)
```

```python
# src/dbx/commands/string/upper.py
from __future__ import annotations
import argparse

def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("upper", help="转大写")
    p.add_argument("text")
    p.set_defaults(handler=lambda args: (print(args.text.upper()), 0)[1])
```

无需改 `cli.py`，运行 `dbx string upper hello` 即可输出 `HELLO`。

### 约定回顾

- 每个 group 是 `commands/` 下的一个**包**（带 `__init__.py`）。
- 每个 group 的 `__init__.py` 必须实现 `register(subparsers)` 函数，向其追加自己的 `add_parser(...)`。
- 每个 action 通过 `parser.set_defaults(handler=...)` 注册处理函数；`handler(args)` 返回退出码（`None` 视为 `0`）。

## 开发与调试

直接通过 `python -m dbx` 也可以运行，方便在 IDE 里打断点：

```bash
uv run python -m dbx date diff 2026-05-13 2024-08-13
```

查看版本：

```bash
dbx --version    # → dbx 0.1.0
```

## License

见 [LICENSE](./LICENSE)。
