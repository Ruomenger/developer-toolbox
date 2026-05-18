"""`dbx date from-ts <timestamp>` —— 将时间戳转换为人类可读的日期时间。"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_DEFAULT_FORMAT = "%Y-%m-%d %H:%M:%S"
_S_THRESHOLD = 10**11
_MS_THRESHOLD = 10**14


def _infer_unit(value: float) -> str:
    magnitude = int(abs(value))
    if magnitude < _S_THRESHOLD:
        return "s"
    if magnitude < _MS_THRESHOLD:
        return "ms"
    return "us"


def _to_seconds(value: float, unit: str) -> float:
    if unit == "ms":
        return value / 1_000
    if unit == "us":
        return value / 1_000_000
    return value


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "from-ts",
        help="将时间戳转换为日期时间",
        description="将时间戳转换为日期时间。",
    )
    parser.add_argument("timestamp", help="时间戳，支持整数或带小数的浮点数")
    parser.add_argument(
        "-u",
        "--unit",
        choices=["auto", "s", "ms", "us"],
        default="auto",
        help="时间戳单位，默认 auto (根据长度推断)",
    )
    parser.add_argument(
        "--tz",
        default=None,
        metavar="TZ",
        help="输出时区 (如 Asia/Shanghai)。默认使用系统时区",
    )
    parser.add_argument(
        "-f",
        "--format",
        default=None,
        dest="fmt",
        metavar="FORMAT",
        help="自定义输出时间格式",
    )
    parser.add_argument(
        "--iso",
        action="store_true",
        help="强制使用 ISO 8601 格式输出",
    )
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    try:
        ts_raw = float(args.timestamp)
    except ValueError:
        print(
            f"[dbx] 错误：无法将 '{args.timestamp}' 解析为有效的时间戳数字",
            file=sys.stderr,
        )
        return 1

    unit = args.unit if args.unit != "auto" else _infer_unit(ts_raw)
    ts_seconds = _to_seconds(ts_raw, unit)

    try:
        if args.tz:
            try:
                tz = ZoneInfo(args.tz)
            except (ZoneInfoNotFoundError, KeyError):
                print(
                    f"[dbx] 错误：未知时区 '{args.tz}'",
                    file=sys.stderr,
                )
                return 1
            dt = datetime.fromtimestamp(ts_seconds, tz=tz)
        else:
            dt = datetime.fromtimestamp(ts_seconds).astimezone()
    except (OSError, OverflowError, ValueError):
        print(
            f"[dbx] 错误：时间戳 '{args.timestamp}' 超出可表达范围",
            file=sys.stderr,
        )
        return 1

    if args.iso:
        print(dt.isoformat())
    else:
        fmt = args.fmt if args.fmt else _DEFAULT_FORMAT
        print(dt.strftime(fmt))

    return 0
