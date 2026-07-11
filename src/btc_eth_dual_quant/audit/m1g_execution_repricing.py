"""Conservative repricing of Freqtrade-exported M1G trades.

This module cannot detect events or select trades. It only verifies and
reprices an already exported lifecycle against canonical 5m bars.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Mapping


TARGET_RETURN = 0.018
STOP_RETURN = -0.04
TIMEOUT = timedelta(hours=24)
COSTS_PER_SIDE = {
    "base": 0.0015,
    "cost_x2": 0.0030,
    "stress_a": 0.0040,
    "stress_b": 0.0055,
}


def validate_entry_timing(event_bar_open: datetime, entry_time: datetime) -> list[str]:
    event_open = _utc(event_bar_open)
    actual_entry = _utc(entry_time)
    earliest = event_open + timedelta(hours=1)
    failures: list[str] = []
    if actual_entry < earliest:
        failures.append("entry must be the first available 5m open after the completed 1h event")
    if actual_entry.minute % 5 or actual_entry.second or actual_entry.microsecond:
        failures.append("entry time must align to a 5m open")
    return failures


@dataclass(frozen=True)
class DetailBar:
    open_time: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class ExportedTrade:
    pair: str
    open_time: datetime
    close_time: datetime
    open_rate: float
    close_rate: float
    stake_amount: float


@dataclass(frozen=True)
class RepricedTrade:
    pair: str
    open_time: datetime
    native_close_time: datetime
    audited_close_time: datetime
    open_rate: float
    native_close_rate: float
    audited_close_rate: float
    audited_exit_reason: str
    native_exit_bar_matches: bool
    net_returns: tuple[tuple[str, float], ...]
    canonical_sha256: str


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def trade_from_export(payload: Mapping[str, object]) -> ExportedTrade:
    forbidden = {"signal", "event", "candidate", "parameter"} & set(payload)
    if forbidden:
        raise ValueError("execution audit input must not contain signal-selection fields")

    def timestamp(name: str) -> datetime:
        return _utc(datetime.fromisoformat(str(payload[name]).replace("Z", "+00:00")))

    return ExportedTrade(
        pair=str(payload["pair"]),
        open_time=timestamp("open_date"),
        close_time=timestamp("close_date"),
        open_rate=float(payload["open_rate"]),
        close_rate=float(payload["close_rate"]),
        stake_amount=float(payload["stake_amount"]),
    )


def _validated_bars(bars: Iterable[DetailBar]) -> list[DetailBar]:
    ordered = list(bars)
    if not ordered:
        raise ValueError("canonical 5m bars are required")
    normalized = [DetailBar(_utc(bar.open_time), bar.open, bar.high, bar.low, bar.close) for bar in ordered]
    for bar in normalized:
        if min(bar.open, bar.high, bar.low, bar.close) <= 0 or not (
            bar.low <= bar.open <= bar.high and bar.low <= bar.close <= bar.high
        ):
            raise ValueError("invalid canonical 5m OHLC")
    for previous, current in zip(normalized, normalized[1:]):
        if current.open_time - previous.open_time != timedelta(minutes=5):
            raise ValueError("canonical 5m bars must be unique, ordered, and continuous")
    return normalized


def reprice_exported_trade(trade: ExportedTrade, bars: Iterable[DetailBar]) -> RepricedTrade:
    if trade.pair not in {"BTC/USDT", "ETH/USDT"}:
        raise ValueError("unsupported M1G pair")
    if trade.open_rate <= 0 or trade.stake_amount <= 0 or trade.close_time < trade.open_time:
        raise ValueError("invalid exported lifecycle")
    detail = _validated_bars(bars)
    if detail[0].open_time != _utc(trade.open_time):
        raise ValueError("first detail bar must be the exported entry bar")

    target = trade.open_rate * (1.0 + TARGET_RETURN)
    stop = trade.open_rate * (1.0 + STOP_RETURN)
    timeout = _utc(trade.open_time) + TIMEOUT
    exit_time = None
    exit_rate = None
    exit_reason = None
    for bar in detail:
        stop_touched = bar.low <= stop
        target_touched = bar.high >= target
        if stop_touched:
            exit_time, exit_rate, exit_reason = bar.open_time, min(bar.open, stop), "stop"
            break
        if target_touched:
            exit_time, exit_rate, exit_reason = bar.open_time, target, "target"
            break
        if bar.open_time >= timeout:
            exit_time, exit_rate, exit_reason = bar.open_time, bar.open, "timeout"
            break
    if exit_time is None or exit_rate is None or exit_reason is None:
        raise ValueError("canonical detail does not contain a complete audited exit")

    returns = tuple(
        (name, (exit_rate * (1.0 - cost)) / (trade.open_rate * (1.0 + cost)) - 1.0)
        for name, cost in COSTS_PER_SIDE.items()
    )
    canonical = {
        "pair": trade.pair,
        "open_time": _utc(trade.open_time).isoformat(),
        "native_close_time": _utc(trade.close_time).isoformat(),
        "audited_close_time": exit_time.isoformat(),
        "open_rate": trade.open_rate,
        "native_close_rate": trade.close_rate,
        "audited_close_rate": exit_rate,
        "audited_exit_reason": exit_reason,
        "net_returns": returns,
    }
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return RepricedTrade(
        pair=trade.pair,
        open_time=_utc(trade.open_time),
        native_close_time=_utc(trade.close_time),
        audited_close_time=exit_time,
        open_rate=trade.open_rate,
        native_close_rate=trade.close_rate,
        audited_close_rate=exit_rate,
        audited_exit_reason=exit_reason,
        native_exit_bar_matches=_utc(trade.close_time) == exit_time,
        net_returns=returns,
        canonical_sha256=digest,
    )


def canonical_payload(result: RepricedTrade) -> dict:
    payload = asdict(result)
    for name in ("open_time", "native_close_time", "audited_close_time"):
        payload[name] = payload[name].isoformat()
    return payload
