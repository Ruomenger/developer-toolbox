"""`dbx` 主入口行为测试 (cli.py)。"""

from __future__ import annotations

import pytest

from dbx import __version__
from dbx.cli import build_parser, main


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"dbx {__version__}"


def test_no_args_shows_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main([])
    # argparse 在缺少必选 subcommand 时退出码为 2
    assert exc.value.code == 2
    assert "usage" in capsys.readouterr().err.lower()


def test_unknown_group_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["definitely-not-a-real-group"])
    assert exc.value.code == 2


def test_help_lists_known_groups(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    # 自动发现的 date 组应当出现在帮助里
    assert "date" in out


def test_date_group_requires_action(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date"])
    assert exc.value.code == 2


def test_build_parser_autodiscovers_date_group() -> None:
    """直接验证自动注册机制：不依赖 main(), 检查 parser 内部结构。"""
    parser = build_parser()
    # 找到顶层 subparsers 中的 group 名字
    subparsers_actions = [
        a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction"
    ]
    assert subparsers_actions, "主 parser 应当存在 subparsers"
    group_names = set(subparsers_actions[0].choices.keys())
    assert "date" in group_names
