"""`dbx date` 子命令组。新增 action 时，在本目录新建模块并在此 register。"""

from __future__ import annotations

import argparse

from . import diff


def register(subparsers: argparse._SubParsersAction) -> None:
    group = subparsers.add_parser("date", help="日期相关工具")
    actions = group.add_subparsers(dest="action", metavar="<action>")
    actions.required = True
    diff.register(actions)
