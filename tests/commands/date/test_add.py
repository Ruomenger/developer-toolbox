"""`dbx date add` 的功能测试。"""

from __future__ import annotations

import pytest

from dbx.cli import main


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_add_positive_days(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, "date", "add", "2026-05-04", "30")
    assert code == 0
    assert out == "2026-06-03\n"
    assert err == ""


def test_add_negative_days(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "add", "2026-05-04", "-30")
    assert code == 0
    assert out == "2026-04-04\n"


def test_add_zero_returns_same_date(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "add", "2026-05-04", "0")
    assert code == 0
    assert out == "2026-05-04\n"


def test_add_into_leap_day(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "add", "2024-02-28", "1")
    assert code == 0
    assert out == "2024-02-29\n"


def test_add_across_year_boundary(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "add", "2025-12-31", "1")
    assert code == 0
    assert out == "2026-01-01\n"


def test_add_negative_across_year_boundary(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "add", "2026-01-01", "-1")
    assert code == 0
    assert out == "2025-12-31\n"


@pytest.mark.parametrize(
    "bad_date",
    [
        "not-a-date",
        "2026/05/04",   # 错误分隔符
        "2026-13-01",   # 非法月份
        "2026-02-30",   # 该日期不存在
        "26-05-04",     # 年份位数不对
    ],
)
def test_add_invalid_date_format(
    capsys: pytest.CaptureFixture[str], bad_date: str
) -> None:
    code, out, err = _run(capsys, "date", "add", bad_date, "1")
    assert code == 1
    assert out == ""
    assert "错误" in err
    assert "YYYY-MM-DD" in err


def test_add_non_integer_days_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "add", "2026-05-04", "abc"])
    assert exc.value.code == 2


def test_add_overflow_beyond_max_date(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, "date", "add", "9999-12-31", "1")
    assert code == 1
    assert out == ""
    assert "错误" in err
    assert "超出" in err


def test_add_overflow_before_min_date(capsys: pytest.CaptureFixture[str]) -> None:
    code, _, err = _run(capsys, "date", "add", "0001-01-01", "-1")
    assert code == 1
    assert "错误" in err


def test_add_missing_args(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "add", "2026-05-04"])
    assert exc.value.code == 2


def test_add_extra_args_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "add", "2026-05-04", "1", "extra"])
    assert exc.value.code == 2


def test_add_round_trip_with_diff(capsys: pytest.CaptureFixture[str]) -> None:
    """add 与 diff 互为逆运算：diff(base, add(base, N)) == N。"""
    code, out, _ = _run(capsys, "date", "add", "2026-05-04", "123")
    assert code == 0
    shifted = out.strip()

    code, out, _ = _run(capsys, "date", "diff", "2026-05-04", shifted)
    assert code == 0
    assert out.strip() == "123"
