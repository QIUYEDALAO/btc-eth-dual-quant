"""Strict event-time M1B funding-arbitrage research accounting.

This module is an offline audit sidecar for a spot-long plus USDT-perpetual-
short portfolio. It consumes local M0 public data only. It is not an execution,
paper-trading, or exchange-access implementation.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from btc_eth_dual_quant.data.funding import infer_funding_interval_hours

from .trend_strategy import TrendBar


MS_PER_HOUR = 3_600_000
MS_PER_DAY = 86_400_000
HOURS_PER_YEAR = 365 * 24
HOURLY_CLOSE_TOLERANCE_MS = 1_000


@dataclass(frozen=True)
class FundingArbParams:
    expected_hold_days: float = 14.0
    min_payback_ratio: float = 2.0
    roundtrip_cost_base: float = 0.005
    entry_mean_apr_threshold: float = 0.08
    exit_mean_apr_threshold: float = 0.02
    spot_fee_per_side: float = 0.001
    futures_fee_per_side: float = 0.0005
    slippage_per_leg: float = 0.0005
    cost_multiplier: float = 1.0
    oos_fraction: float = 0.30
    notional: float = 1.0
    min_complete_cycles: int = 20
    min_oos_sharpe: float = 1.0
    max_drawdown_limit: float = 0.05


@dataclass(frozen=True)
class FundingPoint:
    symbol: str
    funding_time_ms: int
    funding_rate: float
    interval_hours: float
    annualized_rate: float


@dataclass(frozen=True)
class FundingContribution:
    funding_time_ms: int
    funding_rate: float
    interval_hours: float
    settlement_mark_price: float
    perpetual_quantity: float
    income: float
    valuation_bar_close_time_ms: int


@dataclass(frozen=True)
class TwoLegPnl:
    spot_pnl: float
    perp_short_pnl: float
    funding_income: float
    basis_pnl: float
    fees: float
    slippage: float
    net_pnl: float
    net_return: float
    entry_basis: float
    exit_basis: float
    entry_fees: float
    exit_fees: float
    entry_slippage: float
    exit_slippage: float


@dataclass(frozen=True)
class FundingArbCycle:
    symbol: str
    entry_signal_time_ms: int
    entry_time_ms: int
    exit_signal_time_ms: int
    exit_time_ms: int
    holding_days: float
    entry_spot_price: float
    entry_perp_price: float
    exit_spot_price: float
    exit_perp_price: float
    entry_basis: float
    exit_basis: float
    spot_pnl: float
    perp_short_pnl: float
    funding_income: float
    basis_pnl: float
    fees: float
    slippage: float
    net_pnl: float
    net_return: float
    max_drawdown_during_cycle: float
    exit_reason: str
    funding_periods_count: int
    negative_funding_periods_count: int
    funding_contributions: tuple[FundingContribution, ...] = ()
    basis_data_status: str = "available"


@dataclass(frozen=True)
class IncompletePosition:
    symbol: str
    entry_signal_time_ms: int
    entry_time_ms: int
    last_event_time_ms: int
    funding_periods_count: int
    reason: str


@dataclass(frozen=True)
class SleepPeriod:
    symbol: str
    start_time_ms: int
    end_time_ms: int
    days: float
    reason: str


@dataclass(frozen=True)
class FundingArbResult:
    symbol: str
    params: FundingArbParams
    cost_label: str
    cycles: list[FundingArbCycle]
    equity_times_ms: list[int]
    equity_curve: list[float]
    metrics: dict[str, float]
    oos_metrics: dict[str, float]
    gates: dict[str, str]
    final_status: str
    interval_hours: float
    interval_source: str
    interval_anomalies: list[str]
    sleep_periods: list[SleepPeriod]
    data_start_ms: int | None
    data_end_ms: int | None
    is_start_ms: int | None
    is_end_ms: int | None
    oos_start_ms: int | None
    oos_end_ms: int | None
    basis_data_status: str
    interval_distribution: dict[str, int] = field(default_factory=dict)
    incomplete_positions: list[IncompletePosition] = field(default_factory=list)
    oos_carry_in_cycles: list[FundingArbCycle] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    metrics_basis: str = "funding-event time-indexed equity curve"
    oos_split_basis: str = "time-based last 30%"
    no_lookahead: bool = True
    components: dict[str, "FundingArbResult"] = field(default_factory=dict)


def utc_ms(value: int | None) -> str:
    if value is None:
        return "n/a"
    return datetime.fromtimestamp(value / 1000, tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def annualize_funding_rate(period_rate: float, interval_hours: float) -> float:
    if interval_hours <= 0:
        raise ValueError("interval_hours must be positive")
    return period_rate * (HOURS_PER_YEAR / interval_hours)


def infer_interval_from_funding_history(records: list[dict[str, Any] | FundingPoint]) -> tuple[float, list[str]]:
    raw_records = [
        {
            "symbol": record.symbol,
            "fundingTime": record.funding_time_ms,
            "fundingRate": record.funding_rate,
        }
        if isinstance(record, FundingPoint)
        else record
        for record in records
    ]
    if not raw_records:
        raise ValueError("funding history is required")
    symbol = str(raw_records[0].get("symbol") or "UNKNOWN")
    inferred = infer_funding_interval_hours(symbol, funding_rate_history=raw_records)
    event_values = {float(value) for value in inferred.event_intervals.values()}
    warnings = list(inferred.warnings)
    if len(event_values) > 1:
        rendered = ", ".join(f"{value:g}" for value in sorted(event_values))
        warnings.append(f"variable funding intervals observed: {rendered} hours")
    return float(inferred.hours), warnings


def build_funding_points(symbol: str, funding_history: list[dict[str, Any]]) -> tuple[list[FundingPoint], float, list[str]]:
    valid_rows: dict[int, dict[str, Any]] = {}
    for row in funding_history:
        try:
            time_ms = int(row["fundingTime"])
            float(row["fundingRate"])
        except (KeyError, TypeError, ValueError):
            continue
        valid_rows.setdefault(time_ms, row)
    rows = [valid_rows[key] for key in sorted(valid_rows)]
    if len(rows) < 2:
        raise ValueError("at least two funding records are required")
    inferred = infer_funding_interval_hours(symbol, funding_rate_history=rows)
    modal_hours = float(inferred.hours)
    points: list[FundingPoint] = []
    for row in rows:
        time_ms = int(row["fundingTime"])
        interval = float(inferred.event_intervals.get(time_ms, inferred.hours))
        rate = float(row["fundingRate"])
        points.append(
            FundingPoint(
                symbol=symbol,
                funding_time_ms=time_ms,
                funding_rate=rate,
                interval_hours=interval,
                annualized_rate=annualize_funding_rate(rate, interval),
            )
        )
    warnings = list(inferred.warnings)
    distinct = sorted({point.interval_hours for point in points})
    if len(distinct) > 1:
        warnings.append("variable funding intervals observed: " + ", ".join(f"{item:g}h" for item in distinct))
    return points, modal_hours, warnings


def compute_payback_required_apr(params: FundingArbParams | None = None) -> float:
    params = params or FundingArbParams()
    return params.roundtrip_cost_base * params.min_payback_ratio * 365.0 / params.expected_hold_days


def should_enter_funding_arb(
    mean_annualized_3d: float,
    current_funding_rate: float,
    params: FundingArbParams | None = None,
) -> bool:
    params = params or FundingArbParams()
    return (
        current_funding_rate > 0
        and mean_annualized_3d >= params.entry_mean_apr_threshold
        and mean_annualized_3d >= compute_payback_required_apr(params)
    )


def should_exit_funding_arb(
    mean_annualized_3d: float,
    negative_funding_streak: int,
    params: FundingArbParams | None = None,
    low_funding_days: float = 3.0,
) -> str | None:
    params = params or FundingArbParams()
    if negative_funding_streak >= 2:
        return "negative_funding_streak"
    if mean_annualized_3d < params.exit_mean_apr_threshold and low_funding_days >= 3.0:
        return "low_funding_mean"
    return None


def compute_two_leg_pnl(
    entry_spot_price: float,
    exit_spot_price: float,
    entry_perp_price: float,
    exit_perp_price: float,
    funding_rates: list[float],
    params: FundingArbParams | None = None,
    funding_mark_prices: list[float] | None = None,
    perpetual_quantity: float | None = None,
) -> TwoLegPnl:
    params = params or FundingArbParams()
    if min(entry_spot_price, exit_spot_price, entry_perp_price, exit_perp_price) <= 0:
        raise ValueError("prices must be positive")
    if funding_mark_prices is not None and len(funding_mark_prices) != len(funding_rates):
        raise ValueError("funding rates and mark prices must have the same length")
    spot_qty = params.notional / entry_spot_price
    perp_qty = perpetual_quantity if perpetual_quantity is not None else params.notional / entry_perp_price
    spot_pnl = (exit_spot_price - entry_spot_price) * spot_qty
    perp_short_pnl = (entry_perp_price - exit_perp_price) * perp_qty
    marks = funding_mark_prices or [entry_perp_price] * len(funding_rates)
    funding_income = sum(rate * mark * perp_qty for rate, mark in zip(funding_rates, marks))
    basis_pnl = spot_pnl + perp_short_pnl

    entry_spot_notional = entry_spot_price * spot_qty
    exit_spot_notional = exit_spot_price * spot_qty
    entry_perp_notional = entry_perp_price * perp_qty
    exit_perp_notional = exit_perp_price * perp_qty
    multiplier = params.cost_multiplier
    entry_fees = (
        entry_spot_notional * params.spot_fee_per_side
        + entry_perp_notional * params.futures_fee_per_side
    ) * multiplier
    exit_fees = (
        exit_spot_notional * params.spot_fee_per_side
        + exit_perp_notional * params.futures_fee_per_side
    ) * multiplier
    entry_slippage = (
        entry_spot_notional + entry_perp_notional
    ) * params.slippage_per_leg * multiplier
    exit_slippage = (
        exit_spot_notional + exit_perp_notional
    ) * params.slippage_per_leg * multiplier
    fees = entry_fees + exit_fees
    slippage = entry_slippage + exit_slippage
    net_pnl = basis_pnl + funding_income - fees - slippage
    return TwoLegPnl(
        spot_pnl=spot_pnl,
        perp_short_pnl=perp_short_pnl,
        funding_income=funding_income,
        basis_pnl=basis_pnl,
        fees=fees,
        slippage=slippage,
        net_pnl=net_pnl,
        net_return=net_pnl / params.notional,
        entry_basis=entry_perp_price - entry_spot_price,
        exit_basis=exit_perp_price - exit_spot_price,
        entry_fees=entry_fees,
        exit_fees=exit_fees,
        entry_slippage=entry_slippage,
        exit_slippage=exit_slippage,
    )


def _validate_hourly_bars(name: str, bars: list[TrendBar]) -> None:
    if not bars:
        raise ValueError(f"{name} bars are required")
    for bar in bars:
        duration = bar.close_time_ms - bar.open_time_ms
        if abs(duration - (MS_PER_HOUR - 1)) > HOURLY_CLOSE_TOLERANCE_MS:
            raise ValueError(f"{name} must use completed 1h bars")


def _completed_bar_at_or_before(bars: list[TrendBar], valuation_time_ms: int) -> TrendBar | None:
    left = 0
    right = len(bars)
    while left < right:
        middle = (left + right) // 2
        if bars[middle].close_time_ms <= valuation_time_ms:
            left = middle + 1
        else:
            right = middle
    return bars[left - 1] if left else None


def _first_common_bar_open_after(
    spot_bars: list[TrendBar],
    perp_bars: list[TrendBar],
    signal_time_ms: int,
) -> tuple[TrendBar, TrendBar] | None:
    spot_by_open = {bar.open_time_ms: bar for bar in spot_bars if bar.open_time_ms > signal_time_ms}
    perp_by_open = {bar.open_time_ms: bar for bar in perp_bars if bar.open_time_ms > signal_time_ms}
    common = sorted(set(spot_by_open).intersection(perp_by_open))
    if not common:
        return None
    timestamp = common[0]
    return spot_by_open[timestamp], perp_by_open[timestamp]


def _rolling_mean_annualized(points: list[FundingPoint], idx: int, window_ms: int = 3 * MS_PER_DAY) -> float:
    current_time = points[idx].funding_time_ms
    values = [
        point.annualized_rate
        for point in points[: idx + 1]
        if current_time - window_ms < point.funding_time_ms <= current_time
    ]
    return sum(values) / len(values) if values else 0.0


def _market_diagnostics(
    points: list[FundingPoint],
    mark_bars: list[TrendBar],
    index_bars: list[TrendBar],
    premium_bars: list[TrendBar],
) -> tuple[str, dict[str, Any]]:
    missing_mark = 0
    missing_index = 0
    missing_premium = 0
    spreads: list[float] = []
    premium_errors: list[float] = []
    for point in points:
        mark = _completed_bar_at_or_before(mark_bars, point.funding_time_ms)
        index = _completed_bar_at_or_before(index_bars, point.funding_time_ms)
        premium = _completed_bar_at_or_before(premium_bars, point.funding_time_ms)
        missing_mark += mark is None
        missing_index += index is None
        missing_premium += premium is None
        if mark is not None and index is not None and index.close != 0:
            spread = (mark.close - index.close) / index.close
            spreads.append(spread)
            if premium is not None:
                premium_errors.append(abs(spread - premium.close))
    complete = not (missing_mark or missing_index or missing_premium)
    diagnostics: dict[str, Any] = {
        "funding_events": len(points),
        "missing_mark_events": missing_mark,
        "missing_index_events": missing_index,
        "missing_premium_events": missing_premium,
        "mean_mark_index_spread": sum(spreads) / len(spreads) if spreads else 0.0,
        "max_abs_mark_index_spread": max((abs(value) for value in spreads), default=0.0),
        "mean_abs_premium_consistency_error": sum(premium_errors) / len(premium_errors) if premium_errors else 0.0,
    }
    return ("available" if complete else "partial"), diagnostics


def _funding_contribution(
    point: FundingPoint,
    mark_bars: list[TrendBar],
    perp_qty: float,
) -> FundingContribution | None:
    mark = _completed_bar_at_or_before(mark_bars, point.funding_time_ms)
    if mark is None:
        return None
    return FundingContribution(
        funding_time_ms=point.funding_time_ms,
        funding_rate=point.funding_rate,
        interval_hours=point.interval_hours,
        settlement_mark_price=mark.close,
        perpetual_quantity=perp_qty,
        income=mark.close * perp_qty * point.funding_rate,
        valuation_bar_close_time_ms=mark.close_time_ms,
    )


def _cycle_drawdown(
    cycle: FundingArbCycle,
    spot_bars: list[TrendBar],
    perp_bars: list[TrendBar],
    params: FundingArbParams,
) -> float:
    spot_qty = params.notional / cycle.entry_spot_price
    perp_qty = spot_qty
    peak = params.notional
    worst = 0.0
    entry_cost = (cycle.fees + cycle.slippage) / 2.0
    for contribution in cycle.funding_contributions:
        spot = _completed_bar_at_or_before(spot_bars, contribution.funding_time_ms)
        perp = _completed_bar_at_or_before(perp_bars, contribution.funding_time_ms)
        if spot is None or perp is None:
            continue
        funding = sum(
            item.income
            for item in cycle.funding_contributions
            if item.funding_time_ms <= contribution.funding_time_ms
        )
        value = (
            params.notional
            + (spot.close - cycle.entry_spot_price) * spot_qty
            + (cycle.entry_perp_price - perp.close) * perp_qty
            + funding
            - entry_cost
        )
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return abs(worst)


def _equity_returns(equity_curve: list[float]) -> list[float]:
    return [
        0.0 if equity_curve[idx - 1] <= 0 else equity_curve[idx] / equity_curve[idx - 1] - 1.0
        for idx in range(1, len(equity_curve))
    ]


def _max_drawdown_from_equity(equity_curve: list[float]) -> float:
    peak = 0.0
    worst = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return abs(worst)


def _profit_factor_from_cycles(cycles: list[FundingArbCycle], pnl_weight: float) -> float:
    wins = sum(cycle.net_pnl * pnl_weight for cycle in cycles if cycle.net_pnl > 0)
    losses = abs(sum(cycle.net_pnl * pnl_weight for cycle in cycles if cycle.net_pnl < 0))
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return wins / losses


def _time_indexed_metrics(
    equity_times_ms: list[int],
    equity_curve: list[float],
    cycles: list[FundingArbCycle],
    sleep_periods: list[SleepPeriod],
    pnl_weight: float = 1.0,
) -> dict[str, float]:
    if len(equity_times_ms) != len(equity_curve):
        raise ValueError("equity times and values must have the same length")
    span_days = (
        max((equity_times_ms[-1] - equity_times_ms[0]) / MS_PER_DAY, 0.0)
        if len(equity_times_ms) >= 2
        else 0.0
    )
    returns = _equity_returns(equity_curve)
    total = equity_curve[-1] / equity_curve[0] - 1.0 if len(equity_curve) >= 2 and equity_curve[0] > 0 else 0.0
    annualized_return = (
        (equity_curve[-1] / equity_curve[0]) ** (365.0 / span_days) - 1.0
        if span_days > 0 and equity_curve[0] > 0 and equity_curve[-1] > 0
        else 0.0
    )
    periods_per_year = len(returns) / (span_days / 365.0) if span_days > 0 and returns else 0.0
    if len(returns) >= 2 and periods_per_year > 0:
        mean_return = sum(returns) / len(returns)
        variance = sum((item - mean_return) ** 2 for item in returns) / len(returns)
        annualized_volatility = math.sqrt(variance) * math.sqrt(periods_per_year)
        sharpe = (mean_return * periods_per_year) / annualized_volatility if annualized_volatility > 0 else 0.0
    else:
        annualized_volatility = 0.0
        sharpe = 0.0
    held_days = sum(cycle.holding_days * pnl_weight for cycle in cycles)
    winning_cycles = sum(1 for cycle in cycles if cycle.net_pnl > 0)
    return {
        "total_return": total,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "sharpe": sharpe,
        "max_drawdown": _max_drawdown_from_equity(equity_curve),
        "complete_cycles": float(len(cycles)),
        "win_rate": winning_cycles / len(cycles) if cycles else 0.0,
        "profit_factor": _profit_factor_from_cycles(cycles, pnl_weight),
        "average_holding_days": sum(cycle.holding_days for cycle in cycles) / len(cycles) if cycles else 0.0,
        "funding_income_total": sum(cycle.funding_income * pnl_weight for cycle in cycles),
        "basis_pnl_total": sum(cycle.basis_pnl * pnl_weight for cycle in cycles),
        "fees_total": sum(cycle.fees * pnl_weight for cycle in cycles),
        "slippage_total": sum(cycle.slippage * pnl_weight for cycle in cycles),
        "worst_cycle": min((cycle.net_return for cycle in cycles), default=0.0),
        "best_cycle": max((cycle.net_return for cycle in cycles), default=0.0),
        "longest_sleep_days": max((period.days for period in sleep_periods), default=0.0),
        "percent_time_in_market": held_days / span_days if span_days > 0 else 0.0,
        "equity_points": float(len(equity_curve)),
        "return_observations": float(len(returns)),
        "span_days": span_days,
    }


def _cycle_value_at(
    cycle: FundingArbCycle,
    time_ms: int,
    spot_bars: list[TrendBar],
    perp_bars: list[TrendBar],
    params: FundingArbParams,
) -> float:
    if time_ms >= cycle.exit_time_ms:
        return cycle.net_pnl
    spot = _completed_bar_at_or_before(spot_bars, time_ms)
    perp = _completed_bar_at_or_before(perp_bars, time_ms)
    if spot is None or perp is None:
        return 0.0
    spot_qty = params.notional / cycle.entry_spot_price
    perp_qty = spot_qty
    funding = sum(item.income for item in cycle.funding_contributions if item.funding_time_ms <= time_ms)
    open_cost = (cycle.fees + cycle.slippage) / 2.0
    return (
        (spot.close - cycle.entry_spot_price) * spot_qty
        + (cycle.entry_perp_price - perp.close) * perp_qty
        + funding
        - open_cost
    )


def _event_time_equity_curve(
    cycles: list[FundingArbCycle],
    points: list[FundingPoint],
    spot_bars: list[TrendBar],
    perp_bars: list[TrendBar],
    params: FundingArbParams,
    data_start_ms: int,
    data_end_ms: int,
) -> tuple[list[int], list[float]]:
    timeline = sorted(
        {data_start_ms, data_end_ms}
        | {point.funding_time_ms for point in points if data_start_ms <= point.funding_time_ms <= data_end_ms}
        | {cycle.exit_time_ms for cycle in cycles if data_start_ms <= cycle.exit_time_ms <= data_end_ms}
    )
    values: list[float] = []
    for time_ms in timeline:
        realized = sum(cycle.net_pnl for cycle in cycles if cycle.exit_time_ms <= time_ms)
        unrealized = sum(
            _cycle_value_at(cycle, time_ms, spot_bars, perp_bars, params)
            for cycle in cycles
            if cycle.entry_time_ms <= time_ms < cycle.exit_time_ms
        )
        values.append(max(0.0001, 1.0 + realized + unrealized))
    return timeline, values


def _slice_equity_window(
    equity_times_ms: list[int],
    equity_curve: list[float],
    start_ms: int | None,
    end_ms: int | None,
) -> tuple[list[int], list[float]]:
    if not equity_times_ms or not equity_curve or start_ms is None or end_ms is None:
        return [], []
    anchor = 0
    for idx, time_ms in enumerate(equity_times_ms):
        if time_ms <= start_ms:
            anchor = idx
        else:
            break
    times = [start_ms]
    values = [equity_curve[anchor]]
    for time_ms, value in zip(equity_times_ms, equity_curve):
        if start_ms < time_ms <= end_ms:
            times.append(time_ms)
            values.append(value)
    if times[-1] < end_ms:
        times.append(end_ms)
        values.append(values[-1])
    return times, values


def _sleep_periods(
    symbol: str,
    data_start: int | None,
    data_end: int | None,
    cycles: list[FundingArbCycle],
    incomplete: list[IncompletePosition],
) -> list[SleepPeriod]:
    if data_start is None or data_end is None or data_end <= data_start:
        return []
    occupied = [(cycle.entry_time_ms, cycle.exit_time_ms) for cycle in cycles]
    occupied.extend((item.entry_time_ms, data_end) for item in incomplete)
    periods: list[SleepPeriod] = []
    cursor = data_start
    for start, end in sorted(occupied):
        if start > cursor:
            periods.append(SleepPeriod(symbol, cursor, start, (start - cursor) / MS_PER_DAY, "below_entry_threshold"))
        cursor = max(cursor, end)
    if data_end > cursor:
        periods.append(SleepPeriod(symbol, cursor, data_end, (data_end - cursor) / MS_PER_DAY, "below_entry_threshold"))
    return [period for period in periods if period.days > 0]


def run_funding_arbitrage_backtest(
    symbol: str,
    spot_bars: list[TrendBar],
    perp_bars: list[TrendBar],
    funding_history: list[dict[str, Any]],
    mark_bars: list[TrendBar] | None = None,
    index_bars: list[TrendBar] | None = None,
    premium_bars: list[TrendBar] | None = None,
    params: FundingArbParams | None = None,
) -> FundingArbResult:
    params = params or FundingArbParams()
    mark_bars = mark_bars or []
    index_bars = index_bars or []
    premium_bars = premium_bars or []
    for name, bars in (
        ("spot", spot_bars),
        ("perpetual", perp_bars),
        ("mark", mark_bars),
        ("index", index_bars),
        ("premium", premium_bars),
    ):
        _validate_hourly_bars(name, bars)

    points, modal_interval, interval_anomalies = build_funding_points(symbol, funding_history)
    data_start = max(spot_bars[0].open_time_ms, perp_bars[0].open_time_ms, points[0].funding_time_ms)
    data_end = min(
        spot_bars[-1].close_time_ms,
        perp_bars[-1].close_time_ms,
        points[-1].funding_time_ms + MS_PER_HOUR,
    )
    if data_end <= data_start:
        raise ValueError("M1B data ranges do not overlap")
    points = [point for point in points if data_start <= point.funding_time_ms <= data_end]
    if len(points) < 2:
        raise ValueError("fewer than two funding events overlap the 1h market data")
    split_ms = data_start + int((data_end - data_start) * (1.0 - params.oos_fraction))
    basis_status, diagnostics = _market_diagnostics(points, mark_bars, index_bars, premium_bars)

    cycles: list[FundingArbCycle] = []
    incomplete: list[IncompletePosition] = []
    entry_signal: FundingPoint | None = None
    entry_spot: TrendBar | None = None
    entry_perp: TrendBar | None = None
    contributions: list[FundingContribution] = []
    negative_streak = 0
    low_mean_since_ms: int | None = None
    no_lookahead = True

    for idx, point in enumerate(points):
        if not (data_start <= point.funding_time_ms <= data_end):
            continue
        mean_apr = _rolling_mean_annualized(points, idx)
        if entry_signal is None:
            if not should_enter_funding_arb(mean_apr, point.funding_rate, params):
                continue
            execution = _first_common_bar_open_after(spot_bars, perp_bars, point.funding_time_ms)
            if execution is None:
                continue
            entry_spot, entry_perp = execution
            no_lookahead = no_lookahead and entry_spot.open_time_ms > point.funding_time_ms
            entry_signal = point
            contributions = []
            negative_streak = 0
            low_mean_since_ms = None
            continue

        if entry_spot is None or entry_perp is None:
            raise RuntimeError("entry state is incomplete")
        if point.funding_time_ms <= entry_spot.open_time_ms:
            continue
        # Equal base-asset quantity keeps the price legs direction-neutral.
        perp_qty = params.notional / entry_spot.open
        contribution = _funding_contribution(point, mark_bars, perp_qty)
        if contribution is None:
            basis_status = "partial"
        else:
            contributions.append(contribution)
            no_lookahead = no_lookahead and contribution.valuation_bar_close_time_ms <= point.funding_time_ms
        negative_streak = negative_streak + 1 if point.funding_rate < 0 else 0
        if mean_apr < params.exit_mean_apr_threshold:
            low_mean_since_ms = low_mean_since_ms or point.funding_time_ms
        else:
            low_mean_since_ms = None
        low_funding_days = (
            (point.funding_time_ms - low_mean_since_ms) / MS_PER_DAY
            if low_mean_since_ms is not None
            else 0.0
        )
        exit_reason = should_exit_funding_arb(
            mean_apr,
            negative_streak,
            params,
            low_funding_days=low_funding_days,
        )
        if exit_reason is None:
            continue
        execution = _first_common_bar_open_after(spot_bars, perp_bars, point.funding_time_ms)
        if execution is None:
            incomplete.append(
                IncompletePosition(
                    symbol=symbol,
                    entry_signal_time_ms=entry_signal.funding_time_ms,
                    entry_time_ms=entry_spot.open_time_ms,
                    last_event_time_ms=point.funding_time_ms,
                    funding_periods_count=len(contributions),
                    reason="exit_signal_without_next_hour_open",
                )
            )
            entry_signal = None
            entry_spot = None
            entry_perp = None
            contributions = []
            break
        exit_spot, exit_perp = execution
        no_lookahead = no_lookahead and exit_spot.open_time_ms > point.funding_time_ms
        pnl = compute_two_leg_pnl(
            entry_spot.open,
            exit_spot.open,
            entry_perp.open,
            exit_perp.open,
            [item.funding_rate for item in contributions],
            params,
            [item.settlement_mark_price for item in contributions],
            perp_qty,
        )
        provisional = FundingArbCycle(
            symbol=symbol,
            entry_signal_time_ms=entry_signal.funding_time_ms,
            entry_time_ms=entry_spot.open_time_ms,
            exit_signal_time_ms=point.funding_time_ms,
            exit_time_ms=exit_spot.open_time_ms,
            holding_days=(exit_spot.open_time_ms - entry_spot.open_time_ms) / MS_PER_DAY,
            entry_spot_price=entry_spot.open,
            entry_perp_price=entry_perp.open,
            exit_spot_price=exit_spot.open,
            exit_perp_price=exit_perp.open,
            entry_basis=pnl.entry_basis,
            exit_basis=pnl.exit_basis,
            spot_pnl=pnl.spot_pnl,
            perp_short_pnl=pnl.perp_short_pnl,
            funding_income=pnl.funding_income,
            basis_pnl=pnl.basis_pnl,
            fees=pnl.fees,
            slippage=pnl.slippage,
            net_pnl=pnl.net_pnl,
            net_return=pnl.net_return,
            max_drawdown_during_cycle=0.0,
            exit_reason=exit_reason,
            funding_periods_count=len(contributions),
            negative_funding_periods_count=sum(1 for item in contributions if item.funding_rate < 0),
            funding_contributions=tuple(contributions),
            basis_data_status=basis_status,
        )
        cycles.append(
            FundingArbCycle(
                **{**provisional.__dict__, "max_drawdown_during_cycle": _cycle_drawdown(provisional, spot_bars, perp_bars, params)}
            )
        )
        entry_signal = None
        entry_spot = None
        entry_perp = None
        contributions = []
        negative_streak = 0
        low_mean_since_ms = None

    if entry_signal is not None and entry_spot is not None:
        incomplete.append(
            IncompletePosition(
                symbol=symbol,
                entry_signal_time_ms=entry_signal.funding_time_ms,
                entry_time_ms=entry_spot.open_time_ms,
                last_event_time_ms=points[-1].funding_time_ms,
                funding_periods_count=len(contributions),
                reason="data_end_without_legal_exit",
            )
        )

    sleep_periods = _sleep_periods(symbol, data_start, data_end, cycles, incomplete)
    equity_times, equity_curve = _event_time_equity_curve(
        cycles, points, spot_bars, perp_bars, params, data_start, data_end
    )
    summary = _time_indexed_metrics(equity_times, equity_curve, cycles, sleep_periods)
    summary["incomplete_positions"] = float(len(incomplete))
    oos_times, oos_equity = _slice_equity_window(equity_times, equity_curve, split_ms, data_end)
    oos_cycles = [cycle for cycle in cycles if cycle.entry_time_ms >= split_ms]
    carry_in = [cycle for cycle in cycles if cycle.entry_time_ms < split_ms < cycle.exit_time_ms]
    oos_summary = _time_indexed_metrics(oos_times, oos_equity, oos_cycles, [])
    oos_summary["carry_in_cycles"] = float(len(carry_in))
    distribution = Counter(f"{point.interval_hours:g}h" for point in points)
    result = FundingArbResult(
        symbol=symbol,
        params=params,
        cost_label="cost_x2" if params.cost_multiplier > 1 else "base_cost",
        cycles=cycles,
        equity_times_ms=equity_times,
        equity_curve=equity_curve,
        metrics=summary,
        oos_metrics=oos_summary,
        gates={},
        final_status="under_review",
        interval_hours=modal_interval,
        interval_source="M0 fundingRate.fundingTime per event",
        interval_anomalies=interval_anomalies,
        sleep_periods=sleep_periods,
        data_start_ms=data_start,
        data_end_ms=data_end,
        is_start_ms=data_start,
        is_end_ms=split_ms,
        oos_start_ms=split_ms,
        oos_end_ms=data_end,
        basis_data_status=basis_status,
        interval_distribution=dict(distribution),
        incomplete_positions=incomplete,
        oos_carry_in_cycles=carry_in,
        diagnostics=diagnostics,
        no_lookahead=no_lookahead,
    )
    gates, final_status = evaluate_m1b_gates(result)
    return FundingArbResult(**{**result.__dict__, "gates": gates, "final_status": final_status})


def combine_funding_results(
    components: dict[str, FundingArbResult],
    params: FundingArbParams | None = None,
    cost_label: str = "base_cost",
) -> FundingArbResult:
    params = params or FundingArbParams()
    if not components:
        raise ValueError("at least one component result is required")
    cycles = sorted(
        [cycle for result in components.values() for cycle in result.cycles],
        key=lambda cycle: (cycle.entry_time_ms, cycle.symbol),
    )
    data_start = max(result.data_start_ms or 0 for result in components.values())
    data_end = min(result.data_end_ms or 0 for result in components.values())
    union_times = sorted(
        {
            time_ms
            for result in components.values()
            for time_ms in result.equity_times_ms
            if data_start <= time_ms <= data_end
        }
    )
    weight = 1.0 / len(components)
    component_indices = {symbol: 0 for symbol in components}
    equity: list[float] = []
    for time_ms in union_times:
        total = 0.0
        for symbol, result in components.items():
            idx = component_indices[symbol]
            while idx + 1 < len(result.equity_times_ms) and result.equity_times_ms[idx + 1] <= time_ms:
                idx += 1
            component_indices[symbol] = idx
            total += result.equity_curve[idx] * weight
        equity.append(total)
    sleep = [period for result in components.values() for period in result.sleep_periods]
    summary = _time_indexed_metrics(union_times, equity, cycles, sleep, weight)
    incomplete = [item for result in components.values() for item in result.incomplete_positions]
    summary["incomplete_positions"] = float(len(incomplete))
    split_ms = data_start + int((data_end - data_start) * (1.0 - params.oos_fraction))
    oos_times, oos_equity = _slice_equity_window(union_times, equity, split_ms, data_end)
    oos_cycles = [cycle for cycle in cycles if cycle.entry_time_ms >= split_ms]
    carry_in = [cycle for cycle in cycles if cycle.entry_time_ms < split_ms < cycle.exit_time_ms]
    oos_summary = _time_indexed_metrics(oos_times, oos_equity, oos_cycles, [], weight)
    oos_summary["carry_in_cycles"] = float(len(carry_in))
    all_sets = [set(result.equity_times_ms) for result in components.values()]
    intersection = set.intersection(*all_sets) if all_sets else set()
    interval_distribution = Counter()
    for result in components.values():
        interval_distribution.update(result.interval_distribution)
    diagnostics = {
        "utc_union_points": len(union_times),
        "utc_intersection_points": len(intersection),
        "symbols_aligned_by_utc_timestamp": True,
        "component_diagnostics": {symbol: result.diagnostics for symbol, result in components.items()},
    }
    result = FundingArbResult(
        symbol="BTC+ETH",
        params=params,
        cost_label=cost_label,
        cycles=cycles,
        equity_times_ms=union_times,
        equity_curve=equity,
        metrics=summary,
        oos_metrics=oos_summary,
        gates={},
        final_status="under_review",
        interval_hours=min(result.interval_hours for result in components.values()),
        interval_source="component M0 per-event funding intervals",
        interval_anomalies=[item for result in components.values() for item in result.interval_anomalies],
        sleep_periods=sleep,
        data_start_ms=data_start,
        data_end_ms=data_end,
        is_start_ms=data_start,
        is_end_ms=split_ms,
        oos_start_ms=split_ms,
        oos_end_ms=data_end,
        basis_data_status=(
            "available" if all(result.basis_data_status == "available" for result in components.values()) else "partial"
        ),
        interval_distribution=dict(interval_distribution),
        incomplete_positions=incomplete,
        oos_carry_in_cycles=carry_in,
        diagnostics=diagnostics,
        no_lookahead=all(result.no_lookahead for result in components.values()),
        components=components,
    )
    gates, final_status = evaluate_m1b_gates(result)
    return FundingArbResult(**{**result.__dict__, "gates": gates, "final_status": final_status})


def evaluate_m1b_gates(
    result: FundingArbResult,
    cost_x2_result: FundingArbResult | None = None,
) -> tuple[dict[str, str], str]:
    params = result.params
    threshold = compute_payback_required_apr(params)
    if result.data_start_ms is None or result.data_end_ms is None or not result.equity_curve:
        return {"Backtest code": "under_review"}, "under_review"
    oos_points = int(result.oos_metrics.get("equity_points", 0.0))
    if oos_points < 30:
        oos_gate = "insufficient_data"
    elif result.oos_split_basis != "time-based last 30%" or result.metrics_basis != "funding-event time-indexed equity curve":
        oos_gate = "invalid_metric"
    else:
        oos_gate = "pass" if result.oos_metrics.get("sharpe", 0.0) >= params.min_oos_sharpe else "fail"
    gates = {
        "Backtest code": "pass",
        "Funding interval not hardcoded": "pass" if result.interval_distribution and result.interval_source else "fail",
        "Payback threshold": "pass"
        if threshold > params.entry_mean_apr_threshold
        and not should_enter_funding_arb(params.entry_mean_apr_threshold, 0.001, params)
        else "fail",
        "Base cost positive": "pass" if result.metrics.get("total_return", 0.0) > 0 else "fail",
        "Cost x2 positive": "pass"
        if cost_x2_result is not None and cost_x2_result.metrics.get("total_return", 0.0) > 0
        else "fail",
        "Complete cycles >= 20": "pass"
        if result.metrics.get("complete_cycles", 0.0) >= params.min_complete_cycles
        else "fail",
        "OOS Sharpe >= 1.0": oos_gate,
        "Max drawdown <= 5%": "pass"
        if result.metrics.get("max_drawdown", 1.0) <= params.max_drawdown_limit
        else "fail",
        "Funding dries up gracefully": "pass" if result.sleep_periods or not result.cycles else "fail",
        "No lookahead": "pass" if result.no_lookahead else "fail",
    }
    # Even a fully passing numerical result requires human review and cannot
    # approve M2 automatically.
    final_status = "under_review" if all(status == "pass" for status in gates.values()) else "failed_validation"
    return gates, final_status


def result_date_range(result: FundingArbResult) -> str:
    return f"{utc_ms(result.data_start_ms)} -> {utc_ms(result.data_end_ms)}"


def percent(value: float) -> str:
    if math.isinf(value):
        return "inf"
    return f"{value * 100:.4f}%"
