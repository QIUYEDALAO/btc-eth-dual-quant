"""Independent M1C event-time checks; this module does not calculate returns."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class RotationEvent:
    signal_candle_open: datetime
    signal_candle_close: datetime
    btc_score_time: datetime
    eth_score_time: datetime
    effective_fill_time: datetime


def validate_rotation_event(event: RotationEvent) -> list[str]:
    failures: list[str] = []
    timestamps = (
        event.signal_candle_open,
        event.signal_candle_close,
        event.btc_score_time,
        event.eth_score_time,
        event.effective_fill_time,
    )
    if any(value.tzinfo is None or value.utcoffset() is None for value in timestamps):
        failures.append("all timestamps must be timezone-aware UTC values")
        return failures
    if any(value.utcoffset() != timedelta(0) for value in timestamps):
        failures.append("all timestamps must use UTC")
    if event.signal_candle_open.weekday() != 6:
        failures.append("decision candle must open on Sunday UTC")
    if event.signal_candle_close != event.signal_candle_open + timedelta(days=1):
        failures.append("signal candle must be a complete 1d candle")
    if event.btc_score_time != event.eth_score_time:
        failures.append("BTC and ETH scores must use the same UTC timestamp")
    if event.btc_score_time != event.signal_candle_close:
        failures.append("score timestamp must equal the completed signal close")
    if event.effective_fill_time != event.signal_candle_close:
        failures.append("signal may become effective only at the next 1d open")
    return failures


def validate_rotation_switch(old_exit_time: datetime, new_entry_time: datetime) -> list[str]:
    if old_exit_time != new_entry_time:
        return ["rotation exit and replacement entry must share the same next-open timestamp"]
    return []
