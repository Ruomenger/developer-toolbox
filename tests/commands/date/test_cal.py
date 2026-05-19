"""`dbx date cal` 的功能测试。"""

from __future__ import annotations

from datetime import date

import pytest

from dbx.cli import main
from dbx.commands.date.cal import (
    _auto_months_per_row,
    _month_block,
    _render_single_month,
)


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# ---------------------------------------------------------------------------
# 参数解析
# ---------------------------------------------------------------------------


def test_no_args_shows_current_year(capsys: pytest.CaptureFixture[str]) -> None:
    from datetime import date as _date

    code, out, err = _run(capsys, "date", "cal", "--no-color", "--no-today")
    assert code == 0
    assert err == ""
    assert str(_date.today().year) in out


def test_explicit_year(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, "date", "cal", "2024", "--no-color", "--no-today")
    assert code == 0
    assert err == ""
    assert "2024" in out


def test_year_and_month(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, "date", "cal", "2026", "5", "--no-color", "--no-today")
    assert code == 0
    assert err == ""
    assert "May 2026" in out


def test_invalid_year_non_integer(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "cal", "abc"])
    assert exc.value.code == 2


def test_invalid_month_out_of_range(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "cal", "2026", "13"])
    assert exc.value.code == 2


def test_invalid_month_non_integer(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "cal", "2026", "abc"])
    assert exc.value.code == 2


def test_invalid_first_day(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "cal", "--first-day", "tue"])
    assert exc.value.code == 2


def test_extra_positional_args(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "cal", "2026", "5", "extra"])
    assert exc.value.code == 2


# ---------------------------------------------------------------------------
# 核心输出 (单月视图, 无颜色)
# ---------------------------------------------------------------------------


def test_may_2026_monday_first(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, "date", "cal", "2026", "5", "--no-color", "--no-today")
    assert code == 0
    assert err == ""
    lines = out.splitlines()
    assert any("May 2026" in line for line in lines)
    assert any("Mo Tu We Th Fr Sa Su" in line for line in lines)
    assert "31" in out


def test_may_2026_first_row_alignment(capsys: pytest.CaptureFixture[str]) -> None:
    """May 1 2026 is Friday — first row should have 4 blanks then 1 2 3."""
    code, out, _ = _run(capsys, "date", "cal", "2026", "5", "--no-color", "--no-today")
    assert code == 0
    lines = out.splitlines()
    header_idx = next(i for i, line in enumerate(lines) if "Mo Tu We" in line)
    first_data_line = lines[header_idx + 1]
    assert first_data_line.strip().startswith("1")
    assert " 1" in first_data_line
    assert " 2" in first_data_line
    assert " 3" in first_data_line


def test_feb_2024_leap_year(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "cal", "2024", "2", "--no-color", "--no-today")
    assert code == 0
    assert "February 2024" in out
    assert "29" in out


def test_feb_2023_non_leap_year(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "cal", "2023", "2", "--no-color", "--no-today")
    assert code == 0
    assert "February 2023" in out
    lines = out.splitlines()
    for line in lines[2:]:
        assert "29" not in line


def test_jan_2026_starts_on_thursday(capsys: pytest.CaptureFixture[str]) -> None:
    """Jan 1 2026 is Thursday — first row should have 3 blanks then 1."""
    code, out, _ = _run(capsys, "date", "cal", "2026", "1", "--no-color", "--no-today")
    assert code == 0
    lines = out.splitlines()
    header_idx = next(i for i, line in enumerate(lines) if "Mo Tu We" in line)
    first_data_line = lines[header_idx + 1]
    assert " 1" in first_data_line
    assert first_data_line.strip().startswith("1")


# ---------------------------------------------------------------------------
# 周日为每周第一天
# ---------------------------------------------------------------------------


