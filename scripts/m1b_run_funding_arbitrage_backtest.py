#!/usr/bin/env python3
"""Generate the M1B offline funding-arbitrage validation report.

This script reads local M0 public data only. It does not access networks,
secrets, private smoke outputs, or Freqtrade runtime state.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from btc_eth_dual_quant.backtest.funding_arbitrage import (
    FundingArbParams,
    FundingArbResult,
    combine_funding_results,
    compute_payback_required_apr,
    percent,
    result_date_range,
    run_funding_arbitrage_backtest,
    utc_ms,
)
from btc_eth_dual_quant.backtest.m0_data import M0DataUnavailableError, load_funding_history_dicts, load_kline_bars


SYMBOLS = ["BTCUSDT", "ETHUSDT"]


def _metric_line(result: FundingArbResult) -> list[str]:
    metrics = result.metrics
    return [
        f"- total_return: {percent(metrics.get('total_return', 0.0))}",
        f"- annualized_return: {percent(metrics.get('annualized_return', 0.0))}",
        f"- annualized_volatility: {percent(metrics.get('annualized_volatility', 0.0))}",
        f"- sharpe: {metrics.get('sharpe', 0.0):.4f}",
        f"- max_drawdown: {percent(metrics.get('max_drawdown', 0.0))}",
        f"- complete_cycles: {int(metrics.get('complete_cycles', 0.0))}",
        f"- win_rate: {percent(metrics.get('win_rate', 0.0))}",
        f"- profit_factor: {metrics.get('profit_factor', 0.0):.4f}",
        f"- average_holding_days: {metrics.get('average_holding_days', 0.0):.2f}",
        f"- funding_income_total: {metrics.get('funding_income_total', 0.0):.6f}",
        f"- basis_pnl_total: {metrics.get('basis_pnl_total', 0.0):.6f}",
        f"- fees_total: {metrics.get('fees_total', 0.0):.6f}",
        f"- slippage_total: {metrics.get('slippage_total', 0.0):.6f}",
        f"- worst_cycle: {percent(metrics.get('worst_cycle', 0.0))}",
        f"- best_cycle: {percent(metrics.get('best_cycle', 0.0))}",
        f"- longest_sleep_days: {metrics.get('longest_sleep_days', 0.0):.2f}",
        f"- percent_time_in_market: {percent(metrics.get('percent_time_in_market', 0.0))}",
    ]


def _cycle_table(result: FundingArbResult, limit: int = 30) -> list[str]:
    lines = [
        "| symbol | entry UTC | exit UTC | days | net_return | funding | basis | fees | slippage | reason |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for cycle in result.cycles[:limit]:
        lines.append(
            "| "
            f"{cycle.symbol} | {utc_ms(cycle.entry_time_ms)} | {utc_ms(cycle.exit_time_ms)} | "
            f"{cycle.holding_days:.2f} | {percent(cycle.net_return)} | {cycle.funding_income:.6f} | "
            f"{cycle.basis_pnl:.6f} | {cycle.fees:.6f} | {cycle.slippage:.6f} | {cycle.exit_reason} |"
        )
    if len(result.cycles) > limit:
        lines.append(f"| ... | ... | ... | ... | ... | ... | ... | ... | ... | truncated, total cycles={len(result.cycles)} |")
    return lines


def _sleep_table(result: FundingArbResult, limit: int = 20) -> list[str]:
    lines = ["| symbol | start UTC | end UTC | days | reason |", "| --- | --- | --- | ---: | --- |"]
    for period in result.sleep_periods[:limit]:
        lines.append(
            f"| {period.symbol} | {utc_ms(period.start_time_ms)} | {utc_ms(period.end_time_ms)} | {period.days:.2f} | {period.reason} |"
        )
    if len(result.sleep_periods) > limit:
        lines.append(f"| ... | ... | ... | ... | truncated, total sleep periods={len(result.sleep_periods)} |")
    return lines


def _gate_lines(result: FundingArbResult) -> list[str]:
    lines = ["| Gate | Status |", "| --- | --- |"]
    for name, status in result.gates.items():
        lines.append(f"| {name} | {status} |")
    lines.append(f"| Final M1B status | {result.final_status} |")
    return lines


def render_report(
    base_portfolio: FundingArbResult,
    cost_x2_portfolio: FundingArbResult,
    symbol_base: dict[str, FundingArbResult],
    symbol_x2: dict[str, FundingArbResult],
) -> str:
    params = base_portfolio.params
    required_apr = compute_payback_required_apr(params)
    best_cycle = max(base_portfolio.cycles, key=lambda cycle: cycle.net_return, default=None)
    worst_cycle = min(base_portfolio.cycles, key=lambda cycle: cycle.net_return, default=None)
    lines: list[str] = [
        "# M1B Funding Arbitrage Backtest Report",
        "",
        f"- Status: {base_portfolio.final_status}",
        "- Scope: funding-rate-arbitrage offline backtest only",
        "- No live trading",
        "- No paper trading with real API",
        "- No execution/live",
        "- No order placement",
        "- No API trading permissions",
        "- Not investment advice",
        "",
        "## 1. Data Sources",
        "",
        "- spot_klines",
        "- um_futures_klines",
        "- funding_rate_history",
        "- mark_price_klines",
        "- index_price_klines",
        "- premium_index_klines",
        "- Source mode: local M0 public data only",
        "",
        "## 2. Data Range",
        "",
        f"- Portfolio: {result_date_range(base_portfolio)}",
    ]
    for symbol, result in symbol_base.items():
        lines.append(f"- {symbol}: {result_date_range(result)}")
    lines.extend(
        [
            "",
            "## 3. IS/OOS Split",
            "",
            f"- IS start/end: {utc_ms(base_portfolio.is_start_ms)} -> {utc_ms(base_portfolio.is_end_ms)}",
            f"- OOS start/end: {utc_ms(base_portfolio.oos_start_ms)} -> {utc_ms(base_portfolio.oos_end_ms)}",
            "- OOS was not used for parameter selection.",
            "",
            "## 4. Strategy Rules",
            "",
            "- Structure: spot long + USDT perpetual short, equal notional hedge.",
            "- Entry: trailing 3-day funding mean annualized >= 8%, current funding positive, and payback threshold satisfied.",
            "- Exit: trailing 3-day funding mean annualized < 2%, or two consecutive negative funding settlements, or forced final close.",
            "- No leverage expansion, martingale, grid, loss adding, symbol rotation, paper trading, or exchange access.",
            "",
            "## 5. Payback Threshold Calculation",
            "",
            f"- expected_hold_days: {params.expected_hold_days:.0f}",
            f"- roundtrip_cost_base: {percent(params.roundtrip_cost_base)}",
            f"- min_payback_ratio: {params.min_payback_ratio:.1f}",
            f"- required annualized funding APR: {percent(required_apr)}",
            "- 8% annualized funding is rejected by this payback threshold.",
            "",
            "## 6. Cost Assumptions",
            "",
            f"- spot fee per side: {percent(params.spot_fee_per_side)}",
            f"- futures fee per side: {percent(params.futures_fee_per_side)}",
            f"- slippage per leg per fill: {percent(params.slippage_per_leg)}",
            f"- base full roundtrip baseline: {percent(params.roundtrip_cost_base)}",
            "- cost_x2 doubles all modeled fees and slippage.",
            "",
            "## 7. Base Cost Results",
            "",
            *_metric_line(base_portfolio),
            "",
            "## 8. Cost x2 Results",
            "",
            *_metric_line(cost_x2_portfolio),
            "",
            "## 9. BTCUSDT Results",
            "",
            *_metric_line(symbol_base["BTCUSDT"]),
            "",
            "## 10. ETHUSDT Results",
            "",
            *_metric_line(symbol_base["ETHUSDT"]),
            "",
            "## 11. Portfolio Combined Results",
            "",
            f"- BTC+ETH allocation comparison: equal-weight combined cycles={int(base_portfolio.metrics.get('complete_cycles', 0.0))}",
            f"- Base total return: {percent(base_portfolio.metrics.get('total_return', 0.0))}",
            f"- Cost x2 total return: {percent(cost_x2_portfolio.metrics.get('total_return', 0.0))}",
            "",
            "## 12. PnL Decomposition",
            "",
            f"- Funding income contribution: {base_portfolio.metrics.get('funding_income_total', 0.0):.6f}",
            f"- Basis PnL contribution: {base_portfolio.metrics.get('basis_pnl_total', 0.0):.6f}",
            f"- Fees contribution: {-base_portfolio.metrics.get('fees_total', 0.0):.6f}",
            f"- Slippage contribution: {-base_portfolio.metrics.get('slippage_total', 0.0):.6f}",
            f"- Worst cycle: {worst_cycle.symbol + ' ' + percent(worst_cycle.net_return) if worst_cycle else 'n/a'}",
            f"- Best cycle: {best_cycle.symbol + ' ' + percent(best_cycle.net_return) if best_cycle else 'n/a'}",
            "",
            "## 13. Cycle Table",
            "",
            *_cycle_table(base_portfolio),
            "",
            "## 14. Sleep Periods",
            "",
            *_sleep_table(base_portfolio),
            "",
            "## 15. OOS Results",
            "",
            f"- OOS total_return: {percent(base_portfolio.oos_metrics.get('total_return', 0.0))}",
            f"- OOS Sharpe: {base_portfolio.oos_metrics.get('sharpe', 0.0):.4f}",
            f"- OOS complete cycles: {int(base_portfolio.oos_metrics.get('complete_cycles', 0.0))}",
            "",
            "## 16. Funding Interval Diagnostics",
            "",
            f"- Portfolio interval source: {base_portfolio.interval_source}",
            f"- Conservative interval hours used: {base_portfolio.interval_hours:.4f}",
        ]
    )
    for symbol, result in symbol_base.items():
        lines.append(f"- {symbol} interval hours: {result.interval_hours:.4f}; anomalies: {result.interval_anomalies or ['none']}")
    lines.extend(
        [
            f"- Basis data status: {base_portfolio.basis_data_status}",
            "",
            "## 17. Failure / Graceful Sleep Analysis",
            "",
            f"- Funding dries up gracefully gate: {base_portfolio.gates.get('Funding dries up gracefully', 'fail')}",
            f"- Longest no-trade / sleep period: {base_portfolio.metrics.get('longest_sleep_days', 0.0):.2f} days",
            "- If funding is below threshold, the engine remains flat instead of relaxing entry rules.",
            "",
            "## 18. Known Limitations",
            "",
            "- Offline validation only; no execution feasibility is implied.",
            "- Private commission and income payloads are not used.",
            "- Funding settlement mechanics are simplified to equal-notional period-rate accounting.",
            "- Mark/index/premium data are diagnostics; spot and perpetual close prices drive modeled hedge PnL.",
            "",
            "## 19. M1B Gate Status",
            "",
            *_gate_lines(base_portfolio),
            "",
            "## 20. Decision",
            "",
        ]
    )
    if base_portfolio.final_status == "pass":
        lines.append("- Decision: eligible for design review only; not eligible for live trading or M2 approval.")
    else:
        lines.append("- Decision: failed_validation; do not promote funding-rate-arbitrage to execution or paper/live stages.")
    lines.append("- No result in this report approves live trading.")
    lines.append("")
    lines.append("## Cost x2 Symbol Detail")
    lines.append("")
    for symbol, result in symbol_x2.items():
        lines.append(f"### {symbol} cost_x2")
        lines.extend(_metric_line(result))
        lines.append("")
    return "\n".join(lines)


def run_from_local_m0(raw_root: str, duckdb_path: str) -> tuple[FundingArbResult, FundingArbResult, dict[str, FundingArbResult], dict[str, FundingArbResult]]:
    base_params = FundingArbParams(cost_multiplier=1.0)
    x2_params = FundingArbParams(cost_multiplier=2.0)
    base_components: dict[str, FundingArbResult] = {}
    x2_components: dict[str, FundingArbResult] = {}
    for symbol in SYMBOLS:
        spot = load_kline_bars("spot_klines", symbol, raw_root, duckdb_path)
        perp = load_kline_bars("um_futures_klines", symbol, raw_root, duckdb_path)
        try:
            mark = load_kline_bars("mark_price_klines", symbol, raw_root, duckdb_path)
        except (M0DataUnavailableError, ValueError):
            mark = None
        try:
            index = load_kline_bars("index_price_klines", symbol, raw_root, duckdb_path)
        except (M0DataUnavailableError, ValueError):
            index = None
        try:
            premium = load_kline_bars("premium_index_klines", symbol, raw_root, duckdb_path)
        except (M0DataUnavailableError, ValueError):
            premium = None
        funding = load_funding_history_dicts(symbol, raw_root, duckdb_path)
        optional_missing = mark is None or index is None or premium is None
        base_result = run_funding_arbitrage_backtest(symbol, spot, perp, funding, mark, index, premium, base_params)
        x2_result = run_funding_arbitrage_backtest(symbol, spot, perp, funding, mark, index, premium, x2_params)
        if optional_missing:
            base_result = replace(base_result, basis_data_status="basis_data_unavailable")
            x2_result = replace(x2_result, basis_data_status="basis_data_unavailable")
        base_components[symbol] = base_result
        x2_components[symbol] = x2_result
    base = combine_funding_results(base_components, base_params, "base_cost")
    x2 = combine_funding_results(x2_components, x2_params, "cost_x2")
    gates, final_status = __import__(
        "btc_eth_dual_quant.backtest.funding_arbitrage",
        fromlist=["evaluate_m1b_gates"],
    ).evaluate_m1b_gates(base, x2)
    base = replace(base, gates=gates, final_status=final_status)
    return base, x2, base_components, x2_components


def main() -> int:
    parser = argparse.ArgumentParser(description="Run M1B funding-arbitrage offline backtest from local M0 public data.")
    parser.add_argument("--raw-root", default="storage/raw")
    parser.add_argument("--duckdb-path", default="storage/duckdb/m0.duckdb")
    parser.add_argument("--out", default="reports/m1/M1B_FUNDING_ARBITRAGE_BACKTEST_REPORT.md")
    args = parser.parse_args()

    try:
        base, x2, symbol_base, symbol_x2 = run_from_local_m0(args.raw_root, args.duckdb_path)
    except M0DataUnavailableError as exc:
        print(f"M1B report not generated: {exc}")
        return 2

    report = render_report(base, x2, symbol_base, symbol_x2)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Final M1B status: {base.final_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
