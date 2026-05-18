"""`dbx date diff <date1> <date2>` — 计算两个日期相隔的天数。"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime

_FORMAT = "%Y-%m-%d"


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "diff",
        help="计算两个日期相隔的天数",
        description="计算 <date1> 与 <date2> 相隔的天数 (输入格式：YYYY-MM-DD)。",
    )
    parser.add_argument("date1", help="日期一，格式 YYYY-MM-DD")
    parser.add_argument("date2", help="日期二，格式 YYYY-MM-DD")
    parser.set_defaults(handler=run)


def _parse(value: str) -> date:
    return datetime.strptime(value, _FORMAT).date()


def run(args: argparse.Namespace) -> int:
    try:
        d1 = _parse(args.date1)
        d2 = _parse(args.date2)
    except ValueError:
        print(
            f"[dbx] 错误：日期格式不正确，要求 YYYY-MM-DD (收到 '{args.date1}' 与 '{args.date2}')",
            file=sys.stderr,
        )
        return 1

    days = abs((d2 - d1).days)
    print(f"[dbx] {args.date1} 和 {args.date2} 相隔 {days} 天")
    return 0
