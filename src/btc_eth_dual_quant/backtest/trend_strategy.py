"""M1A fixed-parameter trend-following signal generation.

Signals are generated after a daily UTC bar close and may become effective no
earlier than the next bar open. This module does not place orders and does not
model paper/live execution.
"""

from __future__ import annotations

from dataclasses import dataclass

from .indicators import atr, donchian_high, donchian_low, realized_volatility, sma
from .skeleton import LookaheadBiasError, MarketBar, assert_feature_available, schedule_next_open


@dataclass(frozen=True)
class TrendParams:
    regime_ma: int = 200
    entry_channel: int = 55
    exit_channel: int = 20
    atr_period: int = 20
    atr_stop_mult: float = 2.0
    risk_per_trade: float = 0.01
    max_annual_vol_contribution: float = 0.20
    funding_crowding_threshold: float = 0.40
    funding_crowding_days: int = 3


@dataclass(frozen=True)
class TrendBar:
    symbol: str
    open_time_ms: int
    close_time_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def market_bar(self) -> MarketBar:
        return MarketBar(
            open_time_ms=self.open_time_ms,
            close_time_ms=self.close_time_ms,
            open=str(self.open),
            high=str(self.high),
            low=str(self.low),
            close=str(self.close),
        )


@dataclass(frozen=True)
class FundingRecord:
    symbol: str
    funding_time_ms: int
    funding_rate: float
    annualized_rate: float
    interval_hours: float | None = None


@dataclass(frozen=True)
class TrendSignal:
    symbol: str
    action: str
    decision_bar_index: int
    decision_time_ms: int
    earliest_fill_time_ms: int | None
    reason: str
    size_multiplier: float = 1.0
    ignored_reason: str | None = None
    atr_value: float | None = None
    realized_volatility: float | None = None
    stop_price: float | None = None


def validate_bars(bars: list[TrendBar]) -> None:
    previous_open: int | None = None
    one_day_ms = 86_400_000
    for bar in bars:
        if bar.high < max(bar.open, bar.close, bar.low):
            raise ValueError(f"invalid OHLC high ordering for {bar.symbol} at {bar.open_time_ms}")
        if bar.low > min(bar.open, bar.close, bar.high):
            raise ValueError(f"invalid OHLC low ordering for {bar.symbol} at {bar.open_time_ms}")
        if previous_open is not None and bar.open_time_ms - previous_open != one_day_ms:
            raise ValueError(f"non-continuous 1d bars for {bar.symbol} at {bar.open_time_ms}")
        previous_open = bar.open_time_ms


def funding_crowding_by_bar(
    bars: list[TrendBar],
    funding: list[FundingRecord],
    params: TrendParams,
) -> tuple[dict[int, bool], bool]:
    if not funding:
        return {}, True
    one_day_ms = 86_400_000
    max_rate_by_day: dict[int, float] = {}
    for item in funding:
        day_start = (item.funding_time_ms // one_day_ms) * one_day_ms
        max_rate_by_day[day_start] = max(max_rate_by_day.get(day_start, float("-inf")), item.annualized_rate)

    by_day: dict[int, bool] = {}
    threshold = params.funding_crowding_threshold
    for bar in bars:
        day_start = (bar.open_time_ms // one_day_ms) * one_day_ms
        by_day[bar.open_time_ms] = max_rate_by_day.get(day_start, float("-inf")) > threshold

    crowded: dict[int, bool] = {}
    streak = 0
    for bar in bars:
        if by_day.get(bar.open_time_ms, False):
            streak += 1
        else:
            streak = 0
        crowded[bar.open_time_ms] = streak >= params.funding_crowding_days
    return crowded, False


def _ignored_final_signal(symbol: str, idx: int, bar: TrendBar, reason: str) -> TrendSignal:
    return TrendSignal(
        symbol=symbol,
        action="ignore",
        decision_bar_index=idx,
        decision_time_ms=bar.close_time_ms,
        earliest_fill_time_ms=None,
        reason=reason,
        ignored_reason="final_bar_no_next_open",
    )


def generate_trend_signals(
    bars: list[TrendBar],
    funding: list[FundingRecord] | None = None,
    params: TrendParams | None = None,
) -> list[TrendSignal]:
    params = params or TrendParams()
    if not bars:
        return []
    validate_bars(bars)
    symbol = bars[0].symbol
    market_bars = [bar.market_bar() for bar in bars]
    closes = [bar.close for bar in bars]
    highs = [bar.high for bar in bars]
    lows = [bar.low for bar in bars]
    ma = sma(closes, params.regime_ma)
    entry_high = donchian_high(highs, params.entry_channel)
    exit_low = donchian_low(lows, params.exit_channel)
    atr_values = atr(highs, lows, closes, params.atr_period)
    vol_values = realized_volatility(closes, params.atr_period)
    crowded_days, funding_missing = funding_crowding_by_bar(bars, funding or [], params)

    in_position = False
    stop_price: float | None = None
    signals: list[TrendSignal] = []
    for idx, bar in enumerate(bars):
        assert_feature_available(bar.close_time_ms, bar.close_time_ms)
        if ma[idx] is None or entry_high[idx] is None or exit_low[idx] is None or atr_values[idx] is None:
            continue
        action: str | None = None
        reason = ""
        next_stop: float | None = stop_price
        if not in_position and bar.close > entry_high[idx] and bar.close > ma[idx]:
            action = "enter_long"
            reason = "donchian_breakout_with_trend_filter"
            next_stop = bar.close - params.atr_stop_mult * atr_values[idx]
        elif in_position and (bar.close < exit_low[idx] or (stop_price is not None and bar.close < stop_price)):
            action = "exit_long"
            reason = "exit_channel_or_atr_stop"

        if action is None:
            continue
        if idx == len(bars) - 1:
            signals.append(_ignored_final_signal(symbol, idx, bar, reason))
            continue
        scheduled = schedule_next_open(market_bars, idx, reason)
        size_multiplier = 0.5 if action == "enter_long" and crowded_days.get(bar.open_time_ms, False) else 1.0
        if funding_missing and action == "enter_long":
            reason = f"{reason};crowding_filter_unavailable"
        signals.append(
            TrendSignal(
                symbol=symbol,
                action=action,
                decision_bar_index=idx,
                decision_time_ms=scheduled.decision_time_ms,
                earliest_fill_time_ms=scheduled.earliest_effective_time_ms,
                reason=reason,
                size_multiplier=size_multiplier,
                atr_value=atr_values[idx],
                realized_volatility=vol_values[idx],
                stop_price=next_stop,
            )
        )
        if action == "enter_long":
            in_position = True
            stop_price = next_stop
        elif action == "exit_long":
            in_position = False
            stop_price = None
    return signals


def assert_no_same_bar_fill(signal: TrendSignal, bars: list[TrendBar]) -> None:
    if signal.earliest_fill_time_ms is None:
        return
    decision_bar = bars[signal.decision_bar_index]
    if signal.earliest_fill_time_ms <= decision_bar.close_time_ms:
        raise LookaheadBiasError("same-bar close fill is not allowed")
