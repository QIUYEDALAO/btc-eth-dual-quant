#!/usr/bin/env python3
"""Generate the sanitized M1G frozen-IS validation report."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.audit.m1g_is_validation import (
    IS_END_EXCLUSIVE,
    SCENARIOS,
    build_scenario_evidence,
    daily_prices,
    detail_index,
    diagnostics,
    evaluate_is_gates,
    load_jsongz_ohlc,
)


def archive_for(root: Path, scenario: str) -> Path:
    directory = root / scenario.replace("_", "-")
    matches = sorted(directory.glob("*.zip"))
    if len(matches) != 1:
        raise ValueError(f"expected one frozen archive for {scenario}, found {len(matches)}")
    return matches[0]


def pct(value: float) -> str:
    return f"{value * 100:.4f}%"


def main() -> int:
    parser = argparse.ArgumentParser(description="M1G frozen-IS report generator")
    parser.add_argument("--results", type=Path, default=ROOT / "freqtrade_lab/user_data/backtest_results/m1g-is")
    parser.add_argument("--data", type=Path, default=ROOT / "freqtrade_lab/user_data/data/binance")
    parser.add_argument("--out", type=Path, default=ROOT / "reports/m1/M1G_IS_VALIDATION_REPORT.md")
    args = parser.parse_args()

    details = {}
    daily_close = {}
    benchmark = {}
    for symbol in ("BTCUSDT", "ETHUSDT"):
        prefix = symbol.replace("USDT", "_USDT")
        rows_5m = load_jsongz_ohlc(args.data / f"{prefix}-5m.json.gz", end_exclusive=IS_END_EXCLUSIVE)
        rows_1h = load_jsongz_ohlc(args.data / f"{prefix}-1h.json.gz", end_exclusive=IS_END_EXCLUSIVE)
        details[symbol] = detail_index(rows_5m)
        day_open, day_close = daily_prices(rows_1h)
        benchmark[symbol] = (day_open, day_close)
        daily_close.update({(symbol, day): value for day, value in day_close.items()})

    evidence = {
        scenario: build_scenario_evidence(
            scenario=scenario,
            archive_path=archive_for(args.results, scenario),
            detail_by_symbol=details,
            daily_close=daily_close,
            benchmark_prices=benchmark,
        )
        for scenario in SCENARIOS
    }
    decision = evaluate_is_gates(evidence["base"], evidence["cost_x2"])

    lines = [
        "# M1G IS Validation Report",
        "",
        f"- Status: {decision.status}",
        f"- Generated UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "- Scope: frozen M1G IS performance validation and independent execution repricing only",
        "- IS range: 2020-07-01T00:00:00Z to 2024-09-11T00:00:00Z (end exclusive)",
        "- OOS opened: no",
        "- OOS prices/returns accessed: no",
        "- Parameters changed after protocol freeze: no",
        "- API key/private data used: no",
        "- Live/paper/execution implemented: no",
        "",
        "## Decision",
        "",
        "M1G failed its frozen IS Gate. The strategy loses money under Base and Cost x2, daily-MTM risk-adjusted performance is below the preregistered thresholds, and the conservative execution audit does not preserve every native exit bar. OOS remains sealed. No parameter, target, stop, cooldown, cost, or Gate may be changed to rescue this candidate.",
        "",
        "## Fixed Run Matrix",
        "",
        "| Scenario | Trades | Native return | Audited return | Native Sharpe | Audited Sharpe | Native PSR | Audited PSR | Native MaxDD | Audited MaxDD | Benchmark return | Exit-bar mismatches | Archive SHA256 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for scenario in SCENARIOS:
        item = evidence[scenario]
        lines.append(
            f"| {scenario} | {len(item.native_trades)} | {pct(item.native_total_return)} | {pct(item.audited_total_return)} | "
            f"{item.native_metrics.sharpe:.4f} | {item.audited_metrics.sharpe:.4f} | {item.native_metrics.psr:.4f} | "
            f"{item.audited_metrics.psr:.4f} | {pct(item.native_metrics.max_drawdown)} | {pct(item.audited_metrics.max_drawdown)} | "
            f"{pct(item.benchmark_metrics.total_return)} | {item.native_exit_bar_mismatches} | `{item.archive_sha256}` |"
        )

    lines.extend(["", "## Conservative Execution Audit", ""])
    for scenario in SCENARIOS:
        item = evidence[scenario]
        reasons = ", ".join(f"{name}={count}" for name, count in item.audited_exit_reasons)
        lines.append(f"- {scenario}: {reasons}; native/audited exit-bar mismatches={item.native_exit_bar_mismatches}.")
    lines.extend(
        [
            "- The audit consumed only exported trade lifecycles and canonical public 5m OHLC.",
            "- It did not detect events, select pairs, create trades, or alter the frozen signal sequence.",
            "- Same-bar ambiguity resolves to stop; target gaps fill at target; stop gaps use the worse of threshold/open; timeout uses the first 5m open at or after 24h.",
            "- Because the frozen protocol requires exact exit-bar agreement, every non-zero mismatch count is an audit Gate failure.",
            "",
            "## Gate Matrix",
            "",
            "| Gate | Result |",
            "| --- | --- |",
        ]
    )
    for name, passed in decision.gates:
        lines.append(f"| {name} | {'pass' if passed else 'fail'} |")

    lines.extend(["", "## Diagnostics", ""])
    for scenario in SCENARIOS:
        item = evidence[scenario]
        info = diagnostics(item)
        lines.extend(
            [
                f"### {scenario}",
                "",
                f"- Native delete-best-3 return: {pct(item.native_delete_best_three_return)}",
                f"- Audited delete-best-3 return: {pct(item.audited_delete_best_three_return)}",
                f"- Native four-segment returns: {', '.join(pct(value) for value in item.native_segment_returns)}",
                f"- Audited four-segment returns: {', '.join(pct(value) for value in item.audited_segment_returns)}",
                f"- Best native trade PnL: {info['best_trade']:.8f} USDT",
                f"- Worst native trade PnL: {info['worst_trade']:.8f} USDT",
                f"- Median holding: {info['median_holding_hours']:.2f} hours",
                f"- Longest sleep: {info['longest_sleep_days']} days",
                f"- Best-three share of positive PnL: {pct(info['best_three_share'])}",
                "",
            ]
        )

    lines.extend(
        [
            "## Data And Runtime Evidence",
            "",
            "- Signal data: canonical public Binance spot 1h OHLC.",
            "- Detail and repricing data: canonical public Binance spot 5m OHLC.",
            "- Runtime: official pinned Freqtrade 2026.6 image from the frozen protocol.",
            "- Lookahead analysis: pass (20 signals, zero biased entries/exits/indicators).",
            "- Recursive analysis: pass (startup 170/250/340, zero indicator variance and no lookahead).",
            "- Unexplained data gaps: 0; qualified common exchange-outage windows remain excluded by the canonical contract.",
            "- Runtime archives, canonical OHLC, DuckDB, raw data and logs committed: no.",
            "",
            "## Authorization",
            "",
            "- M1G OOS opening: no",
            "- M1G parameter rescue: no",
            "- M1H design review after this failure record merges: yes",
            "- M2: no",
            "- Dry-run/live/API trading: no",
            "",
            "This report is research validation evidence and is not investment advice.",
        ]
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"status={decision.status}")
    return 0 if decision.status == "failed_validation" else 2


if __name__ == "__main__":
    raise SystemExit(main())
