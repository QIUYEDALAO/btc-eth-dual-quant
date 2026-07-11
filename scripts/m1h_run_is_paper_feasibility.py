#!/usr/bin/env python3
"""Execute the single frozen M1H sealed-IS market-path observation."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from btc_eth_dual_quant.audit.m1h_paper import (
    FundingPoint,
    SYMBOLS,
    observe_events,
    summarize,
    validate_spot_bars,
)
from m1h_paper_protocol_check import validate as validate_protocol


ROOT = Path(__file__).resolve().parents[1]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Run one frozen M1H sealed-IS paper observation")
    result.add_argument("--protocol", type=Path, default=ROOT / "config/m1h_is_paper_protocol.json")
    result.add_argument("--qualification-manifest", type=Path, default=ROOT / "storage/logs/m1h_funding_qualification_manifest.json")
    result.add_argument("--snapshot-root", type=Path, default=ROOT / "storage/duckdb/m1h_is_snapshot")
    result.add_argument("--detail-out", type=Path, default=ROOT / "storage/logs/m1h_is_paper_detail.json")
    result.add_argument("--report", type=Path, default=ROOT / "reports/m1/M1H_IS_PAPER_FEASIBILITY_REPORT.md")
    return result


def load_jsonl_gz(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def render(summary: dict, protocol_hash: str, qualification_hash: str) -> str:
    lines = [
        "# M1H IS Paper-Feasibility Report", "",
        f"- Status: {summary['status']}",
        "- Scope: one frozen M1H sealed-IS market-reaction observation",
        "- Candidate: FUNDING-EXTREME-SPOT-CONTRARIAN",
        "- Candidate evaluated: paper event mechanism only",
        "- Formal strategy returns computed: no",
        "- PnL/equity/Sharpe computed: no",
        "- Backtest executed: no",
        "- OOS events/prices/returns accessed: no",
        "- OOS opened: no",
        f"- Protocol SHA256: `{protocol_hash}`",
        f"- Qualification manifest SHA256: `{qualification_hash}`",
        f"- Event evidence SHA256: `{summary['event_sha256']}`", "",
        "## Event And Episode Budget", "",
        f"- Raw frozen funding extremes: {summary['raw_extremes']}",
        f"- Same-symbol 24h representatives: {summary['symbol_cluster_representatives']}",
        f"- Complete symbol observations: {summary['complete_symbol_events']}",
        f"- Independent cross-symbol market episodes: {summary['independent_market_episodes']}",
        f"- Right-censored observations: {summary['right_censored']}",
        f"- Invalid observations: {summary['invalid_observations']}",
        f"- Projected full independent episodes: {summary['projected_full_independent_episodes']}",
        f"- Projected sealed-OOS episodes: {summary['projected_sealed_oos_episodes']} (IS event rate and calendar length only)", "",
        "## Frozen Reaction Horizons", "",
        "| Horizon | Complete | Median close displacement | Positive share | P05 | P95 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for horizon, item in summary["horizon_stats"].items():
        lines.append(
            f"| {horizon}h | {item['count']} | {item['median']:.4%} | {item['positive_share']:.2%} | "
            f"{item['p05']:.4%} | {item['p95']:.4%} |"
        )
    mae = summary["mae_distribution"]
    recovery = summary["recovery_time_distribution"]
    lines.extend([
        "", "## Mandatory Path Diagnostics", "",
        f"- Median 24h MFE: {summary['median_24h_mfe']:.4%}",
        f"- Median 24h close displacement: {summary['median_24h_close_displacement']:.4%}",
        f"- MAE minimum / P05 / median / P95: {mae['minimum']:.4%} / {mae['p05']:.4%} / {mae['median']:.4%} / {mae['p95']:.4%}",
        f"- Recovery share: {recovery['recovered_share']:.2%}",
        f"- Recovery median / P90: {recovery['recovered_median_minutes']} / {recovery['recovered_p90_minutes']} minutes",
        f"- Unrecovered within 24h: {recovery['unrecovered_count']}",
        "- MFE is path evidence only and is not a standalone Gate or realizable profit.", "",
        "## Symbol Evidence", "",
        "| Symbol | Complete events | Median 24h close displacement | Median 24h MFE |",
        "| --- | ---: | ---: | ---: |",
    ])
    for symbol, item in summary["by_symbol"].items():
        lines.append(
            f"| {symbol} | {item['complete_events']} | {item['median_24h_close_displacement']:.4%} | "
            f"{item['median_24h_mfe']:.4%} |"
        )
    lines.extend(["", "## Independent Episode Year Distribution", ""])
    for year, count in sorted(summary["by_year"].items()):
        lines.append(f"- {year}: {count}")
    lines.extend([
        "", f"- Years with at least ten independent episodes: {summary['years_with_ten_episodes']}",
        f"- Maximum single-year episode share: {summary['maximum_single_year_share']:.2%}",
        "", "## Frozen Paper Gate", "", "| Gate | Result |", "| --- | --- |",
    ])
    for gate, passed in summary["gate_matrix"].items():
        lines.append(f"| {gate} | {'pass' if passed else 'fail'} |")
    fixed_rule = "yes" if summary["status"] == "paper_feasibility_pass" else "no"
    lines.extend([
        "", "## Interpretation And Permissions", "",
        "This report measures post-settlement spot paths under the frozen protocol. It does not define entries, exits, positions, fees, PnL, Sharpe, equity or a trading result.",
        "No protocol threshold, horizon, interval, clustering rule, year or symbol definition was changed after observing the evidence.",
        f"- M1H Fixed Rule Contract Design authorized next: {fixed_rule}",
        "- Strategy code authorized: no",
        "- Freqtrade implementation authorized: no",
        "- Backtesting authorized: no",
        "- OOS authorized: no",
        "- API/trading authorized: no",
        "- M2 authorized: no", "",
    ])
    return "\n".join(lines)


def main() -> int:
    args = parser().parse_args()
    protocol_bytes = args.protocol.read_bytes()
    protocol = json.loads(protocol_bytes)
    failures = validate_protocol(protocol)
    if failures:
        raise SystemExit("frozen M1H protocol validation failed: " + "; ".join(failures))
    qualification_bytes = args.qualification_manifest.read_bytes()
    qualification = json.loads(qualification_bytes)
    if qualification.get("status") != "pass":
        raise SystemExit("M1H-03A did not pass; paper observation is prohibited")
    if qualification.get("oos_opened") or qualification.get("oos_values_parsed"):
        raise SystemExit("qualification manifest breached sealed OOS")
    if qualification.get("event_scan_executed") or qualification.get("path_diagnostics_computed"):
        raise SystemExit("qualification stage performed an unauthorized event/path scan")

    results = []
    for symbol in SYMBOLS:
        funding_rows = load_jsonl_gz(args.snapshot_root / f"{symbol}-funding.is.jsonl.gz")
        points = tuple(FundingPoint(**row) for row in funding_rows)
        spot_rows = load_jsonl_gz(args.snapshot_root / f"{symbol}-5m.is.jsonl.gz")
        bars = validate_spot_bars(symbol, spot_rows)
        results.append(observe_events(symbol=symbol, points=points, bars=bars, protocol=protocol))
    summary = summarize(results, protocol)
    summary.update({
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "qualification_manifest_sha256": hashlib.sha256(qualification_bytes).hexdigest(),
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "formal_strategy_returns_computed": False,
        "oos_opened": False,
    })
    args.detail_out.parent.mkdir(parents=True, exist_ok=True)
    args.detail_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report.write_text(render(summary, summary["protocol_sha256"], summary["qualification_manifest_sha256"]), encoding="utf-8")
    print(
        f"status={summary['status']} independent_episodes={summary['independent_market_episodes']} "
        f"report={args.report}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
