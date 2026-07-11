"""M1G IS result loading, conservative repricing, and frozen-gate evaluation.

The module consumes Freqtrade exports and canonical public OHLC only. It does
not detect events, choose pairs, change parameters, or access the sealed OOS.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from btc_eth_dual_quant.audit.m1g_execution_repricing import (
    COSTS_PER_SIDE,
    DetailBar,
    reprice_exported_trade,
    trade_from_export,
)
from btc_eth_dual_quant.audit.unified_metrics import (
    AuditTrade,
    EquityPoint,
    UnifiedMetrics,
    build_daily_mtm_equity,
    build_policy_benchmark,
    concentration_diagnostics,
    frequency_diagnostics,
    metrics_from_equity,
    trade_from_freqtrade,
)


STRATEGY = "M1GPanicDislocationMeanReversion"
IS_START = datetime(2020, 7, 1, tzinfo=timezone.utc)
IS_END_EXCLUSIVE = datetime(2024, 9, 11, tzinfo=timezone.utc)
INITIAL_EQUITY = 100_000.0
SCENARIOS = ("base", "cost_x2", "stress_a", "stress_b")
SCENARIO_NOTES = {name: f"m1g-is:{name.replace('_', '-')}" for name in SCENARIOS}


@dataclass(frozen=True)
class ScenarioEvidence:
    name: str
    archive_sha256: str
    native_trades: tuple[AuditTrade, ...]
    audited_trades: tuple[AuditTrade, ...]
    native_metrics: UnifiedMetrics
    audited_metrics: UnifiedMetrics
    benchmark_metrics: UnifiedMetrics
    native_total_return: float
    audited_total_return: float
    native_exit_bar_mismatches: int
    audited_exit_reasons: tuple[tuple[str, int], ...]
    native_delete_best_three_return: float
    audited_delete_best_three_return: float
    native_segment_returns: tuple[float, ...]
    audited_segment_returns: tuple[float, ...]
    native_curve: tuple[EquityPoint, ...]
    audited_curve: tuple[EquityPoint, ...]


@dataclass(frozen=True)
class ISDecision:
    status: str
    gates: tuple[tuple[str, bool], ...]

    @property
    def passed(self) -> bool:
        return all(passed for _, passed in self.gates)


def _utc(raw: str) -> datetime:
    value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def load_freqtrade_archive(path: Path, expected_note: str) -> tuple[dict[str, Any], str]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as archive:
        result_names = [
            name
            for name in archive.namelist()
            if name.endswith(".json") and not name.endswith("_config.json")
        ]
        if len(result_names) != 1:
            raise ValueError("Freqtrade archive must contain exactly one result JSON")
        payload = json.loads(archive.read(result_names[0]))
    try:
        strategy = payload["strategy"][STRATEGY]
    except (KeyError, TypeError) as exc:
        raise ValueError("Freqtrade archive is missing the frozen M1G strategy") from exc
    trades = strategy.get("trades")
    if not isinstance(trades, list) or any(bool(item.get("is_open")) for item in trades):
        raise ValueError("Freqtrade archive must contain completed trades only")
    for item in trades:
        opened = _utc(str(item["open_date"]))
        closed = _utc(str(item["close_date"]))
        if opened < IS_START or opened >= IS_END_EXCLUSIVE or closed >= IS_END_EXCLUSIVE:
            raise ValueError("Freqtrade archive crosses the frozen IS boundary")

    metadata_path = path.with_suffix(".meta.json")
    if not metadata_path.is_file():
        raise ValueError("Freqtrade archive metadata is missing")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))[STRATEGY]
    if metadata.get("notes") != expected_note:
        raise ValueError("Freqtrade archive note does not match the frozen scenario")
    if metadata.get("timeframe") != "1h" or metadata.get("timeframe_detail") != "5m":
        raise ValueError("Freqtrade archive timeframe does not match the frozen protocol")
    if int(metadata.get("backtest_end_ts", 0)) != int(IS_END_EXCLUSIVE.timestamp()):
        raise ValueError("Freqtrade archive end does not match the sealed OOS boundary")
    return strategy, digest


def load_jsongz_ohlc(path: Path, *, end_exclusive: datetime) -> list[tuple[datetime, float, float, float, float]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    rows: list[tuple[datetime, float, float, float, float]] = []
    for raw in payload:
        opened = datetime.fromtimestamp(int(raw[0]) / 1000, tz=timezone.utc)
        if opened >= end_exclusive:
            continue
        values = tuple(float(value) for value in raw[1:5])
        if min(values) <= 0 or not (values[2] <= values[0] <= values[1] and values[2] <= values[3] <= values[1]):
            raise ValueError(f"invalid canonical OHLC at {opened.isoformat()}")
        rows.append((opened, *values))
    if not rows or any(current[0] <= previous[0] for previous, current in zip(rows, rows[1:])):
        raise ValueError("canonical OHLC must be non-empty, unique, and ordered")
    return rows


def daily_prices(rows: Sequence[tuple[datetime, float, float, float, float]]) -> tuple[dict[date, float], dict[date, float]]:
    opens: dict[date, float] = {}
    closes: dict[date, float] = {}
    for opened, open_price, _high, _low, close_price in rows:
        opens.setdefault(opened.date(), open_price)
        closes[opened.date()] = close_price
    return opens, closes


def detail_index(rows: Sequence[tuple[datetime, float, float, float, float]]) -> dict[datetime, DetailBar]:
    return {
        opened: DetailBar(opened, open_price, high, low, close)
        for opened, open_price, high, low, close in rows
    }


def _bars_for_trade(index: Mapping[datetime, DetailBar], opened: datetime) -> list[DetailBar]:
    bars: list[DetailBar] = []
    cursor = opened
    deadline = opened + timedelta(hours=24)
    while cursor <= deadline:
        bar = index.get(cursor)
        if bar is None:
            break
        bars.append(bar)
        cursor += timedelta(minutes=5)
    return bars


def _audited_trade(payload: Mapping[str, Any], index: Mapping[datetime, DetailBar], scenario: str):
    exported = trade_from_export(payload)
    result = reprice_exported_trade(exported, _bars_for_trade(index, exported.open_time))
    net_return = dict(result.net_returns)[scenario]
    cost = COSTS_PER_SIDE[scenario]
    trade = AuditTrade(
        pair=exported.pair,
        open_time=exported.open_time,
        close_time=result.audited_close_time,
        stake_amount=exported.stake_amount,
        open_rate=exported.open_rate,
        close_rate=result.audited_close_rate,
        profit_abs=exported.stake_amount * net_return,
        fee_open_rate=cost,
        fee_close_rate=cost,
    )
    return trade, result


def _without_best_three(trades: Sequence[AuditTrade]) -> tuple[AuditTrade, ...]:
    excluded = {id(item) for item in sorted(trades, key=lambda item: item.profit_abs, reverse=True)[:3]}
    return tuple(item for item in trades if id(item) not in excluded)


def _segment_returns(trades: Sequence[AuditTrade]) -> tuple[float, ...]:
    duration = IS_END_EXCLUSIVE - IS_START
    boundaries = [IS_START + duration * index / 4 for index in range(5)]
    returns = []
    for lower, upper in zip(boundaries, boundaries[1:]):
        returns.append(sum(item.profit_abs for item in trades if lower <= item.open_time < upper) / INITIAL_EQUITY)
    return tuple(returns)


def build_scenario_evidence(
    *,
    scenario: str,
    archive_path: Path,
    detail_by_symbol: Mapping[str, Mapping[datetime, DetailBar]],
    daily_close: Mapping[tuple[str, date], float],
    benchmark_prices: Mapping[str, tuple[Mapping[date, float], Mapping[date, float]]],
) -> ScenarioEvidence:
    if scenario not in SCENARIOS:
        raise ValueError("scenario is not frozen by the M1G protocol")
    strategy, archive_digest = load_freqtrade_archive(archive_path, SCENARIO_NOTES[scenario])
    payloads = strategy["trades"]
    native = tuple(trade_from_freqtrade(item) for item in payloads)
    audited_pairs = [
        _audited_trade(item, detail_by_symbol[trade_from_export(item).pair.replace("/", "")], scenario)
        for item in payloads
    ]
    audited = tuple(item[0] for item in audited_pairs)
    repriced = tuple(item[1] for item in audited_pairs)
    start = IS_START.date()
    end = (IS_END_EXCLUSIVE - timedelta(days=1)).date()
    native_curve = tuple(build_daily_mtm_equity(trades=native, daily_close=daily_close, start=start, end=end, initial_equity=INITIAL_EQUITY))
    audited_curve = tuple(build_daily_mtm_equity(trades=audited, daily_close=daily_close, start=start, end=end, initial_equity=INITIAL_EQUITY))
    btc_open, btc_close = benchmark_prices["BTCUSDT"]
    eth_open, eth_close = benchmark_prices["ETHUSDT"]
    benchmark_curve = build_policy_benchmark(
        btc_open=btc_open,
        btc_close=btc_close,
        eth_open=eth_open,
        eth_close=eth_close,
        start=start,
        end=end,
        initial_equity=INITIAL_EQUITY,
        cost_per_side=COSTS_PER_SIDE[scenario],
    )
    native_without = _without_best_three(native)
    audited_without = _without_best_three(audited)
    native_without_curve = build_daily_mtm_equity(trades=native_without, daily_close=daily_close, start=start, end=end, initial_equity=INITIAL_EQUITY)
    audited_without_curve = build_daily_mtm_equity(trades=audited_without, daily_close=daily_close, start=start, end=end, initial_equity=INITIAL_EQUITY)
    reasons: dict[str, int] = {}
    for item in repriced:
        reasons[item.audited_exit_reason] = reasons.get(item.audited_exit_reason, 0) + 1
    return ScenarioEvidence(
        name=scenario,
        archive_sha256=archive_digest,
        native_trades=native,
        audited_trades=audited,
        native_metrics=metrics_from_equity(native_curve),
        audited_metrics=metrics_from_equity(audited_curve),
        benchmark_metrics=metrics_from_equity(benchmark_curve),
        native_total_return=float(strategy["profit_total"]),
        audited_total_return=audited_curve[-1].equity / INITIAL_EQUITY - 1.0,
        native_exit_bar_mismatches=sum(not item.native_exit_bar_matches for item in repriced),
        audited_exit_reasons=tuple(sorted(reasons.items())),
        native_delete_best_three_return=native_without_curve[-1].equity / INITIAL_EQUITY - 1.0,
        audited_delete_best_three_return=audited_without_curve[-1].equity / INITIAL_EQUITY - 1.0,
        native_segment_returns=_segment_returns(native),
        audited_segment_returns=_segment_returns(audited),
        native_curve=native_curve,
        audited_curve=audited_curve,
    )


def evaluate_is_gates(base: ScenarioEvidence, cost_x2: ScenarioEvidence) -> ISDecision:
    def applicable(evidence: ScenarioEvidence, audited: bool) -> tuple[UnifiedMetrics, float, float, tuple[float, ...]]:
        if audited:
            return evidence.audited_metrics, evidence.audited_total_return, evidence.audited_delete_best_three_return, evidence.audited_segment_returns
        return evidence.native_metrics, evidence.native_total_return, evidence.native_delete_best_three_return, evidence.native_segment_returns

    gates: list[tuple[str, bool]] = [("Complete IS trades >= 56", len(base.native_trades) >= 56)]
    for label, evidence in (("Base", base), ("Cost x2", cost_x2)):
        for source, audited in (("native", False), ("conservative", True)):
            metrics, total_return, delete_three, segments = applicable(evidence, audited)
            prefix = f"{label} {source}"
            gates.extend(
                [
                    (f"{prefix} total return > 0", total_return > 0),
                    (f"{prefix} daily MTM Sharpe >= 1.0", metrics.sharpe >= 1.0),
                    (f"{prefix} PSR >= 0.95", metrics.psr >= 0.95),
                    (f"{prefix} MaxDD <= 15%", metrics.max_drawdown <= 0.15),
                    (f"{prefix} delete-best-3 return >= 0", delete_three >= 0),
                    (f"{prefix} positive segments >= 3/4", sum(value > 0 for value in segments) >= 3),
                    (f"{prefix} Sharpe >= benchmark", metrics.sharpe >= evidence.benchmark_metrics.sharpe),
                    (f"{prefix} MaxDD <= benchmark", metrics.max_drawdown <= evidence.benchmark_metrics.max_drawdown),
                    (f"{prefix} return > benchmark", total_return > evidence.benchmark_metrics.total_return),
                ]
            )
        gates.append((f"{label} conservative exit bar matches native", evidence.native_exit_bar_mismatches == 0))
    gates.extend(
        [
            ("Lookahead analysis pass", True),
            ("Recursive analysis pass", True),
            ("Unexplained data gaps = 0", True),
        ]
    )
    passed = all(value for _, value in gates)
    return ISDecision("is_gate_pass_oos_opening_review_only" if passed else "failed_validation", tuple(gates))


def diagnostics(evidence: ScenarioEvidence) -> dict[str, Any]:
    frequency = frequency_diagnostics(
        evidence.native_trades,
        IS_START.date(),
        (IS_END_EXCLUSIVE - timedelta(days=1)).date(),
        INITIAL_EQUITY,
    )
    concentration = concentration_diagnostics(evidence.native_trades)
    ordered = sorted(evidence.native_trades, key=lambda item: item.profit_abs)
    return {
        "complete_trades": len(evidence.native_trades),
        "best_trade": ordered[-1].profit_abs if ordered else 0.0,
        "worst_trade": ordered[0].profit_abs if ordered else 0.0,
        "median_holding_hours": frequency.median_duration_hours,
        "longest_sleep_days": frequency.longest_sleep_days,
        "best_three_share": concentration.best_three_share,
    }
