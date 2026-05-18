"""`dbx date from-ts` 的功能测试。"""

from __future__ import annotations

import pytest

from dbx.cli import main


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# ---------------------------------------------------------------------------
# 正常值 — 秒级时间戳
# ---------------------------------------------------------------------------


def test_seconds_timestamp_default_format(capsys: pytest.CaptureFixture[str]) -> None:
    # 1970-01-01 00:00:00 UTC → 本地时间可能偏移，用 --tz UTC 固定
    code, out, err = _run(capsys, "date", "from-ts", "--tz", "UTC", "0")
    assert code == 0
    assert out.strip() == "1970-01-01 00:00:00"
    assert err == ""


def test_seconds_timestamp_explicit_unit(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "from-ts", "-u", "s", "--tz", "UTC", "0")
    assert code == 0
    assert out.strip() == "1970-01-01 00:00:00"


def test_seconds_timestamp_known_value(capsys: pytest.CaptureFixture[str]) -> None:
    # 2024-05-18 14:59:54 UTC
    code, out, _ = _run(capsys, "date", "from-ts", "--tz", "UTC", "1716044394")
    assert code == 0
    assert out.strip() == "2024-05-18 14:59:54"


# ---------------------------------------------------------------------------
# 单位推断
# ---------------------------------------------------------------------------


def test_auto_detects_milliseconds(capsys: pytest.CaptureFixture[str]) -> None:
    # 1716044394000 ms == 1716044394 s
    code, out, _ = _run(capsys, "date", "from-ts", "--tz", "UTC", "1716044394000")
    assert code == 0
    assert out.strip() == "2024-05-18 14:59:54"


def test_auto_detects_microseconds(capsys: pytest.CaptureFixture[str]) -> None:
    # 1716044394000000 us == 1716044394 s
    code, out, _ = _run(capsys, "date", "from-ts", "--tz", "UTC", "1716044394000000")
    assert code == 0
    assert out.strip() == "2024-05-18 14:59:54"


def test_explicit_ms_unit(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "from-ts", "-u", "ms", "--tz", "UTC", "1716044394000")
    assert code == 0
    assert out.strip() == "2024-05-18 14:59:54"


def test_explicit_us_unit(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "from-ts", "-u", "us", "--tz", "UTC", "1716044394000000")
    assert code == 0
    assert out.strip() == "2024-05-18 14:59:54"


# ---------------------------------------------------------------------------
# 带小数的浮点数时间戳
# ---------------------------------------------------------------------------


def test_float_timestamp(capsys: pytest.CaptureFixture[str]) -> None:
    # 小数部分不影响秒级格式输出（截断到秒）
    code, out, _ = _run(capsys, "date", "from-ts", "--tz", "UTC", "1716044394.5")
    assert code == 0
    assert out.strip() == "2024-05-18 14:59:54"


# ---------------------------------------------------------------------------
# 时区参数
# ---------------------------------------------------------------------------


def test_tz_asia_shanghai(capsys: pytest.CaptureFixture[str]) -> None:
    # UTC+8，1716044394 UTC = 2024-05-18 22:59:54 CST
    code, out, _ = _run(capsys, "date", "from-ts", "--tz", "Asia/Shanghai", "1716044394")
    assert code == 0
    assert out.strip() == "2024-05-18 22:59:54"


def test_invalid_tz_returns_error(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, "date", "from-ts", "--tz", "Not/ATimezone", "0")
    assert code == 1
    assert out == ""
    assert "错误" in err
    assert "Not/ATimezone" in err


# ---------------------------------------------------------------------------
# 输出格式选项
# ---------------------------------------------------------------------------


def test_custom_format(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "from-ts", "--tz", "UTC", "-f", "%Y/%m/%d", "1716044394")
    assert code == 0
    assert out.strip() == "2024/05/18"


def test_iso_flag_overrides_default(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "from-ts", "--tz", "UTC", "--iso", "0")
    assert code == 0
    assert out.strip().startswith("1970-01-01T00:00:00")


def test_iso_flag_overrides_format(capsys: pytest.CaptureFixture[str]) -> None:
    # --iso 应忽略 -f
    code, out, _ = _run(capsys, "date", "from-ts", "--tz", "UTC", "--iso", "-f", "%Y", "0")
    assert code == 0
    assert out.strip().startswith("1970-01-01T00:00:00")


# ---------------------------------------------------------------------------
# 异常处理
# ---------------------------------------------------------------------------


def test_invalid_timestamp_string(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, "date", "from-ts", "not-a-number")
    assert code == 1
    assert out == ""
    assert "错误" in err


def test_overflow_large_timestamp(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, "date", "from-ts", "9" * 30)
    assert code == 1
    assert out == ""
    assert "错误" in err
    assert "超出" in err


def test_missing_timestamp_arg(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "from-ts"])
    assert exc.value.code == 2


def test_extra_positional_args_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "from-ts", "0", "extra"])
    assert exc.value.code == 2


def test_invalid_unit_choice_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "from-ts", "-u", "ns", "0"])
    assert exc.value.code == 2


# ---------------------------------------------------------------------------
# 边界值
# ---------------------------------------------------------------------------


def test_zero_timestamp(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "from-ts", "--tz", "UTC", "0")
    assert code == 0
    assert out.strip() == "1970-01-01 00:00:00"


def test_negative_timestamp(capsys: pytest.CaptureFixture[str]) -> None:
    # -1 s → 1969-12-31 23:59:59 UTC
    code, out, _ = _run(capsys, "date", "from-ts", "-u", "s", "--tz", "UTC", "-1")
    assert code == 0
    assert out.strip() == "1969-12-31 23:59:59"


def test_boundary_auto_s_vs_ms(capsys: pytest.CaptureFixture[str]) -> None:
    # 10^11 - 1 应推断为秒 (5138年)
    code, _, err = _run(capsys, "date", "from-ts", "--tz", "UTC", str(10**11 - 1))
    assert code == 0
    assert err == ""


def test_boundary_auto_ms_threshold(capsys: pytest.CaptureFixture[str]) -> None:
    # 10^11 应推断为毫秒
    code, _out, _ = _run(capsys, "date", "from-ts", "-u", "auto", "--tz", "UTC", str(10**11))
    assert code == 0
