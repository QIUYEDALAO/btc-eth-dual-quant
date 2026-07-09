#!/usr/bin/env python3
"""Generate strict event-time M1B revalidation from local M0 public data."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from btc_eth_dual_quant.backtest.funding_arbitrage import (
    FundingArbParams,
    FundingArbResult,
    combine_funding_results,
    compute_payback_required_apr,
    evaluate_m1b_gates,
    percent,
    result_date_range,
    run_funding_arbitrage_backtest,
    utc_ms,
)
from btc_eth_dual_quant.backtest.trend_strategy import TrendBar
from btc_eth_dual_quant.backtest.m0_data import (
    M0DataIndexError,
    M0DataUnavailableError,
    load_funding_history_dicts,
    load_kline_bars,
)


SYMBOLS = ("BTCUSDT", "ETHUSDT")
DATA_INTERVAL = "1h"
HOUR_MS = 3_600_000
FREQTRADE_FUTURES_PROBE_STATUS = "blocked_network"
FREQTRADE_FUTURES_PROBE_RUN = "29049892500"


def _strict_hourly_profile(bars: list[TrendBar]) -> tuple[list[TrendBar], dict[str, int]]:
    valid = [
        bar
        for bar in bars
        if abs((bar.close_time_ms - bar.open_time_ms) - (HOUR_MS - 1)) <= 1_000
    ]
    gaps = sum(
        1
        for left, right in zip(valid, valid[1:])
        if right.open_time_ms - left.open_time_ms != HOUR_MS
    )
    return valid, {
        "raw_rows": len(bars),
        "valid_completed_1h_rows": len(valid),
        "invalid_close_boundary_rows": len(bars) - len(valid),
        "observed_gap_boundaries": gaps,
    }


def _metric_lines(result: FundingArbResult) -> list[str]:
    metrics = result.metrics
    return [
        f"- total_return: {percent(metrics.get('total_return', 0.0))}",
        f"- annualized_return: {percent(metrics.get('annualized_return', 0.0))}",
        f"- annualized_volatility: {percent(metrics.get('annualized_volatility', 0.0))}",
        f"- sharpe: {metrics.get('sharpe', 0.0):.4f}",
        f"- max_drawdown: {percent(metrics.get('max_drawdown', 0.0))}",
        f"- complete_cycles: {int(metrics.get('complete_cycles', 0.0))}",
        f"- incomplete_positions: {int(metrics.get('incomplete_positions', 0.0))}",
        f"- funding_income_total: {metrics.get('funding_income_total', 0.0):.8f}",
        f"- basis_pnl_total: {metrics.get('basis_pnl_total', 0.0):.8f}",
        f"- fees_total: {metrics.get('fees_total', 0.0):.8f}",
        f"- slippage_total: {metrics.get('slippage_total', 0.0):.8f}",
        f"- worst_cycle: {percent(metrics.get('worst_cycle', 0.0))}",
        f"- best_cycle: {percent(metrics.get('best_cycle', 0.0))}",
        f"- longest_sleep_days: {metrics.get('longest_sleep_days', 0.0):.2f}",
    ]


def _cycle_table(result: FundingArbResult, limit: int = 40) -> list[str]:
    lines = [
        "| symbol | entry signal UTC | entry open UTC | exit signal UTC | exit open UTC | funding events | funding | basis | fees | slippage | net return | reason |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for cycle in result.cycles[:limit]:
        lines.append(
            "| "
            f"{cycle.symbol} | {utc_ms(cycle.entry_signal_time_ms)} | {utc_ms(cycle.entry_time_ms)} | "
            f"{utc_ms(cycle.exit_signal_time_ms)} | {utc_ms(cycle.exit_time_ms)} | "
            f"{cycle.funding_periods_count} | {cycle.funding_income:.8f} | {cycle.basis_pnl:.8f} | "
            f"{cycle.fees:.8f} | {cycle.slippage:.8f} | {percent(cycle.net_return)} | {cycle.exit_reason} |"
        )
    if len(result.cycles) > limit:
        lines.append(f"| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | total={len(result.cycles)} |")
    return lines


def _funding_table(result: FundingArbResult, limit: int = 50) -> list[str]:
    contributions = [
        (cycle.symbol, item)
        for cycle in result.cycles
        for item in cycle.funding_contributions
    ]
    lines = [
        "| symbol | settlement UTC | interval hours | rate | mark | perp quantity | income | mark bar close UTC |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for symbol, item in contributions[:limit]:
        lines.append(
            f"| {symbol} | {utc_ms(item.funding_time_ms)} | {item.interval_hours:.4f} | "
            f"{item.funding_rate:.8f} | {item.settlement_mark_price:.8f} | "
            f"{item.perpetual_quantity:.12f} | {item.income:.8f} | "
            f"{utc_ms(item.valuation_bar_close_time_ms)} |"
        )
    if len(contributions) > limit:
        lines.append(f"| ... | ... | ... | ... | ... | ... | ... | truncated, total={len(contributions)} |")
    return lines


def _gate_table(result: FundingArbResult) -> list[str]:
    lines = ["| Gate | Status |", "| --- | --- |"]
    lines.extend(f"| {name} | {status} |" for name, status in result.gates.items())
    lines.append(f"| Final M1B status | {result.final_status} |")
    return lines


def render_report(
    base_portfolio: FundingArbResult,
    cost_x2_portfolio: FundingArbResult,
    symbol_base: dict[str, FundingArbResult],
    symbol_x2: dict[str, FundingArbResult],
) -> str:
    params = base_portfolio.params
    failed = [f"{name}={status}" for name, status in base_portfolio.gates.items() if status != "pass"]
    lines: list[str] = [
        "# M1B Event-Time Revalidation Report",
        "",
        f"- Status: {base_portfolio.final_status}",
        "- Scope: funding-rate-arbitrage offline event-time revalidation only",
        "- Historical report remains unchanged and invalidated for future approval",
        "- No live trading",
        "- No paper trading with real API",
        "- No execution/live",
        "- No order placement or cancellation",
        "- No API key or private data",
        "- This report does not approve M2",
        "- Not investment advice",
        "",
        "## Data Authority",
        "",
        "- Source: local M0 append-only public data",
        "- Required profile: BTCUSDT and ETHUSDT 1h spot, UM perpetual, mark, index, premium, plus funding history",
        "- M0 audit status: audit_revalidation_required; source-level ZIP/REST blockers remain separate",
        "- Freqtrade role: futures short/funding framework smoke only; not the two-leg portfolio truth",
        f"- Freqtrade futures-leg probe: {FREQTRADE_FUTURES_PROBE_STATUS} "
        f"(GitHub run {FREQTRADE_FUTURES_PROBE_RUN}; Binance exchangeInfo returned HTTP 451)",
        "- No Freqtrade futures backtest result or funding-fee output is claimed from the blocked run.",
        f"- Portfolio range: {result_date_range(base_portfolio)}",
    ]
    for symbol, result in symbol_base.items():
        lines.append(f"- {symbol} range: {result_date_range(result)}")
    lines.extend(
        [
            "",
            "## Event-Time Contract",
            "",
            "- A funding event at T becomes visible only at T.",
            "- Entry uses the first common spot/perpetual 1h open strictly after T.",
            "- The triggering funding event is excluded from funding income.",
            "- While held, funding at T is credited using the latest mark bar with close_time <= T.",
            "- Exit signals are evaluated after the held-position funding at T and execute at the next common 1h open.",
            "- The low-funding exit requires the trailing mean to remain below 2% APR for three consecutive days.",
            "- Positions without a legal exit price at data end are incomplete and do not count as complete cycles.",
            "",
            "## Fixed Rules And Costs",
            "",
            f"- expected_hold_days: {params.expected_hold_days:.0f}",
            f"- roundtrip_cost_base: {percent(params.roundtrip_cost_base)}",
            f"- min_payback_ratio: {params.min_payback_ratio:.1f}",
            f"- payback-required APR: {percent(compute_payback_required_apr(params))}",
            "- 8% APR alone is rejected by the payback gate.",
            "- Fees use actual entry and exit notionals for spot and perpetual fills.",
            "- Slippage is charged separately on all four fill directions.",
            "",
            "## Base Cost Portfolio",
            "",
            *_metric_lines(base_portfolio),
            "",
            "## Cost X2 Portfolio",
            "",
            *_metric_lines(cost_x2_portfolio),
        ]
    )
    for symbol in SYMBOLS:
        lines.extend(
            [
                "",
                f"## {symbol}",
                "",
                *_metric_lines(symbol_base[symbol]),
                f"- cost_x2_total_return: {percent(symbol_x2[symbol].metrics.get('total_return', 0.0))}",
                f"- interval_distribution: {symbol_base[symbol].interval_distribution}",
                f"- interval_warnings: {symbol_base[symbol].interval_anomalies or ['none']}",
                f"- diagnostics_status: {symbol_base[symbol].basis_data_status}",
                f"- mark/index/premium diagnostics: {symbol_base[symbol].diagnostics}",
            ]
        )
    lines.extend(
        [
            "",
            "## Complete Cycles",
            "",
            *_cycle_table(base_portfolio),
            "",
            "## Funding Contributions",
            "",
            *_funding_table(base_portfolio),
            "",
            "## Incomplete Positions",
            "",
            f"- count: {len(base_portfolio.incomplete_positions)}",
        ]
    )
    for item in base_portfolio.incomplete_positions:
        lines.append(
            f"- {item.symbol}: entry={utc_ms(item.entry_time_ms)}, last_event={utc_ms(item.last_event_time_ms)}, "
            f"funding_periods={item.funding_periods_count}, reason={item.reason}"
        )
    lines.extend(
        [
            "",
            "## OOS",
            "",
            f"- split: {utc_ms(base_portfolio.oos_start_ms)}",
            f"- OOS total return: {percent(base_portfolio.oos_metrics.get('total_return', 0.0))}",
            f"- OOS Sharpe: {base_portfolio.oos_metrics.get('sharpe', 0.0):.4f}",
            f"- OOS complete cycles: {int(base_portfolio.oos_metrics.get('complete_cycles', 0.0))}",
            f"- OOS carry-in cycles: {int(base_portfolio.oos_metrics.get('carry_in_cycles', 0.0))}",
            "- Carry-in positions are reported separately and excluded from OOS complete-cycle count.",
            "",
            "## UTC Portfolio Alignment",
            "",
            f"- diagnostics: {base_portfolio.diagnostics}",
            "- BTC and ETH component equity are joined only by UTC timestamps.",
            "",
            "## Freqtrade Cross-Check Boundary",
            "",
            "- Freqtrade 2026.6 remains the primary single-leg research framework.",
            "- A futures-only short/funding smoke may cross-check the perpetual leg.",
            "- The prepared public futures probe passed local schema/static validation but its hosted run was blocked by Binance HTTP 451 before market data loaded.",
            "- Freqtrade does not provide the native combined spot-long plus perpetual-short portfolio truth.",
            "- No two-bot workaround is treated as proof because leg synchronization and reconciliation remain external.",
            "",
            "## Gates",
            "",
            *_gate_table(base_portfolio),
            "",
            "## Decision",
            "",
            f"- Failed or blocked numerical gates: {', '.join(failed) if failed else 'none'}",
            f"- Final M1B status: {base_portfolio.final_status}",
            "- Even if every numerical gate passes, the maximum automatic status is under_review.",
            "- M1A and historical M1B remain failed_validation.",
            "- No strategy is eligible for M2.",
            "- No result here approves live trading, paper trading, API permissions, or execution.",
            "",
            "## Known Limitations",
            "",
            "- Public market data cannot model real two-leg fill synchronization, margin failures, or reconciliation incidents.",
            "- M0 audit source discrepancies remain unresolved independently of this accounting correction.",
            "- Freqtrade futures output is a single-leg smoke and is not substituted for two-leg accounting.",
            "- The current hosted environment produced no futures-leg backtest output because public market metadata was region-blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_from_local_m0(
    raw_root: str,
    duckdb_path: str,
) -> tuple[FundingArbResult, FundingArbResult, dict[str, FundingArbResult], dict[str, FundingArbResult]]:
    base_params = FundingArbParams(cost_multiplier=1.0)
    x2_params = FundingArbParams(cost_multiplier=2.0)
    base_components: dict[str, FundingArbResult] = {}
    x2_components: dict[str, FundingArbResult] = {}
    for symbol in SYMBOLS:
        loaded = {
            dataset: load_kline_bars(dataset, symbol, raw_root, duckdb_path, interval=DATA_INTERVAL)
            for dataset in (
                "spot_klines",
                "um_futures_klines",
                "mark_price_klines",
                "index_price_klines",
                "premium_index_klines",
            )
        }
        inputs: dict[str, list[TrendBar]] = {}
        input_quality: dict[str, dict[str, int]] = {}
        for dataset, bars in loaded.items():
            inputs[dataset], input_quality[dataset] = _strict_hourly_profile(bars)
        funding = load_funding_history_dicts(symbol, raw_root, duckdb_path)
        ordered = (
            inputs["spot_klines"],
            inputs["um_futures_klines"],
            funding,
            inputs["mark_price_klines"],
            inputs["index_price_klines"],
            inputs["premium_index_klines"],
        )
        base_result = run_funding_arbitrage_backtest(symbol, *ordered, base_params)
        x2_result = run_funding_arbitrage_backtest(symbol, *ordered, x2_params)
        has_quality_issues = any(
            profile["invalid_close_boundary_rows"] or profile["observed_gap_boundaries"]
            for profile in input_quality.values()
        )
        base_components[symbol] = replace(
            base_result,
            basis_data_status="partial" if has_quality_issues else base_result.basis_data_status,
            diagnostics={**base_result.diagnostics, "input_quality": input_quality},
        )
        x2_components[symbol] = replace(
            x2_result,
            basis_data_status="partial" if has_quality_issues else x2_result.basis_data_status,
            diagnostics={**x2_result.diagnostics, "input_quality": input_quality},
        )
    base = combine_funding_results(base_components, base_params, "base_cost")
    cost_x2 = combine_funding_results(x2_components, x2_params, "cost_x2")
    gates, final_status = evaluate_m1b_gates(base, cost_x2)
    base = replace(base, gates=gates, final_status=final_status)
    return base, cost_x2, base_components, x2_components


def main() -> int:
    parser = argparse.ArgumentParser(description="Run strict M1B event-time revalidation from local M0 public data.")
    parser.add_argument("--raw-root", default="storage/raw")
    parser.add_argument("--duckdb-path", default="storage/duckdb/m0.duckdb")
    parser.add_argument("--out", default="reports/m1/M1B_EVENT_TIME_REVALIDATION_REPORT.md")
    args = parser.parse_args()
    try:
        base, cost_x2, symbol_base, symbol_x2 = run_from_local_m0(args.raw_root, args.duckdb_path)
    except (M0DataUnavailableError, M0DataIndexError, ValueError) as exc:
        print(f"M1B event-time report not generated: {exc}")
        return 2
    report = render_report(base, cost_x2, symbol_base, symbol_x2)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Final M1B status: {base.final_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
