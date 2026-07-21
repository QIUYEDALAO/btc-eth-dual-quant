"""Unified daily-MTM measurement primitives for independent research audits.

This module consumes completed trade evidence and public price marks. It does
not create signals, select parameters, or provide execution behavior.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from statistics import NormalDist
from typing import Any, Iterable, Mapping, Sequence


ANNUALIZATION_DAYS = 365


@dataclass(frozen=True)
class EquityPoint:
    day: date
    equity: float


@dataclass(frozen=True)
class WeeklyGrossTrace:
    rebalance_day: date
    gross_exposure: float
    candidate_volatility: float | None
    shadow_benchmark_volatility: float | None
    history_start: date | None
    history_end: date | None


@dataclass(frozen=True)
class ActiveUniverseBenchmarkAudit:
    equity: tuple[EquityPoint, ...]
    shadow_equity: tuple[EquityPoint, ...]
    weekly_gross_trace: tuple[WeeklyGrossTrace, ...]


@dataclass(frozen=True)
class UnifiedMetrics:
    observations: int
    total_return: float
    cagr: float
    annualized_volatility: float
    sharpe: float
    max_drawdown: float
    sortino: float
    calmar: float
    psr: float
    daily_skew: float
    daily_kurtosis: float


@dataclass(frozen=True)
class AuditTrade:
    pair: str
    open_time: datetime
    close_time: datetime
    stake_amount: float
    open_rate: float
    close_rate: float
    profit_abs: float
    fee_open_rate: float = 0.0
    fee_close_rate: float = 0.0
    slippage_open_rate: float = 0.0
    slippage_close_rate: float = 0.0

    @property
    def symbol(self) -> str:
        return self.pair.replace("/", "").split(":", 1)[0]

    @property
    def liquidation_factor(self) -> float:
        entry = 1.0 + self.fee_open_rate + self.slippage_open_rate
        exit_factor = 1.0 - self.fee_close_rate - self.slippage_close_rate
        if entry <= 0 or exit_factor <= 0:
            raise ValueError("trade costs imply a non-positive liquidation factor")
        return exit_factor / entry


@dataclass(frozen=True)
class CostAttribution:
    entry_fees: float
    exit_fees: float
    entry_slippage: float
    exit_slippage: float
    total: float


@dataclass(frozen=True)
class FrequencyDiagnostics:
    complete_trades: int
    trades_per_30_days: float
    trades_per_365_days: float
    median_duration_hours: float
    p95_duration_hours: float
    longest_sleep_days: int
    turnover: float
    p95_daily_order_events: float
    p99_daily_order_events: float
    p999_daily_order_events: float


@dataclass(frozen=True)
class ConcentrationDiagnostics:
    positive_profit_total: float
    best_three_profit: float
    best_three_share: float
    positive_profit_hhi: float


@dataclass(frozen=True)
class GranularityResult:
    gate_consistent: bool
    trade_count_difference: float
    sharpe_difference: float
    drawdown_difference: float
    ending_equity_difference: float
    passed: bool


def _sample_std(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _population_moment(values: Sequence[float], order: int) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((value - mean) ** order for value in values) / len(values)


def validate_daily_curve(points: Sequence[EquityPoint]) -> None:
    if len(points) < 2:
        raise ValueError("daily equity curve requires at least two points")
    for previous, current in zip(points, points[1:]):
        if current.day != previous.day + timedelta(days=1):
            raise ValueError("daily equity curve must contain every consecutive UTC day")
    if any(not math.isfinite(point.equity) or point.equity <= 0 for point in points):
        raise ValueError("daily equity values must be finite and positive")


def daily_returns(points: Sequence[EquityPoint]) -> list[float]:
    validate_daily_curve(points)
    return [current.equity / previous.equity - 1.0 for previous, current in zip(points, points[1:])]


def probabilistic_sharpe_ratio(returns: Sequence[float], benchmark_daily_sharpe: float = 0.0) -> float:
    if len(returns) < 2:
        return 0.0
    std_sample = _sample_std(returns)
    std_population = math.sqrt(_population_moment(returns, 2))
    if std_sample == 0 or std_population == 0:
        return 0.0
    mean = sum(returns) / len(returns)
    daily_sharpe = mean / std_sample
    skew = _population_moment(returns, 3) / std_population**3
    kurtosis = _population_moment(returns, 4) / std_population**4
    variance_term = 1 - skew * daily_sharpe + ((kurtosis - 1) / 4) * daily_sharpe**2
    z = (daily_sharpe - benchmark_daily_sharpe) * math.sqrt(len(returns) - 1) / math.sqrt(max(variance_term, 1e-12))
    return NormalDist().cdf(z)


def expected_maximum_sharpe(annualized_trial_sharpes: Sequence[float]) -> float:
    """Return the Bailey/Lopez de Prado expected maximum annualized Sharpe."""
    if len(annualized_trial_sharpes) <= 1:
        return 0.0
    trial_std = _sample_std(annualized_trial_sharpes)
    if trial_std == 0:
        return 0.0
    count = len(annualized_trial_sharpes)
    gamma = 0.5772156649015329
    normal = NormalDist()
    first = normal.inv_cdf(1 - 1 / count)
    second = normal.inv_cdf(1 - 1 / (count * math.e))
    return trial_std * ((1 - gamma) * first + gamma * second)


def deflated_sharpe_ratio(returns: Sequence[float], annualized_trial_sharpes: Sequence[float]) -> float:
    benchmark_annualized = expected_maximum_sharpe(annualized_trial_sharpes)
    return probabilistic_sharpe_ratio(returns, benchmark_annualized / math.sqrt(ANNUALIZATION_DAYS))


def metrics_from_equity(points: Sequence[EquityPoint]) -> UnifiedMetrics:
    returns = daily_returns(points)
    mean = sum(returns) / len(returns)
    std = _sample_std(returns)
    annualized_volatility = std * math.sqrt(ANNUALIZATION_DAYS)
    sharpe = mean / std * math.sqrt(ANNUALIZATION_DAYS) if std else 0.0
    downside = math.sqrt(sum(min(value, 0.0) ** 2 for value in returns) / len(returns))
    sortino = mean / downside * math.sqrt(ANNUALIZATION_DAYS) if downside else 0.0
    peak = points[0].equity
    max_drawdown = 0.0
    for point in points:
        peak = max(peak, point.equity)
        max_drawdown = max(max_drawdown, (peak - point.equity) / peak)
    days = len(points) - 1
    total_return = points[-1].equity / points[0].equity - 1.0
    cagr = (points[-1].equity / points[0].equity) ** (ANNUALIZATION_DAYS / days) - 1.0
    calmar = cagr / max_drawdown if max_drawdown else 0.0
    population_std = math.sqrt(_population_moment(returns, 2))
    skew = _population_moment(returns, 3) / population_std**3 if population_std else 0.0
    kurtosis = _population_moment(returns, 4) / population_std**4 if population_std else 0.0
    return UnifiedMetrics(
        observations=len(points),
        total_return=total_return,
        cagr=cagr,
        annualized_volatility=annualized_volatility,
        sharpe=sharpe,
        max_drawdown=max_drawdown,
        sortino=sortino,
        calmar=calmar,
        psr=probabilistic_sharpe_ratio(returns),
        daily_skew=skew,
        daily_kurtosis=kurtosis,
    )


def trade_from_freqtrade(payload: Mapping[str, Any]) -> AuditTrade:
    def timestamp(name: str) -> datetime:
        raw = str(payload.get(name, ""))
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    return AuditTrade(
        pair=str(payload["pair"]),
        open_time=timestamp("open_date"),
        close_time=timestamp("close_date"),
        stake_amount=float(payload["stake_amount"]),
        open_rate=float(payload["open_rate"]),
        close_rate=float(payload["close_rate"]),
        profit_abs=float(payload["profit_abs"]),
        fee_open_rate=float(payload.get("fee_open", 0.0)),
        fee_close_rate=float(payload.get("fee_close", 0.0)),
        slippage_open_rate=float(payload.get("slippage_open", 0.0)),
        slippage_close_rate=float(payload.get("slippage_close", 0.0)),
    )


def build_daily_mtm_equity(
    *,
    trades: Sequence[AuditTrade],
    daily_close: Mapping[tuple[str, date], float],
    start: date,
    end: date,
    initial_equity: float,
) -> list[EquityPoint]:
    if end < start or initial_equity <= 0:
        raise ValueError("invalid MTM range or initial equity")
    ordered = sorted(trades, key=lambda item: (item.open_time, item.close_time, item.pair))
    if any(trade.open_time.date() < start or trade.close_time.date() > end for trade in ordered):
        raise ValueError("trade crosses the fresh-capital MTM evaluation boundary")
    if any(trade.close_time < trade.open_time for trade in ordered):
        raise ValueError("trade close must not precede open")

    by_pair: dict[str, list[AuditTrade]] = {}
    for item in ordered:
        by_pair.setdefault(item.pair, []).append(item)
    for pair, pair_trades in by_pair.items():
        for previous, current in zip(pair_trades, pair_trades[1:]):
            if current.open_time < previous.close_time:
                raise ValueError(f"overlapping trades for the same pair: {pair}")

    # Half-open intervals mean a close and a new open at the same instant do
    # not overlap.  Close events therefore sort before open events.
    duration_trades = [item for item in ordered if item.close_time > item.open_time]
    events = sorted(
        [(item.open_time, 1, item.pair) for item in duration_trades]
        + [(item.close_time, -1, item.pair) for item in duration_trades],
        key=lambda value: (value[0], value[1], value[2]),
    )
    open_count = 0
    for _, delta, _ in events:
        open_count += delta
        if open_count > 5:
            raise ValueError("more than five concurrent positions")
        if open_count < 0:
            raise ValueError("invalid position event ordering")

    points: list[EquityPoint] = []
    closed_profit_by_day: dict[date, float] = {}
    for item in ordered:
        closed_profit_by_day[item.close_time.date()] = closed_profit_by_day.get(item.close_time.date(), 0.0) + item.profit_abs
    realized_equity = initial_equity
    current_day = start
    while current_day <= end:
        realized_equity += closed_profit_by_day.get(current_day, 0.0)
        active = [
            item for item in ordered
            if item.open_time.date() <= current_day < item.close_time.date()
        ]
        equity = realized_equity
        for item in active:
            mark = daily_close.get((item.symbol, current_day))
            if mark is None or mark <= 0:
                raise ValueError(f"missing positive daily mark for {item.symbol}:{current_day}")
            equity += item.stake_amount * (
                (float(mark) / item.open_rate) * item.liquidation_factor - 1.0
            )
        points.append(EquityPoint(current_day, equity))
        current_day += timedelta(days=1)
    validate_daily_curve(points)
    return points


def build_policy_benchmark(
    *,
    btc_open: Mapping[date, float],
    btc_close: Mapping[date, float],
    eth_open: Mapping[date, float],
    eth_close: Mapping[date, float],
    start: date,
    end: date,
    initial_equity: float,
    cost_per_side: float,
) -> list[EquityPoint]:
    if initial_equity <= 0 or not 0 <= cost_per_side < 1:
        raise ValueError("invalid benchmark capital or cost")
    cash = initial_equity
    btc_quantity = 0.0
    eth_quantity = 0.0
    invested = False
    points: list[EquityPoint] = []
    day = start
    while day <= end:
        prices = (btc_open.get(day), btc_close.get(day), eth_open.get(day), eth_close.get(day))
        if any(value is None or float(value) <= 0 for value in prices):
            raise ValueError(f"missing benchmark OHLC price for {day}")
        btc_o, btc_c, eth_o, eth_c = (float(value) for value in prices)
        if day.weekday() == 0:
            pre_trade_equity = cash + btc_quantity * btc_o + eth_quantity * eth_o
            target_btc = pre_trade_equity * 0.25 / btc_o
            target_eth = pre_trade_equity * 0.25 / eth_o
            turnover = abs(target_btc - btc_quantity) * btc_o + abs(target_eth - eth_quantity) * eth_o
            cash = pre_trade_equity - target_btc * btc_o - target_eth * eth_o - turnover * cost_per_side
            btc_quantity, eth_quantity = target_btc, target_eth
            invested = True
        equity = cash + btc_quantity * btc_c + eth_quantity * eth_c if invested else cash
        points.append(EquityPoint(day, equity))
        day += timedelta(days=1)
    validate_daily_curve(points)
    return points


def build_active_universe_benchmark(
    *,
    daily_open: Mapping[tuple[str, date], float],
    daily_close: Mapping[tuple[str, date], float],
    active_universe: Mapping[date, Sequence[str]],
    start: date,
    end: date,
    initial_equity: float,
    cost_per_side: float,
    maximum_gross_exposure: float = 0.50,
    candidate_daily_returns: Mapping[date, float] | None = None,
    risk_match_lookback_days: int = 90,
) -> list[EquityPoint]:
    """Build the ADR-0016 prior-only active-universe benchmark.

    With ``candidate_daily_returns`` omitted this is the 50%-gross equal-weight
    benchmark.  With it supplied, Monday gross is scaled from the preceding 90
    complete UTC days and remains cash-only until both histories are complete.
    Missing authority or price inputs fail closed; membership is never filled.
    """
    return list(build_active_universe_benchmark_audit(
        daily_open=daily_open,
        daily_close=daily_close,
        active_universe=active_universe,
        start=start,
        end=end,
        initial_equity=initial_equity,
        cost_per_side=cost_per_side,
        maximum_gross_exposure=maximum_gross_exposure,
        candidate_daily_returns=candidate_daily_returns,
        risk_match_lookback_days=risk_match_lookback_days,
    ).equity)


def _benchmark_pass(
    *,
    daily_open: Mapping[tuple[str, date], float],
    daily_close: Mapping[tuple[str, date], float],
    active_universe: Mapping[date, Sequence[str]],
    start: date,
    end: date,
    initial_equity: float,
    cost_per_side: float,
    gross_by_monday: Mapping[date, float],
) -> tuple[EquityPoint, ...]:
    cash = initial_equity
    quantities: dict[str, float] = {}
    points: list[EquityPoint] = []
    day = start
    while day <= end:
        members = tuple(sorted(active_universe.get(day, ())))
        if not members:
            raise ValueError(f"missing point-in-time active universe for {day}")
        # A lifecycle/membership exit is executed at the day's open before a
        # possible Monday rebalance.  Consequently an exited asset needs an
        # open, but never a same-day close.  This ordering also prevents the
        # exit from being charged a second time by the rebalance turnover.
        held_symbols = set(quantities)
        open_symbols = held_symbols | (set(members) if day.weekday() == 0 else set())
        open_prices = {symbol: float(daily_open.get((symbol, day), 0.0)) for symbol in open_symbols}
        if any(value <= 0 or not math.isfinite(value) for value in open_prices.values()):
            raise ValueError(f"missing eligible benchmark open for {day}")
        for symbol in sorted(set(quantities) - set(members)):
            cash += quantities.pop(symbol) * open_prices[symbol] * (1.0 - cost_per_side)
        if day.weekday() == 0:
            pre_trade_equity = cash + sum(quantity * open_prices[symbol] for symbol, quantity in quantities.items())
            gross = gross_by_monday[day]
            target_notional = pre_trade_equity * gross / len(members)
            target_quantities = {symbol: target_notional / open_prices[symbol] for symbol in members}
            turnover = sum(
                abs(target_quantities.get(symbol, 0.0) - quantities.get(symbol, 0.0)) * open_prices[symbol]
                for symbol in set(target_quantities) | set(quantities)
            )
            cash = pre_trade_equity - target_notional * len(members) - turnover * cost_per_side
            quantities = target_quantities
        close_prices = {symbol: float(daily_close.get((symbol, day), 0.0)) for symbol in quantities}
        if any(value <= 0 or not math.isfinite(value) for value in close_prices.values()):
            raise ValueError(f"missing eligible benchmark close for {day}")
        points.append(EquityPoint(day, cash + sum(quantity * close_prices[symbol] for symbol, quantity in quantities.items())))
        day += timedelta(days=1)
    validate_daily_curve(points)
    return tuple(points)


def build_active_universe_benchmark_audit(
    *,
    daily_open: Mapping[tuple[str, date], float],
    daily_close: Mapping[tuple[str, date], float],
    active_universe: Mapping[date, Sequence[str]],
    start: date,
    end: date,
    initial_equity: float,
    cost_per_side: float,
    maximum_gross_exposure: float = 0.50,
    candidate_daily_returns: Mapping[date, float] | None = None,
    risk_match_lookback_days: int = 90,
) -> ActiveUniverseBenchmarkAudit:
    """Return benchmark equity plus the immutable weekly gross audit trace.

    The volatility denominator is always derived from an independently built
    fixed-50%-gross shadow curve.  It never feeds back from the risk-matched
    curve being constructed.
    """
    if end < start or initial_equity <= 0 or not 0 <= cost_per_side < 1:
        raise ValueError("invalid active-universe benchmark contract")
    if not 0 <= maximum_gross_exposure <= 1 or risk_match_lookback_days != 90:
        raise ValueError("invalid benchmark gross cap or lookback")
    mondays = [start + timedelta(days=offset) for offset in range((end - start).days + 1) if (start + timedelta(days=offset)).weekday() == 0]
    shadow_gross = {day: maximum_gross_exposure for day in mondays}
    shadow = _benchmark_pass(
        daily_open=daily_open, daily_close=daily_close, active_universe=active_universe,
        start=start, end=end, initial_equity=initial_equity, cost_per_side=cost_per_side,
        gross_by_monday=shadow_gross,
    )
    shadow_returns = {point.day: value for point, value in zip(shadow[1:], daily_returns(shadow))}
    gross_by_monday: dict[date, float] = {}
    trace: list[WeeklyGrossTrace] = []
    for day in mondays:
        candidate_vol: float | None = None
        shadow_vol: float | None = None
        history_start: date | None = None
        history_end: date | None = None
        gross = maximum_gross_exposure
        if candidate_daily_returns is not None:
            prior_days = [day - timedelta(days=offset) for offset in range(risk_match_lookback_days, 0, -1)]
            candidate_window = [candidate_daily_returns.get(item) for item in prior_days]
            shadow_window = [shadow_returns.get(item) for item in prior_days]
            if any(value is None or not math.isfinite(float(value)) for value in candidate_window + shadow_window):
                gross = 0.0
            else:
                history_start, history_end = prior_days[0], prior_days[-1]
                candidate_vol = _sample_std([float(value) for value in candidate_window])
                shadow_vol = _sample_std([float(value) for value in shadow_window])
                gross = 0.0 if shadow_vol == 0 else min(maximum_gross_exposure, maximum_gross_exposure * candidate_vol / shadow_vol)
        gross_by_monday[day] = gross
        trace.append(WeeklyGrossTrace(day, gross, candidate_vol, shadow_vol, history_start, history_end))
    equity = _benchmark_pass(
        daily_open=daily_open, daily_close=daily_close, active_universe=active_universe,
        start=start, end=end, initial_equity=initial_equity, cost_per_side=cost_per_side,
        gross_by_monday=gross_by_monday,
    )
    return ActiveUniverseBenchmarkAudit(equity, shadow, tuple(trace))


def cost_attribution(trades: Iterable[AuditTrade]) -> CostAttribution:
    entry_fees = exit_fees = entry_slippage = exit_slippage = 0.0
    for trade in trades:
        exit_notional = trade.stake_amount * trade.close_rate / trade.open_rate
        entry_fees += trade.stake_amount * trade.fee_open_rate
        exit_fees += exit_notional * trade.fee_close_rate
        entry_slippage += trade.stake_amount * trade.slippage_open_rate
        exit_slippage += exit_notional * trade.slippage_close_rate
    total = entry_fees + exit_fees + entry_slippage + exit_slippage
    return CostAttribution(entry_fees, exit_fees, entry_slippage, exit_slippage, total)


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def frequency_diagnostics(trades: Sequence[AuditTrade], start: date, end: date, initial_equity: float) -> FrequencyDiagnostics:
    days = (end - start).days + 1
    durations = [(trade.close_time - trade.open_time).total_seconds() / 3600 for trade in trades]
    ordered = sorted(trades, key=lambda item: item.open_time)
    sleeps = [
        max(0, (current.open_time.date() - previous.close_time.date()).days)
        for previous, current in zip(ordered, ordered[1:])
    ]
    if ordered:
        sleeps.extend(
            [
                max(0, (ordered[0].open_time.date() - start).days),
                max(0, (end - ordered[-1].close_time.date()).days),
            ]
        )
    turnover = sum(
        trade.stake_amount + trade.stake_amount * trade.close_rate / trade.open_rate for trade in trades
    ) / initial_equity if initial_equity > 0 else 0.0
    daily_events: dict[date, int] = {
        start + timedelta(days=offset): 0 for offset in range(days)
    }
    for trade in trades:
        if trade.open_time.date() in daily_events:
            daily_events[trade.open_time.date()] += 1
        if trade.close_time.date() in daily_events:
            daily_events[trade.close_time.date()] += 1
    event_counts = list(daily_events.values())
    return FrequencyDiagnostics(
        complete_trades=len(trades),
        trades_per_30_days=len(trades) * 30 / days if days else 0.0,
        trades_per_365_days=len(trades) * 365 / days if days else 0.0,
        median_duration_hours=_percentile(durations, 0.5),
        p95_duration_hours=_percentile(durations, 0.95),
        longest_sleep_days=max(sleeps, default=days),
        turnover=turnover,
        p95_daily_order_events=_percentile(event_counts, 0.95),
        p99_daily_order_events=_percentile(event_counts, 0.99),
        p999_daily_order_events=_percentile(event_counts, 0.999),
    )


def concentration_diagnostics(trades: Sequence[AuditTrade]) -> ConcentrationDiagnostics:
    positives = sorted((trade.profit_abs for trade in trades if trade.profit_abs > 0), reverse=True)
    total = sum(positives)
    best_three = sum(positives[:3])
    shares = [value / total for value in positives] if total else []
    return ConcentrationDiagnostics(total, best_three, best_three / total if total else 0.0, sum(value**2 for value in shares))


def compare_granularity(
    *,
    reference_metrics: UnifiedMetrics,
    candidate_metrics: UnifiedMetrics,
    reference_trades: int,
    candidate_trades: int,
    reference_gate: bool,
    candidate_gate: bool,
) -> GranularityResult:
    trade_difference = abs(candidate_trades - reference_trades) / max(reference_trades, 1)
    sharpe_difference = abs(candidate_metrics.sharpe - reference_metrics.sharpe)
    drawdown_difference = abs(candidate_metrics.max_drawdown - reference_metrics.max_drawdown)
    ending_difference = abs(candidate_metrics.total_return - reference_metrics.total_return) / max(
        abs(1 + reference_metrics.total_return), 1e-12
    )
    gate_consistent = reference_gate == candidate_gate
    passed = gate_consistent and trade_difference <= 0.05 and sharpe_difference <= 0.15 and drawdown_difference <= 0.02 and ending_difference <= 0.05
    return GranularityResult(gate_consistent, trade_difference, sharpe_difference, drawdown_difference, ending_difference, passed)
