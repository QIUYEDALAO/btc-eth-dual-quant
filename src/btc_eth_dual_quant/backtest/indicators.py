"""Offline indicators for M1A trend backtest validation.

All rolling calculations use only observations at or before each output index.
Donchian helpers intentionally exclude the current bar so a bar cannot trigger
itself with its own high or low.
"""

from __future__ import annotations

import math
from statistics import pstdev


def sma(values: list[float], period: int) -> list[float | None]:
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[float | None] = []
    running = 0.0
    for idx, value in enumerate(values):
        running += value
        if idx >= period:
            running -= values[idx - period]
        out.append(running / period if idx + 1 >= period else None)
    return out


def donchian_high(highs: list[float], period: int) -> list[float | None]:
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[float | None] = []
    for idx in range(len(highs)):
        if idx < period:
            out.append(None)
        else:
            out.append(max(highs[idx - period : idx]))
    return out


def donchian_low(lows: list[float], period: int) -> list[float | None]:
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[float | None] = []
    for idx in range(len(lows)):
        if idx < period:
            out.append(None)
        else:
            out.append(min(lows[idx - period : idx]))
    return out


def true_range(highs: list[float], lows: list[float], closes: list[float]) -> list[float]:
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("highs, lows, and closes must have identical lengths")
    out: list[float] = []
    for idx, high in enumerate(highs):
        low = lows[idx]
        if idx == 0:
            out.append(high - low)
        else:
            previous_close = closes[idx - 1]
            out.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
    return out


def atr(highs: list[float], lows: list[float], closes: list[float], period: int) -> list[float | None]:
    ranges = true_range(highs, lows, closes)
    return sma(ranges, period)


def realized_volatility(closes: list[float], period: int, annualization_days: int = 365) -> list[float | None]:
    if period <= 1:
        raise ValueError("period must be greater than 1")
    out: list[float | None] = []
    returns: list[float] = []
    for idx, close in enumerate(closes):
        if idx == 0:
            out.append(None)
            continue
        previous = closes[idx - 1]
        if previous <= 0:
            returns.append(0.0)
        else:
            returns.append(math.log(close / previous))
        if len(returns) < period:
            out.append(None)
        else:
            window = returns[-period:]
            out.append(pstdev(window) * math.sqrt(annualization_days))
    return out
