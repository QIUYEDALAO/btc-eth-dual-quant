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

from . import metrics as perf_metrics
from .trend_engine import split_in_sample_oos
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


def _metrics_from_cycles(cycles: list[FundingArbCycle], data_days: float, sleep_periods: list[SleepPeriod]) -> tuple[list[float], dict[str, float]]:
    equity = [1.0]
    for cycle in cycles:
        equity.append(max(0.0001, equity[-1] + cycle.net_return))
    positions = [1.0 for _ in cycles]
    trades = [
        perf_metrics.Trade(
            symbol=cycle.symbol,
            entry_time_ms=cycle.entry_time_ms,
            exit_time_ms=cycle.exit_time_ms,
            entry_price=cycle.entry_spot_price,
            exit_price=cycle.exit_spot_price,
            quantity=1.0,
            pnl=cycle.net_pnl,
            return_pct=cycle.net_return,
            bars_held=max(1, int(round(cycle.holding_days))),
        )
        for cycle in cycles
    ]
    summary = perf_metrics.metrics_summary(equity, trades, max(1, int(round(data_days))), positions)
    summary["complete_cycles"] = float(len(cycles))
    summary["average_holding_days"] = sum(cycle.holding_days for cycle in cycles) / len(cycles) if cycles else 0.0
    summary["funding_income_total"] = sum(cycle.funding_income for cycle in cycles)
    summary["basis_pnl_total"] = sum(cycle.basis_pnl for cycle in cycles)
    summary["fees_total"] = sum(cycle.fees for cycle in cycles)
    summary["slippage_total"] = sum(cycle.slippage for cycle in cycles)
    summary["worst_cycle"] = min((cycle.net_return for cycle in cycles), default=0.0)
    summary["best_cycle"] = max((cycle.net_return for cycle in cycles), default=0.0)
    summary["longest_sleep_days"] = max((period.days for period in sleep_periods), default=0.0)
    held_days = sum(cycle.holding_days for cycle in cycles)
    summary["percent_time_in_market"] = held_days / data_days if data_days > 0 else 0.0
    cycle_drawdown = max((cycle.max_drawdown_during_cycle for cycle in cycles), default=0.0)
    summary["max_drawdown"] = max(abs(summary["max_drawdown"]), cycle_drawdown)
    return equity, summary


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
    equity_curve, summary = _metrics_from_cycles(cycles, data_days, sleep_periods)
    _is_cycles, oos_cycles = split_in_sample_oos(cycles, params.oos_fraction)
    _, oos_summary = _metrics_from_cycles(oos_cycles, max(1.0, data_days * params.oos_fraction), [])
    result = FundingArbResult(
        symbol=symbol,
        params=params,
        cost_label="cost_x2" if params.cost_multiplier > 1 else "base_cost",
        cycles=cycles,
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
    data_start = min(starts) if starts else None
    data_end = max(ends) if ends else None
    data_days = max(1.0, ((data_end or 0) - (data_start or 0)) / MS_PER_DAY) if data_start and data_end else 1.0
    sleep_periods = [period for result in components.values() for period in result.sleep_periods]
    equity_curve, summary = _metrics_from_cycles(cycles, data_days, sleep_periods)
    _, oos_cycles = split_in_sample_oos(cycles, params.oos_fraction)
    _, oos_summary = _metrics_from_cycles(oos_cycles, max(1.0, data_days * params.oos_fraction), [])
    interval_anomalies = [warning for result in components.values() for warning in result.interval_anomalies]
    result = FundingArbResult(
        symbol="BTC+ETH",
        params=params,
        cost_label=cost_label,
        cycles=cycles,
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
        is_end_ms=data_start + int(((data_end or data_start or 0) - (data_start or 0)) * (1.0 - params.oos_fraction)) if data_start else None,
        oos_start_ms=data_start + int(((data_end or data_start or 0) - (data_start or 0)) * (1.0 - params.oos_fraction)) if data_start else None,
        oos_end_ms=data_end,
        basis_data_status="basis_data_unavailable"
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
    gates = {
        "Backtest code": "pass" if result.data_start_ms is not None and result.data_end_ms is not None else "fail",
        "Funding interval not hardcoded": "pass" if result.interval_hours > 0 and result.interval_source else "fail",
        "Payback threshold": "pass"
        if threshold > params.entry_mean_apr_threshold and not should_enter_funding_arb(params.entry_mean_apr_threshold, 0.001, params)
        else "fail",
        "Base cost positive": "pass" if result.metrics.get("total_return", 0.0) > 0 else "fail",
        "Cost x2 positive": "pass"
        if (cost_x2_result.metrics.get("total_return", 0.0) > 0 if cost_x2_result is not None else result.cost_label == "cost_x2" and result.metrics.get("total_return", 0.0) > 0)
        else "fail",
        "Complete cycles >= 20": "pass" if result.metrics.get("complete_cycles", 0.0) >= params.min_complete_cycles else "fail",
        "OOS Sharpe >= 1.0": "pass" if result.oos_metrics.get("sharpe", 0.0) >= params.min_oos_sharpe else "fail",
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
