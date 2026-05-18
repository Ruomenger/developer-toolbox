"""`dbx date diff` 的功能测试。"""

from __future__ import annotations

import pytest

from dbx.cli import main


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_positive_diff(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, "date", "diff", "2026-04-13", "2026-08-11")
    assert code == 0
    assert out == "120\n"
    assert err == ""


def test_negative_diff(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "diff", "2026-08-13", "2026-08-11")
    assert code == 0
    assert out == "-2\n"


def test_zero_diff_same_date(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "diff", "2026-08-11", "2026-08-11")
    assert code == 0
    assert out == "0\n"


def test_diff_across_leap_year(capsys: pytest.CaptureFixture[str]) -> None:
    # 2024 是闰年，2024-02-28 → 2024-03-01 跨过 2/29
    code, out, _ = _run(capsys, "date", "diff", "2024-02-28", "2024-03-01")
    assert code == 0
    assert out == "2\n"


def test_diff_year_boundary(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "diff", "2025-12-31", "2026-01-01")
    assert code == 0
    assert out == "1\n"


@pytest.mark.parametrize(
    "bad_pair",
    [
        ("2026-05-13", "oops"),
        ("not-a-date", "2026-05-13"),
        ("2026/05/13", "2026-05-14"),   # 错误分隔符
        ("2026-13-01", "2026-05-13"),   # 非法月份
        ("2026-02-30", "2026-05-13"),   # 该日期不存在
        ("26-05-13", "2026-05-13"),     # 年份位数不对
    ],
)
def test_invalid_date_format_returns_error(
    capsys: pytest.CaptureFixture[str], bad_pair: tuple[str, str]
) -> None:
    code, out, err = _run(capsys, "date", "diff", *bad_pair)
    assert code == 1
    assert out == ""
    assert "错误" in err
    assert "YYYY-MM-DD" in err


def test_missing_args_exits_with_usage_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "diff"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "usage" in err.lower() or "用法" in err


def test_extra_args_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "diff", "2026-01-01", "2026-01-02", "2026-01-03"])
    assert exc.value.code == 2
