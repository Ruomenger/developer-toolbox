"""`dbx date to-ts [datetime_str ...]` —— 将日期时间字符串转换为时间戳。"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_FALLBACK_FORMATS = [
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d",
    "%Y-%m-%d",
]


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "to-ts",
        help="将日期时间字符串转换为时间戳",
        description=("将日期时间字符串转换为时间戳。如果不提供任何参数，则默认输出当前时间戳。"),
    )
    parser.add_argument(
        "datetime_str",
        nargs="*",
        help=(
            '待转换的日期时间字符串（如 "2024-05-18 16:26:33"）。'
            '支持使用 "now" 或留空来获取当前时间。'
        ),
    )
    parser.add_argument(
        "-u",
        "--unit",
        choices=["s", "ms", "us"],
        default="s",
        help="输出时间戳的单位，默认为 s (秒)",
    )
    parser.add_argument(
        "--tz",
        default=None,
        metavar="TZ",
        help="输入时间所属的时区 (如 Asia/Shanghai)。默认使用系统本地时区",
    )
    parser.add_argument(
        "-f",
        "--format",
        default=None,
        dest="fmt",
        metavar="FORMAT",
        help='指定输入时间的解析格式 (如 "%%Y-%%m-%%d %%H:%%M:%%S")。若不指定，将尝试智能解析',
    )
    parser.set_defaults(handler=run)


def _resolve_tz(tz_name: str) -> ZoneInfo | None:
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, KeyError):
        return None


def _parse_dt(dt_str: str, fmt: str | None) -> datetime:
    if fmt:
        return datetime.strptime(dt_str, fmt)

    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        pass

    for fallback in _FALLBACK_FORMATS:
        try:
            return datetime.strptime(dt_str, fallback)
        except ValueError:
            continue

    raise ValueError(dt_str)


def _apply_unit(ts: float, unit: str) -> int:
    if unit == "ms":
        return int(ts * 1_000)
    if unit == "us":
        return int(ts * 1_000_000)
    return int(ts)


def run(args: argparse.Namespace) -> int:
    dt_str = " ".join(args.datetime_str) if args.datetime_str else "now"

    if dt_str.lower() == "now":
        ts = datetime.now(UTC).timestamp()
        print(_apply_unit(ts, args.unit))
        return 0

    try:
        dt = _parse_dt(dt_str, args.fmt)
    except ValueError:
        if args.fmt:
            print(
                f"[dbx] 错误：日期字符串 '{dt_str}' 与格式 '{args.fmt}' 不匹配",
                file=sys.stderr,
            )
        else:
            print(
                f"[dbx] 错误：无法自动识别日期格式 '{dt_str}'，请使用 -f 明确指定",
                file=sys.stderr,
            )
        return 1

    if dt.tzinfo is not None:
        pass
    elif args.tz:
        tz = _resolve_tz(args.tz)
        if tz is None:
            print(
                f"[dbx] 错误：未知时区 '{args.tz}'",
                file=sys.stderr,
            )
            return 1
        dt = dt.replace(tzinfo=tz)
    else:
        dt = dt.astimezone()

    print(_apply_unit(dt.timestamp(), args.unit))
    return 0
