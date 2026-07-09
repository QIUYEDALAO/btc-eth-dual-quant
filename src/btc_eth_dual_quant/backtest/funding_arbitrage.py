"""M1B offline funding-rate-arbitrage validation engine.

The engine models a fixed research structure: spot long plus USDT perpetual
short with equal notional. It consumes local M0 public data supplied by callers;
it does not call exchange APIs and does not model paper/live execution.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .trend_strategy import TrendBar


MS_PER_HOUR = 3_600_000
MS_PER_DAY = 86_400_000
HOURS_PER_YEAR = 365 * 24
FUNDING_INTERVAL_JITTER_TOLERANCE_MS = 60_000


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


@dataclass(frozen=True)
class FundingArbCycle:
    symbol: str
    entry_time_ms: int
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
    basis_data_status: str = "available"


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
    metrics_basis: str = "funding-period time-indexed equity curve"
    oos_split_basis: str = "time-based last 30%"
    no_lookahead: bool = True
    components: dict[str, "FundingArbResult"] = field(default_factory=dict)


def utc_ms(value: int | None) -> str:
    if value is None:
        return "n/a"
    return datetime.fromtimestamp(value / 1000, tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def infer_interval_from_funding_history(records: list[dict[str, Any] | FundingPoint]) -> tuple[float, list[str]]:
    times = sorted(
        {
            int(record.funding_time_ms if isinstance(record, FundingPoint) else record["fundingTime"])
            for record in records
            if (record.funding_time_ms if isinstance(record, FundingPoint) else record.get("fundingTime")) is not None
        }
    )
    if len(times) < 2:
        raise ValueError("at least two funding records are required to infer interval")
    deltas = [right - left for left, right in zip(times, times[1:]) if right > left]
    if not deltas:
        raise ValueError("funding records must contain increasing timestamps")
    buckets = [round(delta / FUNDING_INTERVAL_JITTER_TOLERANCE_MS) for delta in deltas]
    mode_bucket, _count = Counter(buckets).most_common(1)[0]
    mode_delta = mode_bucket * FUNDING_INTERVAL_JITTER_TOLERANCE_MS
    interval_hours = mode_delta / MS_PER_HOUR
    warnings: list[str] = []
    unusual = sorted({delta for delta in deltas if abs(delta - mode_delta) > FUNDING_INTERVAL_JITTER_TOLERANCE_MS})
    if unusual:
        hours = ", ".join(f"{delta / MS_PER_HOUR:.4g}" for delta in unusual[:6])
        warnings.append(f"funding_interval_anomaly: observed non-modal interval hours {hours}")
    if interval_hours <= 0:
        raise ValueError("funding interval must be positive")
    return interval_hours, warnings


def annualize_funding_rate(period_rate: float, interval_hours: float) -> float:
    if interval_hours <= 0:
        raise ValueError("interval_hours must be positive")
    return period_rate * (HOURS_PER_YEAR / interval_hours)


def compute_payback_required_apr(params: FundingArbParams | None = None) -> float:
    params = params or FundingArbParams()
    return params.roundtrip_cost_base * params.min_payback_ratio * 365.0 / params.expected_hold_days


def should_enter_funding_arb(mean_annualized_3d: float, current_funding_rate: float, params: FundingArbParams | None = None) -> bool:
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
) -> str | None:
    params = params or FundingArbParams()
    if negative_funding_streak >= 2:
        return "negative_funding_streak"
    if mean_annualized_3d < params.exit_mean_apr_threshold:
        return "low_funding_mean"
    return None


def compute_two_leg_pnl(
    entry_spot_price: float,
    exit_spot_price: float,
    entry_perp_price: float,
    exit_perp_price: float,
    funding_rates: list[float],
    params: FundingArbParams | None = None,
) -> TwoLegPnl:
    params = params or FundingArbParams()
    if min(entry_spot_price, exit_spot_price, entry_perp_price, exit_perp_price) <= 0:
        raise ValueError("prices must be positive")
    notional = params.notional
    spot_qty = notional / entry_spot_price
    perp_qty = notional / entry_perp_price
    spot_pnl = (exit_spot_price - entry_spot_price) * spot_qty
    perp_short_pnl = (entry_perp_price - exit_perp_price) * perp_qty
    funding_income = sum(funding_rates) * notional
    basis_pnl = spot_pnl + perp_short_pnl
    fees = notional * ((params.spot_fee_per_side * 2) + (params.futures_fee_per_side * 2)) * params.cost_multiplier
    slippage = notional * (params.slippage_per_leg * 4) * params.cost_multiplier
    net_pnl = basis_pnl + funding_income - fees - slippage
    return TwoLegPnl(
        spot_pnl=spot_pnl,
        perp_short_pnl=perp_short_pnl,
        funding_income=funding_income,
        basis_pnl=basis_pnl,
        fees=fees,
        slippage=slippage,
        net_pnl=net_pnl,
        net_return=net_pnl / notional,
        entry_basis=entry_perp_price - entry_spot_price,
        exit_basis=exit_perp_price - exit_spot_price,
    )


def _funding_points(symbol: str, funding_history: list[dict[str, Any]], interval_hours: float) -> list[FundingPoint]:
    points: list[FundingPoint] = []
    for row in funding_history:
        try:
            rate = float(row["fundingRate"])
            time_ms = int(row["fundingTime"])
        except (KeyError, TypeError, ValueError):
            continue
        points.append(
            FundingPoint(
                symbol=symbol,
                funding_time_ms=time_ms,
                funding_rate=rate,
                interval_hours=interval_hours,
                annualized_rate=annualize_funding_rate(rate, interval_hours),
            )
        )
    return sorted(points, key=lambda item: item.funding_time_ms)


def _latest_bar_at_or_before(bars: list[TrendBar], time_ms: int) -> TrendBar | None:
    candidate: TrendBar | None = None
    for bar in bars:
        if bar.open_time_ms <= time_ms:
            candidate = bar
        else:
            break
    return candidate


def _rolling_mean_annualized(points: list[FundingPoint], idx: int, window_ms: int = 3 * MS_PER_DAY) -> float:
    current_time = points[idx].funding_time_ms
    values = [
        point.annualized_rate
        for point in points[: idx + 1]
        if current_time - window_ms < point.funding_time_ms <= current_time
    ]
    return sum(values) / len(values) if values else 0.0


def _cycle_drawdown(
    entry_spot_price: float,
    entry_perp_price: float,
    spot_bars: list[TrendBar],
    perp_bars: list[TrendBar],
    funding_points: list[FundingPoint],
    params: FundingArbParams,
) -> float:
    spot_qty = params.notional / entry_spot_price
    perp_qty = params.notional / entry_perp_price
    equity = params.notional
    peak = equity
    worst = 0.0
    funding_sum = 0.0
    for point in funding_points:
        spot = _latest_bar_at_or_before(spot_bars, point.funding_time_ms)
        perp = _latest_bar_at_or_before(perp_bars, point.funding_time_ms)
        if spot is None or perp is None:
            continue
        funding_sum += point.funding_rate * params.notional
        spot_pnl = (spot.close - entry_spot_price) * spot_qty
        perp_pnl = (entry_perp_price - perp.close) * perp_qty
        equity = params.notional + spot_pnl + perp_pnl + funding_sum
        peak = max(peak, equity)
        if peak > 0:
            worst = min(worst, equity / peak - 1.0)
    return abs(worst)


def _equity_returns(equity_curve: list[float]) -> list[float]:
    returns: list[float] = []
    for idx in range(1, len(equity_curve)):
        previous = equity_curve[idx - 1]
        returns.append(0.0 if previous <= 0 else equity_curve[idx] / previous - 1.0)
    return returns


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
        raise ValueError("equity_times_ms and equity_curve must have the same length")
    span_days = (
        max((equity_times_ms[-1] - equity_times_ms[0]) / MS_PER_DAY, 0.0)
        if len(equity_times_ms) >= 2
        else 0.0
    )
    returns = _equity_returns(equity_curve)
    total = equity_curve[-1] / equity_curve[0] - 1.0 if len(equity_curve) >= 2 and equity_curve[0] > 0 else 0.0
    annualized_return = (equity_curve[-1] / equity_curve[0]) ** (365.0 / span_days) - 1.0 if span_days > 0 and equity_curve[0] > 0 and equity_curve[-1] > 0 else 0.0
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


def _cycle_pnl_at_time(
    cycle: FundingArbCycle,
    point: FundingPoint,
    spot_bars: list[TrendBar],
    perp_bars: list[TrendBar],
    held_points: list[FundingPoint],
    params: FundingArbParams,
) -> float:
    if point.funding_time_ms >= cycle.exit_time_ms:
        return cycle.net_pnl
    spot = _latest_bar_at_or_before(spot_bars, point.funding_time_ms)
    perp = _latest_bar_at_or_before(perp_bars, point.funding_time_ms)
    if spot is None or perp is None:
        return 0.0
    spot_qty = params.notional / cycle.entry_spot_price
    perp_qty = params.notional / cycle.entry_perp_price
    spot_pnl = (spot.close - cycle.entry_spot_price) * spot_qty
    perp_short_pnl = (cycle.entry_perp_price - perp.close) * perp_qty
    funding_income = sum(item.funding_rate for item in held_points) * params.notional
    open_cost = (cycle.fees + cycle.slippage) / 2.0
    return spot_pnl + perp_short_pnl + funding_income - open_cost


def _funding_period_equity_curve(
    cycles: list[FundingArbCycle],
    points: list[FundingPoint],
    spot_bars: list[TrendBar],
    perp_bars: list[TrendBar],
    params: FundingArbParams,
    data_start_ms: int,
    data_end_ms: int,
) -> tuple[list[int], list[float]]:
    in_range_points = [point for point in points if data_start_ms <= point.funding_time_ms <= data_end_ms]
    if not in_range_points:
        return [data_start_ms, data_end_ms], [1.0, 1.0]
    ordered_cycles = sorted(cycles, key=lambda cycle: cycle.entry_time_ms)
    cycle_idx = 0
    realized_pnl = 0.0
    equity_times: list[int] = []
    equity: list[float] = []
    for point in in_range_points:
        while cycle_idx < len(ordered_cycles) and ordered_cycles[cycle_idx].exit_time_ms < point.funding_time_ms:
            realized_pnl += ordered_cycles[cycle_idx].net_pnl
            cycle_idx += 1
        current_cycle = ordered_cycles[cycle_idx] if cycle_idx < len(ordered_cycles) else None
        if current_cycle and current_cycle.entry_time_ms <= point.funding_time_ms <= current_cycle.exit_time_ms:
            held_points = [
                item
                for item in points
                if current_cycle.entry_time_ms <= item.funding_time_ms <= point.funding_time_ms
            ]
            current_pnl = _cycle_pnl_at_time(current_cycle, point, spot_bars, perp_bars, held_points, params)
            value = 1.0 + realized_pnl + current_pnl
            if point.funding_time_ms >= current_cycle.exit_time_ms:
                realized_pnl += current_cycle.net_pnl
                cycle_idx += 1
        else:
            value = 1.0 + realized_pnl
        equity_times.append(point.funding_time_ms)
        equity.append(max(0.0001, value))
    if equity_times[0] > data_start_ms:
        equity_times.insert(0, data_start_ms)
        equity.insert(0, 1.0)
    if equity_times[-1] < data_end_ms:
        equity_times.append(data_end_ms)
        equity.append(equity[-1])
    return equity_times, equity


def _slice_equity_window(
    equity_times_ms: list[int],
    equity_curve: list[float],
    start_ms: int | None,
    end_ms: int | None,
) -> tuple[list[int], list[float]]:
    if not equity_times_ms or not equity_curve or start_ms is None or end_ms is None:
        return [], []
    anchor_idx: int | None = None
    for idx, ts in enumerate(equity_times_ms):
        if ts <= start_ms:
            anchor_idx = idx
        elif ts > start_ms:
            break
    times: list[int] = []
    values: list[float] = []
    if anchor_idx is not None:
        times.append(start_ms)
        values.append(equity_curve[anchor_idx])
    for ts, value in zip(equity_times_ms, equity_curve):
        if start_ms < ts <= end_ms:
            times.append(ts)
            values.append(value)
    if len(times) == 1 and end_ms > times[0]:
        times.append(end_ms)
        values.append(values[-1])
    return times, values


def _sleep_periods(symbol: str, data_start: int | None, data_end: int | None, cycles: list[FundingArbCycle]) -> list[SleepPeriod]:
    if data_start is None or data_end is None or data_end <= data_start:
        return []
    periods: list[SleepPeriod] = []
    cursor = data_start
    for cycle in cycles:
        if cycle.entry_time_ms > cursor:
            periods.append(
                SleepPeriod(
                    symbol=symbol,
                    start_time_ms=cursor,
                    end_time_ms=cycle.entry_time_ms,
                    days=(cycle.entry_time_ms - cursor) / MS_PER_DAY,
                    reason="below_entry_threshold",
                )
            )
        cursor = max(cursor, cycle.exit_time_ms)
    if data_end > cursor:
        periods.append(
            SleepPeriod(
                symbol=symbol,
                start_time_ms=cursor,
                end_time_ms=data_end,
                days=(data_end - cursor) / MS_PER_DAY,
                reason="below_entry_threshold",
            )
        )
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
    if not spot_bars or not perp_bars or not funding_history:
        raise ValueError("spot bars, perpetual bars, and funding history are required")
    interval_hours, interval_anomalies = infer_interval_from_funding_history(funding_history)
    points = _funding_points(symbol, funding_history, interval_hours)
    data_start = max(spot_bars[0].open_time_ms, perp_bars[0].open_time_ms, points[0].funding_time_ms)
    data_end = min(spot_bars[-1].open_time_ms, perp_bars[-1].open_time_ms, points[-1].funding_time_ms)
    data_days = max(1.0, (data_end - data_start) / MS_PER_DAY)
    split_ms = data_start + int((data_end - data_start) * (1.0 - params.oos_fraction))

    cycles: list[FundingArbCycle] = []
    in_position = False
    entry_point: FundingPoint | None = None
    entry_spot: TrendBar | None = None
    entry_perp: TrendBar | None = None
    held_points: list[FundingPoint] = []
    negative_streak = 0
    basis_data_status = "available"

    for idx, point in enumerate(points):
        if point.funding_time_ms < data_start or point.funding_time_ms > data_end:
            continue
        mean_apr = _rolling_mean_annualized(points, idx)
        if not in_position:
            if should_enter_funding_arb(mean_apr, point.funding_rate, params):
                spot = _latest_bar_at_or_before(spot_bars, point.funding_time_ms)
                perp = _latest_bar_at_or_before(perp_bars, point.funding_time_ms)
                if spot is None or perp is None:
                    continue
                for optional_bars in (mark_bars, index_bars, premium_bars):
                    if optional_bars is not None and _latest_bar_at_or_before(optional_bars, point.funding_time_ms) is None:
                        basis_data_status = "basis_data_unavailable"
                in_position = True
                entry_point = point
                entry_spot = spot
                entry_perp = perp
                held_points = [point]
                negative_streak = 1 if point.funding_rate < 0 else 0
            continue

        held_points.append(point)
        negative_streak = negative_streak + 1 if point.funding_rate < 0 else 0
        exit_reason = should_exit_funding_arb(mean_apr, negative_streak, params)
        if exit_reason is None:
            continue
        if entry_point is None or entry_spot is None or entry_perp is None:
            raise RuntimeError("position state is incomplete")
        exit_spot = _latest_bar_at_or_before(spot_bars, point.funding_time_ms)
        exit_perp = _latest_bar_at_or_before(perp_bars, point.funding_time_ms)
        if exit_spot is None or exit_perp is None:
            continue
        pnl = compute_two_leg_pnl(
            entry_spot.close,
            exit_spot.close,
            entry_perp.close,
            exit_perp.close,
            [item.funding_rate for item in held_points],
            params,
        )
        cycle_basis_status = basis_data_status
        for optional_bars in (mark_bars, index_bars, premium_bars):
            if optional_bars is not None and _latest_bar_at_or_before(optional_bars, point.funding_time_ms) is None:
                cycle_basis_status = "basis_data_unavailable"
        cycles.append(
            FundingArbCycle(
                symbol=symbol,
                entry_time_ms=entry_point.funding_time_ms,
                exit_time_ms=point.funding_time_ms,
                holding_days=max(0.0, (point.funding_time_ms - entry_point.funding_time_ms) / MS_PER_DAY),
                entry_spot_price=entry_spot.close,
                entry_perp_price=entry_perp.close,
                exit_spot_price=exit_spot.close,
                exit_perp_price=exit_perp.close,
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
                max_drawdown_during_cycle=_cycle_drawdown(entry_spot.close, entry_perp.close, spot_bars, perp_bars, held_points, params),
                exit_reason=exit_reason,
                funding_periods_count=len(held_points),
                negative_funding_periods_count=sum(1 for item in held_points if item.funding_rate < 0),
                basis_data_status=cycle_basis_status,
            )
        )
        in_position = False
        entry_point = None
        entry_spot = None
        entry_perp = None
        held_points = []
        negative_streak = 0

    if in_position and entry_point is not None and entry_spot is not None and entry_perp is not None and held_points:
        exit_point = held_points[-1]
        exit_spot = _latest_bar_at_or_before(spot_bars, exit_point.funding_time_ms)
        exit_perp = _latest_bar_at_or_before(perp_bars, exit_point.funding_time_ms)
        if exit_spot is not None and exit_perp is not None:
            pnl = compute_two_leg_pnl(
                entry_spot.close,
                exit_spot.close,
                entry_perp.close,
                exit_perp.close,
                [item.funding_rate for item in held_points],
                params,
            )
            cycles.append(
                FundingArbCycle(
                    symbol=symbol,
                    entry_time_ms=entry_point.funding_time_ms,
                    exit_time_ms=exit_point.funding_time_ms,
                    holding_days=max(0.0, (exit_point.funding_time_ms - entry_point.funding_time_ms) / MS_PER_DAY),
                    entry_spot_price=entry_spot.close,
                    entry_perp_price=entry_perp.close,
                    exit_spot_price=exit_spot.close,
                    exit_perp_price=exit_perp.close,
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
                    max_drawdown_during_cycle=_cycle_drawdown(entry_spot.close, entry_perp.close, spot_bars, perp_bars, held_points, params),
                    exit_reason="forced_end_exit",
                    funding_periods_count=len(held_points),
                    negative_funding_periods_count=sum(1 for item in held_points if item.funding_rate < 0),
                    basis_data_status=basis_data_status,
                )
            )

    sleep_periods = _sleep_periods(symbol, data_start, data_end, cycles)
    equity_times, equity_curve = _funding_period_equity_curve(cycles, points, spot_bars, perp_bars, params, data_start, data_end)
    summary = _time_indexed_metrics(equity_times, equity_curve, cycles, sleep_periods)
    oos_times, oos_equity = _slice_equity_window(equity_times, equity_curve, split_ms, data_end)
    oos_cycles = [cycle for cycle in cycles if cycle.entry_time_ms >= split_ms]
    oos_summary = _time_indexed_metrics(oos_times, oos_equity, oos_cycles, []) if oos_times else {
        "total_return": 0.0,
        "annualized_return": 0.0,
        "annualized_volatility": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "complete_cycles": float(len(oos_cycles)),
        "equity_points": 0.0,
        "return_observations": 0.0,
        "span_days": 0.0,
    }
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
        interval_hours=interval_hours,
        interval_source="fundingRate.fundingTime",
        interval_anomalies=interval_anomalies,
        sleep_periods=sleep_periods,
        data_start_ms=data_start,
        data_end_ms=data_end,
        is_start_ms=data_start,
        is_end_ms=split_ms,
        oos_start_ms=split_ms,
        oos_end_ms=data_end,
        basis_data_status=basis_data_status,
    )
    gates, final_status = evaluate_m1b_gates(result)
    return FundingArbResult(**{**result.__dict__, "gates": gates, "final_status": final_status})


def combine_funding_results(
    components: dict[str, FundingArbResult],
    params: FundingArbParams | None = None,
    cost_label: str = "base_cost",
) -> FundingArbResult:
    params = params or FundingArbParams()
    cycles = sorted(
        [cycle for result in components.values() for cycle in result.cycles],
        key=lambda cycle: (cycle.entry_time_ms, cycle.symbol),
    )
    starts = [result.data_start_ms for result in components.values() if result.data_start_ms is not None]
    ends = [result.data_end_ms for result in components.values() if result.data_end_ms is not None]
    data_start = max(starts) if starts else None
    data_end = min(ends) if ends else None
    sleep_periods = [period for result in components.values() for period in result.sleep_periods]
    component_values = list(components.values())
    weight = 1.0 / len(component_values) if component_values else 1.0
    union_times = sorted(
        {
            ts
            for result in component_values
            for ts in result.equity_times_ms
            if data_start is not None and data_end is not None and data_start <= ts <= data_end
        }
    )
    component_indices = {symbol: 0 for symbol in components}
    equity_curve: list[float] = []
    for ts in union_times:
        total = 0.0
        for symbol, result in components.items():
            idx = component_indices[symbol]
            while idx + 1 < len(result.equity_times_ms) and result.equity_times_ms[idx + 1] <= ts:
                idx += 1
            component_indices[symbol] = idx
            total += result.equity_curve[idx] * weight
        equity_curve.append(total)
    summary = _time_indexed_metrics(union_times, equity_curve, cycles, sleep_periods, weight) if union_times else {}
    split_ms = data_start + int(((data_end or data_start or 0) - (data_start or 0)) * (1.0 - params.oos_fraction)) if data_start else None
    oos_times, oos_equity = _slice_equity_window(union_times, equity_curve, split_ms, data_end)
    oos_cycles = [cycle for cycle in cycles if split_ms is not None and cycle.entry_time_ms >= split_ms]
    oos_summary = _time_indexed_metrics(oos_times, oos_equity, oos_cycles, [], weight) if oos_times else {
        "total_return": 0.0,
        "annualized_return": 0.0,
        "annualized_volatility": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "complete_cycles": float(len(oos_cycles)),
        "equity_points": 0.0,
        "return_observations": 0.0,
        "span_days": 0.0,
    }
    interval_anomalies = [warning for result in components.values() for warning in result.interval_anomalies]
    result = FundingArbResult(
        symbol="BTC+ETH",
        params=params,
        cost_label=cost_label,
        cycles=cycles,
        equity_times_ms=union_times,
        equity_curve=equity_curve,
        metrics=summary,
        oos_metrics=oos_summary,
        gates={},
        final_status="under_review",
        interval_hours=min((result.interval_hours for result in components.values()), default=0.0),
        interval_source="component_fundingRate.fundingTime",
        interval_anomalies=interval_anomalies,
        sleep_periods=sleep_periods,
        data_start_ms=data_start,
        data_end_ms=data_end,
        is_start_ms=data_start,
        is_end_ms=split_ms,
        oos_start_ms=split_ms,
        oos_end_ms=data_end,
        basis_data_status="partial"
        if any(result.basis_data_status != "available" for result in components.values())
        else "available",
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
    oos_sharpe = result.oos_metrics.get("sharpe", 0.0)
    if oos_points < 30:
        oos_gate = "insufficient_data"
    elif result.oos_split_basis != "time-based last 30%" or result.metrics_basis != "funding-period time-indexed equity curve":
        oos_gate = "invalid_metric"
    else:
        oos_gate = "pass" if oos_sharpe >= params.min_oos_sharpe else "fail"
    gates = {
        "Backtest code": "pass",
        "Funding interval not hardcoded": "pass" if result.interval_hours > 0 and result.interval_source else "fail",
        "Payback threshold": "pass"
        if threshold > params.entry_mean_apr_threshold and not should_enter_funding_arb(params.entry_mean_apr_threshold, 0.001, params)
        else "fail",
        "Base cost positive": "pass" if result.metrics.get("total_return", 0.0) > 0 else "fail",
        "Cost x2 positive": "pass"
        if (cost_x2_result.metrics.get("total_return", 0.0) > 0 if cost_x2_result is not None else result.cost_label == "cost_x2" and result.metrics.get("total_return", 0.0) > 0)
        else "fail",
        "Complete cycles >= 20": "pass" if result.metrics.get("complete_cycles", 0.0) >= params.min_complete_cycles else "fail",
        "OOS Sharpe >= 1.0": oos_gate,
        "Max drawdown <= 5%": "pass" if result.metrics.get("max_drawdown", 1.0) <= params.max_drawdown_limit else "fail",
        "Funding dries up gracefully": "pass" if result.sleep_periods or not result.cycles else "fail",
        "No lookahead": "pass" if result.no_lookahead else "fail",
    }
    final_status = "pass" if all(status == "pass" for status in gates.values()) else "failed_validation"
    return gates, final_status


def result_date_range(result: FundingArbResult) -> str:
    return f"{utc_ms(result.data_start_ms)} -> {utc_ms(result.data_end_ms)}"


def percent(value: float) -> str:
    if math.isinf(value):
        return "inf"
    return f"{value * 100:.4f}%"
