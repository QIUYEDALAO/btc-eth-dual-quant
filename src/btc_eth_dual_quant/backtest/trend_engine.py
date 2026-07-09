"""Offline long-only spot trend backtest engine for M1A validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from . import metrics
from .indicators import atr, donchian_high, donchian_low, realized_volatility, sma
from .metrics import Trade
from .skeleton import LookaheadBiasError, schedule_next_open
from .trend_strategy import FundingRecord, TrendBar, TrendParams, funding_crowding_by_bar, validate_bars


@dataclass(frozen=True)
class BacktestResult:
    symbol: str
    params: TrendParams
    cost_multiplier: float
    equity_curve: list[float]
    position_curve: list[float]
    trades: list[Trade]
    metrics: dict[str, float]
    signals_count: int
    crowding_filter_unavailable: bool = False
    ignored_final_signals: int = 0


@dataclass(frozen=True)
class PortfolioResult:
    name: str
    components: dict[str, BacktestResult]
    equity_curve: list[float]
    trades: list[Trade]
    metrics: dict[str, float]


@dataclass(frozen=True)
class Fill:
    action: str
    bar_index: int
    decision_index: int
    reason: str
    stop_price: float | None = None
    size_multiplier: float = 1.0
    atr_value: float | None = None
    realized_volatility: float | None = None


def position_size(
    equity: float,
    cash: float,
    price: float,
    atr_value: float,
    realized_vol: float | None,
    params: TrendParams,
    size_multiplier: float = 1.0,
    one_way_cost: float = 0.0015,
) -> float:
    if equity <= 0 or cash <= 0 or price <= 0 or atr_value <= 0:
        return 0.0
    stop_distance = params.atr_stop_mult * atr_value
    risk_qty = (equity * params.risk_per_trade) / stop_distance
    if realized_vol is not None and realized_vol > 0:
        vol_qty = (equity * params.max_annual_vol_contribution) / (realized_vol * price)
    else:
        vol_qty = risk_qty
    cash_qty = cash / (price * (1.0 + one_way_cost))
    return max(0.0, min(risk_qty, vol_qty, cash_qty) * size_multiplier)


def _build_fills(
    bars: list[TrendBar],
    funding: list[FundingRecord],
    params: TrendParams,
) -> tuple[dict[int, list[Fill]], bool, int]:
    closes = [bar.close for bar in bars]
    highs = [bar.high for bar in bars]
    lows = [bar.low for bar in bars]
    ma = sma(closes, params.regime_ma)
    entry_high = donchian_high(highs, params.entry_channel)
    exit_low = donchian_low(lows, params.exit_channel)
    atr_values = atr(highs, lows, closes, params.atr_period)
    vol_values = realized_volatility(closes, params.atr_period)
    crowded_days, funding_missing = funding_crowding_by_bar(bars, funding, params)
    market_bars = [bar.market_bar() for bar in bars]

    fills: dict[int, list[Fill]] = {}
    in_position = False
    stop_price: float | None = None
    ignored_final = 0
    for idx, bar in enumerate(bars):
        if ma[idx] is None or entry_high[idx] is None or exit_low[idx] is None or atr_values[idx] is None:
            continue
        action: str | None = None
        reason = ""
        next_stop = stop_price
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
            ignored_final += 1
            continue
        scheduled = schedule_next_open(market_bars, idx, reason)
        fill_idx = idx + 1
        if bars[fill_idx].open_time_ms != scheduled.earliest_effective_time_ms:
            raise LookaheadBiasError("fill must occur at next bar open")
        size_multiplier = 0.5 if action == "enter_long" and crowded_days.get(bar.open_time_ms, False) else 1.0
        if funding_missing and action == "enter_long":
            reason = f"{reason};crowding_filter_unavailable"
        fills.setdefault(fill_idx, []).append(
            Fill(
                action=action,
                bar_index=fill_idx,
                decision_index=idx,
                reason=reason,
                stop_price=next_stop,
                size_multiplier=size_multiplier,
                atr_value=atr_values[idx],
                realized_volatility=vol_values[idx],
            )
        )
        if action == "enter_long":
            in_position = True
            stop_price = next_stop
        else:
            in_position = False
            stop_price = None
    return fills, funding_missing, ignored_final


def run_trend_backtest(
    symbol: str,
    bars: list[TrendBar],
    funding: list[FundingRecord] | None = None,
    params: TrendParams | None = None,
    initial_equity: float = 10_000.0,
    spot_fee: float = 0.001,
    slippage: float = 0.0005,
    cost_multiplier: float = 1.0,
) -> BacktestResult:
    params = params or TrendParams()
    if not bars:
        raise ValueError("bars are required")
    validate_bars(bars)
    one_way_cost = (spot_fee + slippage) * cost_multiplier
    fills, funding_missing, ignored_final = _build_fills(bars, funding or [], params)

    cash = initial_equity
    quantity = 0.0
    entry_price = 0.0
    entry_time_ms = 0
    entry_index = 0
    equity_curve: list[float] = []
    position_curve: list[float] = []
    trades: list[Trade] = []
    for idx, bar in enumerate(bars):
        for fill in fills.get(idx, []):
            fill_price = bar.open
            if fill.action == "enter_long" and quantity == 0:
                equity = cash
                qty = position_size(
                    equity,
                    cash,
                    fill_price,
                    fill.atr_value or 0.0,
                    fill.realized_volatility,
                    params,
                    fill.size_multiplier,
                    one_way_cost,
                )
                cost = qty * fill_price * one_way_cost
                notional = qty * fill_price
                if notional + cost > cash + 1e-9:
                    qty = cash / (fill_price * (1.0 + one_way_cost))
                    cost = qty * fill_price * one_way_cost
                    notional = qty * fill_price
                cash -= notional + cost
                quantity = qty
                entry_price = fill_price * (1.0 + one_way_cost)
                entry_time_ms = bar.open_time_ms
                entry_index = idx
            elif fill.action == "exit_long" and quantity > 0:
                gross = quantity * fill_price
                cost = gross * one_way_cost
                cash += gross - cost
                exit_price = fill_price * (1.0 - one_way_cost)
                pnl = (exit_price - entry_price) * quantity
                trades.append(
                    Trade(
                        symbol=symbol,
                        entry_time_ms=entry_time_ms,
                        exit_time_ms=bar.open_time_ms,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        quantity=quantity,
                        pnl=pnl,
                        return_pct=exit_price / entry_price - 1.0 if entry_price else 0.0,
                        bars_held=idx - entry_index,
                    )
                )
                quantity = 0.0
                entry_price = 0.0
        equity_curve.append(cash + quantity * bar.close)
        position_curve.append(quantity)

    days = max(1, len(bars))
    return BacktestResult(
        symbol=symbol,
        params=params,
        cost_multiplier=cost_multiplier,
        equity_curve=equity_curve,
        position_curve=position_curve,
        trades=trades,
        metrics=metrics.metrics_summary(equity_curve, trades, days, position_curve),
        signals_count=sum(len(items) for items in fills.values()),
        crowding_filter_unavailable=funding_missing,
        ignored_final_signals=ignored_final,
    )


def combine_equal_weight(results: dict[str, BacktestResult], name: str = "BTC+ETH equal-weight portfolio") -> PortfolioResult:
    if not results:
        raise ValueError("results are required")
    min_len = min(len(result.equity_curve) for result in results.values())
    equity_curve = [
        sum(result.equity_curve[idx] for result in results.values()) / len(results)
        for idx in range(min_len)
    ]
    positions = [
        sum(1.0 for result in results.values() if result.position_curve[idx] > 0)
        for idx in range(min_len)
    ]
    trades: list[Trade] = []
    for result in results.values():
        trades.extend(result.trades)
    return PortfolioResult(
        name=name,
        components=results,
        equity_curve=equity_curve,
        trades=trades,
        metrics=metrics.metrics_summary(equity_curve, trades, max(1, min_len), positions),
    )


T = TypeVar("T")


def split_in_sample_oos(items: list[T], oos_fraction: float = 0.30) -> tuple[list[T], list[T]]:
    if not 0 < oos_fraction < 1:
        raise ValueError("oos_fraction must be between 0 and 1")
    if len(items) < 2:
        return items, []
    split_at = int(len(items) * (1.0 - oos_fraction))
    split_at = max(1, min(split_at, len(items) - 1))
    return items[:split_at], items[split_at:]


def parameter_neighborhood(center: TrendParams | None = None) -> list[TrendParams]:
    center = center or TrendParams()
    params: list[TrendParams] = []
    for regime_ma in (160, 200, 240):
        for entry_channel in (44, 55, 66):
            for exit_channel in (16, 20, 24):
                for atr_stop_mult in (1.6, 2.0, 2.4):
                    params.append(
                        TrendParams(
                            regime_ma=regime_ma,
                            entry_channel=entry_channel,
                            exit_channel=exit_channel,
                            atr_period=center.atr_period,
                            atr_stop_mult=atr_stop_mult,
                            risk_per_trade=center.risk_per_trade,
                            max_annual_vol_contribution=center.max_annual_vol_contribution,
                            funding_crowding_threshold=center.funding_crowding_threshold,
                            funding_crowding_days=center.funding_crowding_days,
                        )
                    )
    return params


def remove_best_trades_effect(result: BacktestResult, count: int = 3) -> dict[str, float]:
    removed_pnl = sum(trade.pnl for trade in sorted(result.trades, key=lambda trade: trade.pnl, reverse=True)[:count])
    if result.equity_curve:
        adjusted_curve = [result.equity_curve[0]]
        adjusted_curve.extend(max(0.01, value - removed_pnl) for value in result.equity_curve[1:])
    else:
        adjusted_curve = []
    adjusted_trades = sorted(result.trades, key=lambda trade: trade.pnl, reverse=True)[count:]
    positions = getattr(result, "position_curve", [1.0 if adjusted_trades else 0.0 for _ in adjusted_curve])
    summary = metrics.metrics_summary(adjusted_curve, adjusted_trades, max(1, len(adjusted_curve)), positions)
    summary["breakeven_or_better"] = 1.0 if summary["total_return"] >= 0 else 0.0
    return summary


@dataclass(frozen=True)
class Segment:
    name: str
    start_ms: int
    end_ms: int
    note: str = ""


def segment_result(result: BacktestResult, bars: list[TrendBar], segment: Segment) -> dict[str, float | str]:
    indexes = [idx for idx, bar in enumerate(bars) if segment.start_ms <= bar.open_time_ms <= segment.end_ms]
    if len(indexes) < 2:
        return {"return": 0.0, "max_drawdown": 0.0, "trade_count": 0.0, "exposure_days": 0.0, "note": segment.note}
    start = indexes[0]
    end = indexes[-1]
    curve = result.equity_curve[start : end + 1]
    segment_trades = [
        trade for trade in result.trades if bars[start].open_time_ms <= trade.entry_time_ms <= bars[end].open_time_ms
    ]
    positions = result.position_curve[start : end + 1]
    return {
        "return": metrics.total_return(curve),
        "max_drawdown": metrics.max_drawdown(curve),
        "trade_count": float(len(segment_trades)),
        "exposure_days": float(metrics.exposure_days(positions)),
        "note": segment.note,
    }
