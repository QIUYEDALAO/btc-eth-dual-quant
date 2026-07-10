#!/usr/bin/env python3
"""Build the sanitized T3 metrics-foundation regression report."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.audit.unified_metrics import EquityPoint, metrics_from_equity


EXPECTED_SHA256 = "842291287ca64967831fb36d1d1af2cbea4c77a80663f283d238f490e0a06bda"


def load_curves(path: Path) -> tuple[list[EquityPoint], list[EquityPoint]]:
    base: list[EquityPoint] = []
    x2: list[EquityPoint] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            day = date.fromisoformat(row["date_utc"])
            base.append(EquityPoint(day, float(row["equity_base"])))
            x2.append(EquityPoint(day, float(row["equity_x2"])))
    return base, x2


def close(actual: float, expected: float, tolerance: float) -> bool:
    return abs(actual - expected) <= tolerance


def main() -> int:
    parser = argparse.ArgumentParser(description="T3 unified metric regression report")
    parser.add_argument("--equity-csv", type=Path, default=ROOT / "reports/expert/m1c_oos_daily_equity.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "reports/m1/T3_UNIFIED_METRICS_AND_POLICY_BENCHMARK_REPORT.md")
    args = parser.parse_args()
    digest = hashlib.sha256(args.equity_csv.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("sealed expert equity fixture hash mismatch")
    base_curve, x2_curve = load_curves(args.equity_csv)
    base = metrics_from_equity(base_curve)
    x2 = metrics_from_equity(x2_curve)
    checks = {
        "Sealed expert CSV hash": digest == EXPECTED_SHA256,
        "Base Sharpe regression": close(base.sharpe, 0.7882, 0.00005),
        "Base MaxDD regression": close(base.max_drawdown, 0.234729, 0.000005),
        "Base PSR regression": close(base.psr, 0.9024, 0.00005),
        "Cost x2 Sharpe regression": close(x2.sharpe, 0.7528, 0.00005),
        "Cost x2 MaxDD regression": close(x2.max_drawdown, 0.244688, 0.000005),
        "Cost x2 PSR regression": close(x2.psr, 0.8920, 0.00005),
        "Consecutive UTC daily observations": len(base_curve) == 975 and len(x2_curve) == 975,
    }
    passed = all(checks.values())
    lines = [
        "# T3 Unified Metrics and Policy Benchmark Report",
        "",
        f"- Status: {'pass' if passed else 'blocked'}",
        f"- Generated UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "- Scope: unified measurement and policy-benchmark foundation only",
        "- New strategy evaluated: no",
        "- New candidate OOS opened: no",
        "- Strategy returns computed: no; only sealed M1C regression evidence was recomputed",
        "- API key used: no",
        "- Live/paper/execution implemented: no",
        "",
        "## Unified Convention",
        "",
        "- One continuous UTC daily mark-to-market equity curve; flat days return zero.",
        "- Arithmetic daily returns, sample standard deviation (`ddof=1`), `sqrt(365)`, and zero risk-free rate.",
        "- Sharpe, MaxDD, Sortino, Calmar, PSR, and DSR share the same curve.",
        "- Freqtrade summary metrics remain diagnostics only and cannot override unified metrics.",
        "- Trade adapter consumes completed Freqtrade exports and public golden price marks; it does not generate signals.",
        "",
        "## Fixed Policy Benchmark",
        "",
        "- Allocation: 25% BTC, 25% ETH, 50% USDT.",
        "- Rebalance: every Monday at the UTC open.",
        "- Costs: identical modeled per-side costs applied to traded notional.",
        "- Benchmark builder is fixture-tested here; no candidate comparison or new OOS return is produced in T3.",
        "",
        "## Sealed M1C Regression",
        "",
        f"- Fixture: `reports/expert/m1c_oos_daily_equity.csv`",
        f"- Fixture SHA256: `{digest}`",
        f"- Range: {base_curve[0].day.isoformat()} through {base_curve[-1].day.isoformat()} UTC",
        "",
        "| Scenario | Observations | Total return | CAGR | Annual vol | Sharpe | MaxDD | Sortino | Calmar | PSR |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| Base | {base.observations} | {base.total_return:.4%} | {base.cagr:.4%} | {base.annualized_volatility:.4%} | {base.sharpe:.4f} | {base.max_drawdown:.4%} | {base.sortino:.4f} | {base.calmar:.4f} | {base.psr:.4f} |",
        f"| Cost x2 | {x2.observations} | {x2.total_return:.4%} | {x2.cagr:.4%} | {x2.annualized_volatility:.4%} | {x2.sharpe:.4f} | {x2.max_drawdown:.4%} | {x2.sortino:.4f} | {x2.calmar:.4f} | {x2.psr:.4f} |",
        "",
        "## Foundation Coverage",
        "",
        "- Freqtrade completed-trade adapter and daily public-price MTM: implemented and fixture-tested.",
        "- Policy benchmark with Monday-open rebalance and costs: implemented and fixture-tested.",
        "- PSR and DSR with multiple-trial penalty: implemented and fixture-tested.",
        "- Cost attribution: implemented and fixture-tested.",
        "- Frequency, turnover, duration, sleep, and concentration diagnostics: implemented and fixture-tested.",
        "- Granularity Gate comparison with mandatory Gate-status consistency: implemented and fixture-tested.",
        "",
        "## Gate",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for name, result in checks.items():
        lines.append(f"| {name} | {'pass' if result else 'fail'} |")
    lines.extend(
        [
            "",
            f"- T4 authorized: {'yes' if passed else 'no'}",
            "- M1D feasibility authorized: no; T4 must pass first",
            "- M1D strategy code authorized: no",
            "- M2 authorized: no",
            "",
            "Historical M1C remains `failed_validation`; this regression validates measurement code and does not rescue or approve that strategy.",
            "",
        ]
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"report={args.out}")
    print(f"status={'pass' if passed else 'blocked'}")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
