"""`dbx date` 子命令组。新增 action 时，在本目录新建模块并在此 register。"""

from __future__ import annotations

import argparse

from . import add, diff, from_ts


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    group = subparsers.add_parser("date", help="日期相关工具")
    actions = group.add_subparsers(dest="action", metavar="<action>")
    actions.required = True
    diff.register(actions)
    add.register(actions)
    from_ts.register(actions)
