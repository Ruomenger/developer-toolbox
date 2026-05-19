"""`dbx date cal [year] [month]` —— 终端日历，支持周数、今天高亮、自适应布局。"""

from __future__ import annotations

import argparse
import calendar
import os
import shutil
import sys
from datetime import date

_MONTH_NAMES = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

_DAY_ABBRS_MON = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
_DAY_ABBRS_SUN = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]

_REVERSE_ON = "\033[7m"
_REVERSE_OFF = "\033[0m"

_BLOCK_WIDTH_NO_WK = 20
_BLOCK_WIDTH_WK = 23
_GAP = 2


def _month_type(value: str) -> int:
    try:
        m = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"无效的月份: '{value}'") from None
    if m < 1 or m > 12:
        raise argparse.ArgumentTypeError(f"月份必须在 1-12 之间 (收到 {m})")
    return m


def _positive_int(value: str) -> int:
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"无效的正整数: '{value}'") from None
    if n < 1:
        raise argparse.ArgumentTypeError(f"每行月数必须 >= 1 (收到 {n})")
    return n


def _should_use_color(no_color_flag: bool) -> bool:
    return not no_color_flag and "NO_COLOR" not in os.environ and sys.stdout.isatty()


def _visible_len(s: str) -> int:
    return len(s.replace(_REVERSE_ON, "").replace(_REVERSE_OFF, ""))


def _pad_line(line: str, target_width: int) -> str:
    visible = _visible_len(line)
    return line + " " * max(0, target_width - visible)


def _day_cell(day: int, is_today: bool, use_color: bool) -> str:
    cell = f"{day:2d}"
    if is_today and use_color:
        return f"{_REVERSE_ON}{cell}{_REVERSE_OFF}"
    return cell


def _month_block(
    year: int,
    month: int,
    *,
    first_weekday: int,
    week_numbers: bool,
    today: date | None,
    use_color: bool,
) -> list[str]:
    cal = calendar.Calendar(firstweekday=first_weekday)
    weeks = cal.monthdatescalendar(year, month)

    block_width = _BLOCK_WIDTH_WK if week_numbers else _BLOCK_WIDTH_NO_WK
    abbrs = _DAY_ABBRS_SUN if first_weekday == calendar.SUNDAY else _DAY_ABBRS_MON

    title = f"{_MONTH_NAMES[month]} {year}"
    title_line = title.center(block_width)

    day_header = " ".join(abbrs)
    if week_numbers:
        day_header = "Wk " + day_header

    thursday_index = (3 - first_weekday) % 7

    lines: list[str] = [title_line, day_header]

    for week in weeks:
        parts: list[str] = []
        if week_numbers:
            wk_num = week[thursday_index].isocalendar()[1]
            parts.append(f"{wk_num:2d}")
        for d in week:
            if d.month != month:
                parts.append("  ")
            else:
                is_today = today is not None and d == today
                parts.append(_day_cell(d.day, is_today, use_color))
        lines.append(" ".join(parts))

    return [_pad_line(line, block_width) for line in lines]


def _render_single_month(
    year: int,
    month: int,
    *,
    first_weekday: int,
    week_numbers: bool,
    today: date | None,
    use_color: bool,
) -> str:
    block = _month_block(
        year,
        month,
        first_weekday=first_weekday,
        week_numbers=week_numbers,
        today=today,
        use_color=use_color,
    )
    return "\n".join(block)


def _auto_months_per_row(term_width: int, week_numbers: bool) -> int:
    block_width = _BLOCK_WIDTH_WK if week_numbers else _BLOCK_WIDTH_NO_WK
    return max(1, (term_width + _GAP) // (block_width + _GAP))


def _render_year(
    year: int,
    *,
    first_weekday: int,
    week_numbers: bool,
    months_per_row: int,
    today: date | None,
    use_color: bool,
) -> str:
    blocks = [
        _month_block(
            year,
            m,
            first_weekday=first_weekday,
            week_numbers=week_numbers,
            today=today,
            use_color=use_color,
        )
        for m in range(1, 13)
    ]

    block_width = _BLOCK_WIDTH_WK if week_numbers else _BLOCK_WIDTH_NO_WK
    row_width = months_per_row * block_width + (months_per_row - 1) * _GAP

    result_lines: list[str] = [str(year).center(row_width)]

    for row_start in range(0, 12, months_per_row):
        row_blocks = blocks[row_start : row_start + months_per_row]
        max_lines = max(len(b) for b in row_blocks)

        for line_idx in range(max_lines):
            parts: list[str] = []
            for col, block in enumerate(row_blocks):
                if col > 0:
                    parts.append(" " * _GAP)
                cell = block[line_idx] if line_idx < len(block) else " " * block_width
                parts.append(cell)
            result_lines.append("".join(parts))

        result_lines.append("")

    while result_lines and result_lines[-1] == "":
        result_lines.pop()

    return "\n".join(result_lines)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "cal",
        help="终端日历",
        description="显示终端日历，支持指定年份和月份，可配置每周起始日和周数显示。",
    )
    parser.add_argument(
        "year",
        nargs="?",
        type=int,
        default=None,
        help="年份，默认为当前年份",
    )
    parser.add_argument(
        "month",
        nargs="?",
        type=_month_type,
        default=None,
        help="月份 (1-12)，不指定则显示全年",
    )
    parser.add_argument(
        "-s",
        "--week-numbers",
        action="store_true",
        default=False,
        help="显示 ISO 8601 周数",
    )
    parser.add_argument(
        "-f",
        "--first-day",
        choices=["mon", "sun"],
        default="mon",
        help="每周第一天 (默认: mon)",
    )
    parser.add_argument(
        "-m",
        "--months-per-row",
        type=_positive_int,
        default=None,
        metavar="N",
        help="全年视图每行月数 (默认自动计算)",
    )
    parser.add_argument(
        "--no-today",
        action="store_true",
        default=False,
        help="不高亮今天",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="禁用颜色",
    )
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    year = args.year if args.year is not None else date.today().year
    month = args.month

    first_weekday = calendar.SUNDAY if args.first_day == "sun" else calendar.MONDAY

    today = None if args.no_today else date.today()
    use_color = _should_use_color(args.no_color)

    if month is not None:
        output = _render_single_month(
            year,
            month,
            first_weekday=first_weekday,
            week_numbers=args.week_numbers,
            today=today,
            use_color=use_color,
        )
    else:
        term_width = shutil.get_terminal_size((80, 24)).columns
        months_per_row = (
            args.months_per_row
            if args.months_per_row
            else _auto_months_per_row(term_width, args.week_numbers)
        )
        output = _render_year(
            year,
            first_weekday=first_weekday,
            week_numbers=args.week_numbers,
            months_per_row=months_per_row,
            today=today,
            use_color=use_color,
        )

    print(output)
    return 0
