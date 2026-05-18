# developer-toolbox (`dbx`)

[![CI](https://github.com/Ruomenger/developer-toolbox/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/Ruomenger/developer-toolbox/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ruomenger/developer-toolbox.svg)](./LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

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
| `dbx date diff <date1> <date2>` | 输出 `date2 - date1` 的整数天数差，可为负数；输入格式 `YYYY-MM-DD` |
| `dbx date add <date> <±days>` | 输出 `date` 偏移 `days` 天后的日期；`days` 为整数，可正可负 |

示例 —— 成功路径只输出一个整数，便于脚本捕获：

```bash
# date2 > date1 → 正数
$ dbx date diff 2024-08-13 2026-05-13
638

# date2 < date1 → 负数
$ dbx date diff 2026-05-13 2024-08-13
-638

# 同一天 → 0
$ dbx date diff 2026-05-13 2026-05-13
0

# 直接拿来做脚本里的算术
days=$(dbx date diff 2026-01-01 "$(date +%Y-%m-%d)")
```

输入格式错误会写到 stderr 并以非零退出码退出：

```bash
$ dbx date diff 2026-05-13 oops
[dbx] 错误：日期格式不正确，要求 YYYY-MM-DD (收到 '2026-05-13' 与 'oops')
$ echo $?
1
```

`dbx date add` 输出偏移后的日期，与 `diff` 互为逆运算：

```bash
# 30 天后
$ dbx date add 2026-05-04 30
2026-06-03

# 30 天前 (负数)
$ dbx date add 2026-05-04 -30
2026-04-04

# 跨闰日 / 跨年都正确处理
$ dbx date add 2024-02-28 1
2024-02-29
$ dbx date add 2025-12-31 1
2026-01-01
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
dbx date diff 2024-08-13 2026-05-13   # → 638
```

> 提示：如果你习惯使用 `~/.local/bin`（多数发行版的默认约定），把上面命令里的路径相应替换即可。

## 目录结构

```
developer-toolbox/
├── pyproject.toml             # 项目元数据 (requires-python >= 3.11) + pytest 配置
├── .python-version            # uv 固定的解释器版本
├── .github/
│   └── workflows/
│       └── test.yml           # GitHub Actions: ubuntu / macos 上跑 pytest
├── bin/
│   └── dbx                    # bash 入口包装：跟随软链接 + uv run
├── src/
│   └── dbx/
│       ├── __init__.py        # 版本号
│       ├── __main__.py        # 支持 `python -m dbx`
│       ├── cli.py             # 主入口：自动发现并注册 commands/ 下的子命令组
│       └── commands/
│           ├── __init__.py
│           └── date/          # 子命令组 (group)
│               ├── __init__.py    # 注册 group 并装配各 action
│               ├── diff.py        # action: 计算日期差
│               └── add.py         # action: 日期偏移
└── tests/                     # 测试目录，按 src/dbx/ 层级一对一镜像
    ├── test_cli.py
    └── commands/
        └── date/
            ├── test_diff.py
            └── test_add.py
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
- 新增 action / group 时，请在 `tests/` 下按相同层级补充测试（例如 `tests/commands/string/test_upper.py`）。

## 开发与调试

直接通过 `python -m dbx` 也可以运行，方便在 IDE 里打断点：

```bash
uv run python -m dbx date diff 2024-08-13 2026-05-13
```

查看版本：

```bash
dbx --version    # → dbx 0.1.0
```

### 运行测试

测试基于 pytest 9，由 uv 在 dev 依赖组中管理。首次运行前确保 dev 依赖已同步：

```bash
uv sync                           # 默认会装上 dev 组
uv run pytest                     # 跑全部测试 (默认输出 coverage 报告)
uv run pytest tests/commands/date # 只跑某个子目录
uv run pytest -k diff -v          # 按关键字筛选 + 详细输出
uv run pytest --no-cov            # 临时关掉 coverage 提速
```

每次 push 到 `main` 或开 Pull Request 时，GitHub Actions 会在 `ubuntu-latest` 与 `macos-latest` 上自动跑同一套测试 (`.github/workflows/test.yml`)，外加 `ruff` / `mypy` 两个独立 job。

### 代码质量与 pre-commit

仓库配了 `.pre-commit-config.yaml`，hooks 直接复用项目级钉版的 ruff / mypy，与 CI 完全同源。建议克隆后开启一次本地 hook：

```bash
uv sync                            # 装上 pre-commit
uv run pre-commit install          # 装 git hook，之后 git commit 时自动跑
uv run pre-commit run --all-files  # 也可以手动一次性扫全仓
```

依赖升级由 `.github/dependabot.yml` 接管，每周一开 PR 升级 Python dev 工具链与 GitHub Actions 版本（`uv` / `github-actions` 两个 ecosystem）。

## License

见 [LICENSE](./LICENSE)。
