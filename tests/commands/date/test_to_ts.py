"""`dbx date to-ts` 的功能测试。"""

from __future__ import annotations

import time

import pytest

from dbx.cli import main


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# ---------------------------------------------------------------------------
# 已知值 — UTC 锚点
# ---------------------------------------------------------------------------


def test_known_utc_datetime(capsys: pytest.CaptureFixture[str]) -> None:
    # 2024-05-18 14:59:54 UTC == 1716044394
    code, out, err = _run(capsys, "date", "to-ts", "--tz", "UTC", "2024-05-18", "14:59:54")
    assert code == 0
    assert out.strip() == "1716044394"
    assert err == ""


def test_known_utc_datetime_iso_format(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "to-ts", "2024-05-18T14:59:54+00:00")
    assert code == 0
    assert out.strip() == "1716044394"


def test_epoch_utc(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "to-ts", "--tz", "UTC", "1970-01-01", "00:00:00")
    assert code == 0
    assert out.strip() == "0"


# ---------------------------------------------------------------------------
# 单位换算
# ---------------------------------------------------------------------------


def test_unit_ms(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "to-ts", "-u", "ms", "--tz", "UTC", "2024-05-18T14:59:54")
    assert code == 0
    assert out.strip() == "1716044394000"


def test_unit_us(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "to-ts", "-u", "us", "--tz", "UTC", "2024-05-18T14:59:54")
    assert code == 0
    assert out.strip() == "1716044394000000"


def test_default_unit_is_seconds(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "to-ts", "--tz", "UTC", "2024-05-18T14:59:54")
    assert code == 0
    assert len(out.strip()) == 10  # 秒级时间戳 10 位


# ---------------------------------------------------------------------------
# 时区参数
# ---------------------------------------------------------------------------


def test_tz_asia_shanghai(capsys: pytest.CaptureFixture[str]) -> None:
    # 2024-05-18 22:59:54 CST (UTC+8) == 1716044394 UTC
    code, out, _ = _run(capsys, "date", "to-ts", "--tz", "Asia/Shanghai", "2024-05-18", "22:59:54")
    assert code == 0
    assert out.strip() == "1716044394"


def test_aware_datetime_ignores_tz_flag(capsys: pytest.CaptureFixture[str]) -> None:
    # 字符串自带 +08:00，即使指定 --tz UTC 也应用字符串自带时区
    code, out, _ = _run(capsys, "date", "to-ts", "--tz", "UTC", "2024-05-18T22:59:54+08:00")
    assert code == 0
    assert out.strip() == "1716044394"


def test_invalid_tz_returns_error(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, "date", "to-ts", "--tz", "Not/ATimezone", "2024-05-18")
    assert code == 1
    assert out == ""
    assert "错误" in err
    assert "Not/ATimezone" in err


# ---------------------------------------------------------------------------
# "now" 与默认行为
# ---------------------------------------------------------------------------


def test_now_keyword_returns_reasonable_timestamp(capsys: pytest.CaptureFixture[str]) -> None:
    before = int(time.time())
    code, out, _ = _run(capsys, "date", "to-ts", "now")
    after = int(time.time())
    assert code == 0
    ts = int(out.strip())
    assert before <= ts <= after


def test_now_case_insensitive(capsys: pytest.CaptureFixture[str]) -> None:
    before = int(time.time())
    code, out, _ = _run(capsys, "date", "to-ts", "NOW")
    after = int(time.time())
    assert code == 0
    assert before <= int(out.strip()) <= after


def test_no_args_returns_current_timestamp(capsys: pytest.CaptureFixture[str]) -> None:
    before = int(time.time())
    code, out, _ = _run(capsys, "date", "to-ts")
    after = int(time.time())
    assert code == 0
    ts = int(out.strip())
    assert before <= ts <= after


# ---------------------------------------------------------------------------
# 智能解析 (smart parsing)
# ---------------------------------------------------------------------------


def test_smart_parse_iso_with_T(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "to-ts", "--tz", "UTC", "2024-05-18T14:59:54")
    assert code == 0
    assert out.strip() == "1716044394"


def test_smart_parse_slash_datetime(capsys: pytest.CaptureFixture[str]) -> None:
    # fallback 格式 %Y/%m/%d %H:%M:%S
    code, out, _ = _run(capsys, "date", "to-ts", "--tz", "UTC", "2024/05/18 14:59:54")
    assert code == 0
    assert out.strip() == "1716044394"


def test_smart_parse_date_only(capsys: pytest.CaptureFixture[str]) -> None:
    # %Y-%m-%d 应视为 00:00:00
    code, out, _ = _run(capsys, "date", "to-ts", "--tz", "UTC", "1970-01-01")
    assert code == 0
    assert out.strip() == "0"


def test_smart_parse_slash_date_only(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "to-ts", "--tz", "UTC", "1970/01/01")
    assert code == 0
    assert out.strip() == "0"


# ---------------------------------------------------------------------------
# 显式格式 -f
# ---------------------------------------------------------------------------


def test_explicit_format(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(
        capsys, "date", "to-ts", "--tz", "UTC", "-f", "%d/%m/%Y %H:%M:%S", "18/05/2024 14:59:54"
    )
    assert code == 0
    assert out.strip() == "1716044394"


def test_explicit_format_mismatch_returns_error(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, "date", "to-ts", "-f", "%Y-%m-%d", "not-a-date")
    assert code == 1
    assert out == ""
    assert "错误" in err
    assert "-f" in err or "格式" in err


# ---------------------------------------------------------------------------
# 异常处理
# ---------------------------------------------------------------------------


def test_unrecognized_format_returns_error(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, "date", "to-ts", "not-a-date")
    assert code == 1
    assert out == ""
    assert "错误" in err
    assert "-f" in err or "自动识别" in err


# ---------------------------------------------------------------------------
# round-trip 与 from-ts 的互逆验证
# ---------------------------------------------------------------------------


def test_round_trip_to_ts_then_from_ts(capsys: pytest.CaptureFixture[str]) -> None:
    """to-ts → from-ts 应还原原始日期时间字符串。"""
    code, out, _ = _run(capsys, "date", "to-ts", "--tz", "UTC", "2024-05-18T14:59:54")
    assert code == 0
    ts = out.strip()

    code, out, _ = _run(capsys, "date", "from-ts", "--tz", "UTC", ts)
    assert code == 0
    assert out.strip() == "2024-05-18 14:59:54"


def test_round_trip_ms_unit(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = _run(capsys, "date", "to-ts", "-u", "ms", "--tz", "UTC", "2024-05-18T14:59:54")
    assert code == 0
    ts_ms = out.strip()

    code, out, _ = _run(capsys, "date", "from-ts", "-u", "ms", "--tz", "UTC", ts_ms)
    assert code == 0
    assert out.strip() == "2024-05-18 14:59:54"


# ---------------------------------------------------------------------------
# 边界值
# ---------------------------------------------------------------------------


def test_negative_epoch(capsys: pytest.CaptureFixture[str]) -> None:
    # 1969-12-31 23:59:59 UTC == -1
    code, out, _ = _run(capsys, "date", "to-ts", "--tz", "UTC", "1969-12-31T23:59:59")
    assert code == 0
    assert out.strip() == "-1"


def test_invalid_unit_choice_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["date", "to-ts", "-u", "ns", "2024-05-18"])
    assert exc.value.code == 2