def test_sunday_first_header(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(
        capsys, "date", "cal", "2026", "5", "--first-day", "sun", "--no-color", "--no-today"
    )
    assert code == 0
    lines = out.splitlines()
    header_line = next(line for line in lines if "Su Mo Tu" in line)
    assert header_line.strip().startswith("Su")


def test_sunday_first_may_2026_alignment(capsys: pytest.CaptureFixture[str]) -> None:
    """May 1 2026 is Friday — with Sunday-first, 5 blanks before 1."""
    code, out, _ = _run(
        capsys, "date", "cal", "2026", "5", "--first-day", "sun", "--no-color", "--no-today"
    )
    assert code == 0
    lines = out.splitlines()
    header_idx = next(i for i, line in enumerate(lines) if "Su Mo Tu" in line)
    first_data_line = lines[header_idx + 1]
    assert first_data_line.strip().startswith("1")


# ---------------------------------------------------------------------------
# 周数
# ---------------------------------------------------------------------------


def test_week_numbers_flag(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "cal", "2026", "5", "-s", "--no-color", "--no-today")
    assert code == 0
    assert "Wk" in out


def test_week_numbers_may_2026(capsys: pytest.CaptureFixture[str]) -> None:
    """May 2026 spans ISO weeks 18-22."""
    code, out, _ = _run(capsys, "date", "cal", "2026", "5", "-s", "--no-color", "--no-today")
    assert code == 0
    lines = out.splitlines()
    wk_header_idx = next(i for i, line in enumerate(lines) if "Wk" in line)
    data_lines = lines[wk_header_idx + 1 :]
    wk_nums = []
    for line in data_lines:
        stripped = line.strip()
        if stripped:
            wk_nums.append(int(stripped.split()[0]))
    assert wk_nums == [18, 19, 20, 21, 22]


def test_week_numbers_jan_2026_starts_week_1(capsys: pytest.CaptureFixture[str]) -> None:
    """Jan 1 2026 is Thursday → first week is ISO week 1."""
    code, out, _ = _run(capsys, "date", "cal", "2026", "1", "-s", "--no-color", "--no-today")
    assert code == 0
    lines = out.splitlines()
    wk_header_idx = next(i for i, line in enumerate(lines) if "Wk" in line)
    first_data = lines[wk_header_idx + 1].strip()
    assert first_data.split()[0] == "1"


def test_week_numbers_dec_2026_has_week_53(capsys: pytest.CaptureFixture[str]) -> None:
    """2026 has 53 ISO weeks (Jan 1 is Thursday)."""
    code, out, _ = _run(capsys, "date", "cal", "2026", "12", "-s", "--no-color", "--no-today")
    assert code == 0
    lines = out.splitlines()
    last_data_line = ""
    for line in reversed(lines):
        stripped = line.strip()
        if stripped and stripped[0].isdigit():
            last_data_line = stripped
            break
    assert "53" in last_data_line


def test_week_numbers_sunday_first(capsys: pytest.CaptureFixture[str]) -> None:
    """Week numbers should still be correct with Sunday-first.
    With Sunday-first, May 2026 has 6 week rows (vs 5 with Monday-first)
    because the first row starts with Sunday May 3, creating an extra row."""
    code, out, _ = _run(
        capsys,
        "date",
        "cal",
        "2026",
        "5",
        "-s",
        "--first-day",
        "sun",
        "--no-color",
        "--no-today",
    )
    assert code == 0
    lines = out.splitlines()
    wk_header_idx = next(i for i, line in enumerate(lines) if "Wk" in line)
    data_lines = lines[wk_header_idx + 1 :]
    wk_nums = []
    for line in data_lines:
        stripped = line.strip()
        if stripped:
            wk_nums.append(int(stripped.split()[0]))
    assert wk_nums == [18, 19, 20, 21, 22, 23]


# ---------------------------------------------------------------------------
# 全年视图
# ---------------------------------------------------------------------------


def test_year_view_all_months(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "cal", "2026", "--no-color", "--no-today")
    assert code == 0
    for month_name in [
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
    ]:
        assert month_name in out


def test_year_view_custom_months_per_row(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "cal", "2026", "-m", "2", "--no-color", "--no-today")
    assert code == 0
    assert "2026" in out


def test_year_view_single_column(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "cal", "2026", "-m", "1", "--no-color", "--no-today")
    assert code == 0
    assert "2026" in out


# ---------------------------------------------------------------------------
# 今天高亮 (直接调用渲染函数，避免 TTY 检测)
# ---------------------------------------------------------------------------


def test_today_highlighted_with_color() -> None:
    block = _month_block(
        2026,
        5,
        first_weekday=0,
        week_numbers=False,
        today=date(2026, 5, 19),
        use_color=True,
    )
    full = "\n".join(block)
    assert "\033[7m" in full
    assert "\033[0m" in full


def test_today_not_highlighted_with_no_today() -> None:
    block = _month_block(
        2026,
        5,
        first_weekday=0,
        week_numbers=False,
        today=None,
        use_color=True,
    )
    full = "\n".join(block)
    assert "\033[7m" not in full


def test_today_not_highlighted_for_other_month() -> None:
    """today is in March, rendering May — no highlight."""
    block = _month_block(
        2026,
        5,
        first_weekday=0,
        week_numbers=False,
        today=date(2026, 3, 15),
        use_color=True,
    )
    full = "\n".join(block)
    assert "\033[7m" not in full


def test_no_color_flag_disables_highlight(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "cal", "2026", "5", "--no-color")
    assert code == 0
    assert "\033[" not in out


# ---------------------------------------------------------------------------
# 自适应布局
# ---------------------------------------------------------------------------


def test_auto_months_per_row_80_cols_no_wk() -> None:
    assert _auto_months_per_row(80, False) == 3


def test_auto_months_per_row_80_cols_with_wk() -> None:
    assert _auto_months_per_row(80, True) == 3


def test_auto_months_per_row_120_cols_no_wk() -> None:
    assert _auto_months_per_row(120, False) == 5


def test_auto_months_per_row_120_cols_with_wk() -> None:
    assert _auto_months_per_row(120, True) == 4


def test_auto_months_per_row_narrow_terminal() -> None:
    assert _auto_months_per_row(40, False) == 1


def test_auto_months_per_row_wide_terminal() -> None:
    result = _auto_months_per_row(200, False)
    assert result >= 7


# ---------------------------------------------------------------------------
# 月块渲染直接测试
# ---------------------------------------------------------------------------


def test_month_block_width_no_wk() -> None:
    block = _month_block(
        2026,
        5,
        first_weekday=0,
        week_numbers=False,
        today=None,
        use_color=False,
    )
    for line in block:
        assert len(line) == 20


def test_month_block_width_with_wk() -> None:
    block = _month_block(
        2026,
        5,
        first_weekday=0,
        week_numbers=True,
        today=None,
        use_color=False,
    )
    for line in block:
        assert len(line) == 23


def test_render_single_month_returns_string() -> None:
    result = _render_single_month(
        2026,
        5,
        first_weekday=0,
        week_numbers=False,
        today=None,
        use_color=False,
    )
    assert isinstance(result, str)
    assert "May 2026" in result


# ---------------------------------------------------------------------------
# 月份边界
# ---------------------------------------------------------------------------


def test_month_1_january(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "cal", "2026", "1", "--no-color", "--no-today")
    assert code == 0
    assert "January 2026" in out


def test_month_12_december(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "cal", "2026", "12", "--no-color", "--no-today")
    assert code == 0
    assert "December 2026" in out


def test_month_zero_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "cal", "2026", "0"])
    assert exc.value.code == 2


def test_invalid_months_per_row(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "cal", "2026", "-m", "0"])
    assert exc.value.code == 2
