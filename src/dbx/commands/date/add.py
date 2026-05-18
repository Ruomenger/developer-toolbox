"""`dbx date add <date> <±days>` —— 在给定日期上加/减天数，输出结果日期。"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta

_FORMAT = "%Y-%m-%d"


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "add",
        help="在指定日期上加/减天数",
        description=(
            "输出 <date> + <days> 的结果日期 (输入格式 YYYY-MM-DD，days 为整数，可为负)。"
        ),
    )
    parser.add_argument("date", help="基准日期，格式 YYYY-MM-DD")
    parser.add_argument("days", type=int, help="偏移天数，整数 (可为负)")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    try:
        base = datetime.strptime(args.date, _FORMAT).date()
    except ValueError:
        print(
            f"[dbx] 错误：日期格式不正确，要求 YYYY-MM-DD (收到 '{args.date}')",
            file=sys.stderr,
        )
        return 1

    try:
        result = base + timedelta(days=args.days)
    except OverflowError:
        print(
            f"[dbx] 错误：日期超出可表达范围 (基准 {args.date} 偏移 {args.days} 天)",
            file=sys.stderr,
        )
        return 1

    print(result.isoformat())
    return 0
