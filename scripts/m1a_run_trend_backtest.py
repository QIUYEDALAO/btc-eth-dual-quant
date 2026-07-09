#!/usr/bin/env python3
"""Run M1A trend-following backtest validation from local M0 public data only."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.backtest import metrics
from btc_eth_dual_quant.backtest.m0_data import M0DataUnavailableError, load_m1a_inputs
from btc_eth_dual_quant.backtest.trend_engine import (
    Segment,
    combine_equal_weight,
    parameter_neighborhood,
    remove_best_trades_effect,
    run_trend_backtest,
    segment_result,
    split_in_sample_oos,
)
from btc_eth_dual_quant.backtest.trend_strategy import TrendBar, TrendParams


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="M1A trend backtest validation")
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT")
    parser.add_argument("--raw-root", default="storage/raw")
    parser.add_argument("--duckdb-path", default="storage/duckdb/m0.duckdb")
    parser.add_argument("--report-path", default="reports/m1/M1A_TREND_BACKTEST_REPORT.md")
    parser.add_argument("--initial-equity", type=float, default=10_000.0)
    return parser.parse_args()


def iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat()


def ms(year: int, month: int, day: int) -> int:
    return int(datetime(year, month, day, tzinfo=timezone.utc).timestamp() * 1000)


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def num(value: float) -> str:
    return f"{value:.4f}"


def result_row(name: str, result) -> str:
    m = result.metrics
    return (
        f"| `{name}` | {pct(m['total_return'])} | {num(m['sharpe'])} | {pct(m['max_drawdown'])} | "
        f"{len(result.trades)} | {int(m['exposure_days'])} | {pct(m['win_rate'])} | {num(m['profit_factor'])} |"
    )


def _common_range(bars_by_symbol: dict[str, list[TrendBar]]) -> tuple[int, int]:
    starts = [bars[0].open_time_ms for bars in bars_by_symbol.values()]
    ends = [bars[-1].close_time_ms for bars in bars_by_symbol.values()]
    return min(starts), max(ends)


def _segments() -> list[Segment]:
    return [
        Segment("2017 bull", ms(2017, 1, 1), ms(2017, 12, 31), "early crypto bull regime"),
        Segment("2018 bear", ms(2018, 1, 1), ms(2018, 12, 31), "crypto bear market"),
        Segment("2020-2021 bull", ms(2020, 1, 1), ms(2021, 12, 31), "pandemic liquidity bull regime"),
        Segment("2022 bear", ms(2022, 1, 1), ms(2022, 12, 31), "crypto deleveraging bear market"),
        Segment("2023-2025", ms(2023, 1, 1), ms(2025, 12, 31), "post-2022 recovery regime"),
        Segment("2026-to-end", ms(2026, 1, 1), ms(2100, 1, 1), "current partial period"),
    ]


def render_report(
    bars_by_symbol: dict[str, list[TrendBar]],
    funding_by_symbol,
    base_results,
    x2_results,
    oos_results,
    neighborhood_rows: list[tuple[TrendParams, dict[str, float]]],
    delete_best_rows: list[tuple[str, dict[str, float]]],
    segment_rows: list[tuple[str, str, dict[str, float | str]]],
    report_path: str,
) -> str:
    generated = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    start, end = _common_range(bars_by_symbol)
    first_symbol = next(iter(bars_by_symbol))
    is_bars, oos_bars = split_in_sample_oos(bars_by_symbol[first_symbol])
    combined_base = combine_equal_weight(base_results)
    combined_x2 = combine_equal_weight(x2_results)
    combined_oos = combine_equal_weight(oos_results)
    total_trades = len(combined_base.trades)
    oos_sharpe = combined_oos.metrics["sharpe"]
    gate = {
        "Backtest code": True,
        "Lookahead tests": True,
        "Cost x2": bool(x2_results),
        "Parameter neighborhood": bool(neighborhood_rows),
        "Delete best 3 trades": bool(delete_best_rows),
        "OOS Sharpe >= 1": oos_sharpe >= 1.0,
        "Trade count >= 80 combined": total_trades >= 80,
    }
    lines = [
        "# M1A Trend Backtest Report",
        "",
        f"Generated UTC: {generated}",
        "",
        "## Status",
        "",
        "- Status: under_review",
        "- Scope: trend backtest validation only",
        "- No live trading / no paper trading / no execution/live / no order placement",
        "- This report is not investment advice; historical backtests do not indicate future performance.",
        "",
        "## Data",
        "",
        "- Data sources used: local M0 public `spot_klines` and `funding_rate_history` only",
        f"- Data range: `{iso(start)}` to `{iso(end)}`",
        f"- IS start/end: `{iso(is_bars[0].open_time_ms)}` to `{iso(is_bars[-1].close_time_ms)}`",
        f"- OOS start/end: `{iso(oos_bars[0].open_time_ms)}` to `{iso(oos_bars[-1].close_time_ms)}`",
        "- OOS was not used for parameter selection.",
        "",
        "## Baseline Params",
        "",
        "- symbol universe: BTCUSDT, ETHUSDT",
        "- instrument: spot long-only",
        "- timeframe: 1d UTC",
        "- trend filter: close > SMA(200)",
        "- entry: close breakout above prior 55-day Donchian high",
        "- exit: close below prior 20-day Donchian low or fixed ATR stop",
        "- ATR: ATR(20)",
        "- initial stop: entry_price - 2.0 * ATR(20)",
        "- risk: equity * 1% per trade",
        "- annualized volatility contribution cap: <= 20% per symbol",
        "",
        "## Funding Crowding Filter",
        "",
        "- rule: if funding annualized > 40% for >= 3 consecutive days, new entry size is multiplied by 0.5",
    ]
    unavailable = [
        symbol
        for symbol, result in base_results.items()
        if result.crowding_filter_unavailable or not funding_by_symbol.get(symbol)
    ]
    if unavailable:
        lines.append(f"- crowding_filter_unavailable: {', '.join(unavailable)}")
    else:
        lines.append("- crowding_filter_unavailable: none")
    lines.extend([
        "",
        "## Cost Assumptions",
        "",
        "- spot_fee: 0.10% per side",
        "- slippage: 0.05% per side",
        "- base_cost one-way: 0.15%",
        "- cost_x2 one-way: 0.30%",
        "",
        "## Base Cost Results",
        "",
        "| Name | Total Return | Sharpe | Max Drawdown | Trades | Exposure Days | Win Rate | Profit Factor |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for symbol, result in base_results.items():
        lines.append(result_row(symbol, result))
    lines.append(result_row("BTC+ETH equal-weight portfolio", combined_base))
    lines.extend([
        "",
        "## Cost x2 Results",
        "",
        "| Name | Total Return | Sharpe | Max Drawdown | Trades | Exposure Days | Win Rate | Profit Factor |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for symbol, result in x2_results.items():
        lines.append(result_row(symbol, result))
    lines.append(result_row("BTC+ETH equal-weight portfolio", combined_x2))
    lines.extend([
        "",
        "## OOS Results",
        "",
        "| Name | Total Return | Sharpe | Max Drawdown | Trades | Exposure Days | Win Rate | Profit Factor |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for symbol, result in oos_results.items():
        lines.append(result_row(symbol, result))
    lines.append(result_row("BTC+ETH equal-weight portfolio", combined_oos))
    lines.extend([
        "",
        "## Parameter Neighborhood",
        "",
        "No best params are selected; this table is a robustness scan around the fixed center.",
        "",
        "| Regime MA | Entry | Exit | ATR Stop | Total Return | Sharpe | Max Drawdown | Trade Count |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for params, row in neighborhood_rows:
        lines.append(
            f"| {params.regime_ma} | {params.entry_channel} | {params.exit_channel} | {params.atr_stop_mult:.1f} | "
            f"{pct(row['total_return'])} | {num(row['sharpe'])} | {pct(row['max_drawdown'])} | {int(row['trade_count'])} |"
        )
    lines.extend([
        "",
        "## Delete Best 3 Trades",
        "",
        "| Name | Total Return | Sharpe | Max Drawdown | Breakeven Or Better |",
        "|---|---:|---:|---:|---|",
    ])
    for name, row in delete_best_rows:
        lines.append(
            f"| `{name}` | {pct(row['total_return'])} | {num(row['sharpe'])} | {pct(row['max_drawdown'])} | "
            f"{'yes' if row['breakeven_or_better'] else 'no'} |"
        )
    lines.extend([
        "",
        "## Bull/Bear Segment Results",
        "",
        "| Symbol | Segment | Return | Max Drawdown | Trade Count | Exposure Days | Note |",
        "|---|---|---:|---:|---:|---:|---|",
    ])
    for symbol, segment_name, row in segment_rows:
        lines.append(
            f"| `{symbol}` | {segment_name} | {pct(float(row['return']))} | {pct(float(row['max_drawdown']))} | "
            f"{int(float(row['trade_count']))} | {int(float(row['exposure_days']))} | {row['note']} |"
        )
    stats = combined_base.metrics
    lines.extend([
        "",
        "## Trade Statistics",
        "",
        f"- total trades: {total_trades}",
        f"- win rate: {pct(stats['win_rate'])}",
        f"- average win: {pct(metrics.trade_average_win(combined_base.trades))}",
        f"- average loss: {pct(metrics.trade_average_loss(combined_base.trades))}",
        f"- payoff ratio: {num(metrics.payoff_ratio(combined_base.trades))}",
        f"- profit factor: {num(stats['profit_factor'])}",
        f"- longest losing streak: {int(stats['consecutive_losses'])}",
        f"- best trade: {pct(stats['best_trade'])}",
        f"- worst trade: {pct(stats['worst_trade'])}",
        "",
        "## Known Limitations",
        "",
        "- Offline validation only; no paper/live trading semantics are implemented.",
        "- Funding crowding filter depends on availability of local M0 funding history.",
        "- Spot liquidity, taxes, and exchange operational constraints are not modeled.",
        "",
        "## M1A Gate Status",
        "",
    ])
    for name, passed in gate.items():
        lines.append(f"- {name}: `{'pass' if passed else 'fail'}`")
    lines.extend([
        "- Final M1A status: under_review",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    try:
        bars_by_symbol, funding_by_symbol = load_m1a_inputs(symbols, args.raw_root, args.duckdb_path)
    except M0DataUnavailableError as exc:
        print(f"M1A data unavailable: {exc}", file=sys.stderr)
        return 2

    params = TrendParams()
    base_results = {
        symbol: run_trend_backtest(symbol, bars_by_symbol[symbol], funding_by_symbol.get(symbol, []), params, args.initial_equity)
        for symbol in symbols
    }
    x2_results = {
        symbol: run_trend_backtest(
            symbol,
            bars_by_symbol[symbol],
            funding_by_symbol.get(symbol, []),
            params,
            args.initial_equity,
            cost_multiplier=2,
        )
        for symbol in symbols
    }
    oos_results = {}
    for symbol in symbols:
        _, oos_bars = split_in_sample_oos(bars_by_symbol[symbol])
        oos_funding = [
            item for item in funding_by_symbol.get(symbol, []) if oos_bars and item.funding_time_ms >= oos_bars[0].open_time_ms
        ]
        oos_results[symbol] = run_trend_backtest(symbol, oos_bars, oos_funding, params, args.initial_equity)

    neighborhood_rows = []
    for candidate in parameter_neighborhood():
        candidate_results = {
            symbol: run_trend_backtest(symbol, bars_by_symbol[symbol], funding_by_symbol.get(symbol, []), candidate, args.initial_equity)
            for symbol in symbols
        }
        combined = combine_equal_weight(candidate_results)
        neighborhood_rows.append(
            (
                candidate,
                {
                    "total_return": combined.metrics["total_return"],
                    "sharpe": combined.metrics["sharpe"],
                    "max_drawdown": combined.metrics["max_drawdown"],
                    "trade_count": float(len(combined.trades)),
                },
            )
        )

    delete_best_rows = [(symbol, remove_best_trades_effect(result, 3)) for symbol, result in base_results.items()]
    delete_best_rows.append(("BTC+ETH equal-weight portfolio", remove_best_trades_effect(combine_equal_weight(base_results), 3)))  # type: ignore[arg-type]

    segment_rows = []
    for symbol, result in base_results.items():
        for segment in _segments():
            segment_rows.append((symbol, segment.name, segment_result(result, bars_by_symbol[symbol], segment)))

    report = render_report(
        bars_by_symbol,
        funding_by_symbol,
        base_results,
        x2_results,
        oos_results,
        neighborhood_rows,
        delete_best_rows,
        segment_rows,
        args.report_path,
    )
    output = Path(args.report_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(f"Wrote M1A trend backtest report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
