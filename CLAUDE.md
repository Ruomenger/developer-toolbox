# CLAUDE.md — developer-toolbox 项目快速上下文

`dbx` 是个人命令行工具箱：子命令组 + action 架构，目标平台 macOS / Linux。

---

## 1. 提交规范

- 用 **Conventional Commits**：`type(scope): 简短摘要`
  - 常用 type：`feat` / `fix` / `chore` / `ci` / `docs` / `test` / `style` / `refactor` / `perf`
  - type 与 scope 用英文，摘要用中文。
- body 用 **TAB 缩进的编号列表**（不是空格）。
- 不加 `Co-Authored-By`。
- 不主动 push；用户说 "push" 才推。
- 不主动 commit；用户说 "提交" 才提。

---

## 2. 工具链与依赖

- Python 3.11，由 `.python-version` 钉死，`uv` 自动拉。
- 包管理统一用 `uv`，不要 pip / poetry / 手动 venv。
- 依赖严格 `==` 钉版，包括所有 dev 工具链。`uv add --dev` 默认写 `>=`，手动改成 `==`。
- 保留 `[[tool.uv.index]]` 中 `url = "https://pypi.org/simple"` `default = true`，不可删。
- ruff 启用 E/W/F/I/B/UP/SIM/RUF；`ignore` 必须包含 RUF001/002/003。
- mypy `strict = true`，覆盖 `src` 与 `tests`。
- pytest 9 + pytest-cov；`addopts` 含 `--cov --cov-report=term-missing`；不设 `fail_under`。
- pytest `--import-mode=importlib`，`tests/` 下不放 `__init__.py`。
- pre-commit 使用 local hooks 调 `uv run ruff/mypy`。

---

## 3. 架构与扩展约定

### 目录契约

```
src/dbx/
├── cli.py               # 自动发现 commands/ 下的 group，禁止改
└── commands/
    └── <group>/         # 子命令组：package（带 __init__.py）
        ├── __init__.py     # 实现 register(subparsers)
        └── <action>.py     # 实现 register(...) + run(...)
```

### 加新 action / group

- 不要改 `cli.py`。
- group `__init__.py` 中 `from . import <action>` 并 `<action>.register(actions)`。
- 每个 action 文件实现：
  - `register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None`
  - `run(args: argparse.Namespace) -> int` 返回退出码
  - `parser.set_defaults(handler=run)`
- 文件头加 `from __future__ import annotations`。
- 运行期下标的泛型（如 `_SubParsersAction[X]` 作为值表达式）放在 `if TYPE_CHECKING:` 块内。

### 测试镜像（强约束）

- 每加一个 action / group，**必须**在 `tests/` 下按相同层级补测试：
  - `src/dbx/commands/<group>/<action>.py` → `tests/commands/<group>/test_<action>.py`
- 覆盖：正常值、边界（闰年、跨年、溢出）、参数化非法输入、argparse 缺参/多参、与逆运算命令的 round-trip。

---

## 4. CLI 输出契约

- 成功路径：stdout 只输出业务结果（整数、ISO 日期等），无前缀、无中文修饰。
- 错误路径：stderr，格式 `[dbx] 错误：<原因>`，退出码 **1**。
- 参数错误（缺参、类型错、不在 choices 内）：交给 argparse，退出码 **2**。
- 差值类命令固定方向（如 `dbx date diff` 始终是 `date2 - date1`），写在 help 与 README。

---

## 5. CI 与本地校验

- workflow `.github/workflows/test.yml`，name 为 `ci`，4 个 job：
  - `lint`（ruff check + format check，ubuntu）
  - `typecheck`（mypy strict，ubuntu）
  - `pytest`（ubuntu + macos 矩阵）
- 触发：push 到 main 和所有 PR；`concurrency.cancel-in-progress: true`。
- Actions 版本：`actions/checkout@v5` + `astral-sh/setup-uv@v7`（均 Node 24）。升级前用 `curl <action.yml> | grep using:` 确认。
- Dependabot 每周一升 `uv` 与 `github-actions`，prefix `chore(deps)` / `ci(deps)`。

---

## 6. pre-commit

- 开发机首装：`uv run pre-commit install`。
- 手动跑全量前**先 `git add -A`**：`pre-commit run --all-files` 只覆盖 tracked 文件。
- hook：ruff check / ruff format --check / mypy / yaml / toml / merge-conflict / eof / trailing。

---

## 7. 常用命令速查

```bash
uv sync                                       # 同步含 dev 依赖
uv run pytest                                 # 测试 (带 coverage)
uv run pytest tests/commands/date             # 限定目录
uv run pytest -k diff -v                      # 关键字 + 详细
uv run pytest --no-cov                        # 临时关 coverage

uv run ruff check .
uv run ruff format .                          # 写盘修
uv run ruff format --check .                  # 仅校验
uv run mypy

uv run pre-commit install                     # 首装
uv run pre-commit run --all-files             # 手动一次性扫 (先 git add)

./bin/dbx <group> <action> ...
uv run python -m dbx <group> <action> ...     # 等价，方便 IDE 调试
```
