#!/usr/bin/env python3
"""Run frozen M1E paper diagnostics on ignored IS snapshots only."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from btc_eth_dual_quant.audit.m1e_paper import detect_events, summarize


ROOT = Path(__file__).resolve().parents[1]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Run M1E IS-only paper feasibility")
    result.add_argument("--protocol", type=Path, default=ROOT / "config/m1e_is_paper_protocol.json")
    result.add_argument("--snapshot-root", type=Path, default=ROOT / "storage/duckdb/m1e_is_snapshot")
    result.add_argument("--snapshot-manifest", type=Path, default=ROOT / "storage/logs/m1e_is_snapshot_manifest.json")
    result.add_argument("--detail-out", type=Path, default=ROOT / "storage/logs/m1e_is_paper_detail.json")
    result.add_argument("--report", type=Path, default=ROOT / "reports/m1/M1E_IS_PAPER_FEASIBILITY_REPORT.md")
    return result


def load_rows(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def render(summary: dict, protocol_hash: str, snapshot_hash: str) -> str:
    lines = [
        "# M1E IS Paper-Feasibility Report", "",
        f"- Status: {summary['status']}",
        "- Scope: M1E-06 IS-only paper diagnostics",
        "- Candidate evaluated: paper events only",
        "- Formal strategy returns computed: no",
        "- Equity curve computed: no",
        "- OOS prices/returns accessed: no",
        "- OOS opened: no",
        f"- Protocol SHA256: `{protocol_hash}`",
        f"- IS snapshot manifest SHA256: `{snapshot_hash}`",
        f"- Event evidence SHA256: `{summary['event_sha256']}`", "",
        "## Event Budget", "",
        f"- Raw expansion candidates: {summary['raw_candidates']}",
        f"- 24h cluster representatives: {summary['cluster_representatives']}",
        f"- Complete events: {summary['complete_events']}",
        f"- Right-censored events: {summary['right_censored']}",
        f"- Projected full events: {summary['projected_full_events']}",
        f"- Projected sealed-OOS events: {summary['projected_oos_events']}",
        f"- Longest no-event period: {summary['longest_sleep_hours'] / 24:.2f} days", "",
        "## Path Evidence", "",
        f"- Combined median 24h MFE: {summary['median_mfe_24h']:.4%}",
        f"- Combined median 24h MAE: {summary['median_mae_24h']:.4%}", "",
        "| Horizon | Count | Mean displacement | Median | Positive | P05 | P95 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for horizon, item in summary["horizon_stats"].items():
        lines.append(f"| {horizon}h | {item['count']} | {item['mean']:.4%} | {item['median']:.4%} | {item['positive_rate']:.2%} | {item['p05']:.4%} | {item['p95']:.4%} |")
    lines.extend(["", "## Symbol Evidence", "", "| Symbol | Events | Median 24h MFE | Median 24h MAE |", "| --- | ---: | ---: | ---: |"])
    for symbol, item in summary["by_symbol"].items():
        lines.append(f"| {symbol} | {item['events']} | {item['median_mfe_24h']:.4%} | {item['median_mae_24h']:.4%} |")
    lines.extend(["", "## Year Distribution", ""])
    for year, count in sorted(summary["by_year"].items()):
        lines.append(f"- {year}: {count}")
    lines.extend(["", "## Paper Gate", "", "| Gate | Result |", "| --- | --- |"])
    for gate, passed in summary["gate_matrix"].items():
        lines.append(f"| {gate} | {'pass' if passed else 'fail'} |")
    lines.extend([
        "", f"- M1E-07 fixed rule contract authorized: {'yes' if summary['status'] == 'pass' else 'no'}",
        "- Strategy code authorized: no", "- Freqtrade backtesting authorized: no",
        "- OOS authorized: no", "- M2 authorized: no", "",
        "This report measures price paths after preregistered IS events. It is not a strategy backtest and contains no entry, exit, position, fee-adjusted trade return or equity curve.", "",
    ])
    return "\n".join(lines)


def main() -> int:
    args = parser().parse_args()
    protocol_bytes = args.protocol.read_bytes()
    protocol = json.loads(protocol_bytes)
    manifest_bytes = args.snapshot_manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("status") != "pass" or manifest.get("oos_opened") or manifest.get("oos_ohlc_parsed"):
        raise SystemExit("IS snapshot manifest is not sealed and eligible")
    results = []
    for symbol in protocol["scope"]["symbols"]:
        path = args.snapshot_root / f"{symbol}-1h.is.jsonl.gz"
        results.append(detect_events(load_rows(path), protocol))
    summary = summarize(results, protocol)
    args.detail_out.parent.mkdir(parents=True, exist_ok=True)
    args.detail_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report.write_text(render(
        summary,
        hashlib.sha256(protocol_bytes).hexdigest(),
        hashlib.sha256(manifest_bytes).hexdigest(),
    ), encoding="utf-8")
    print(f"status={summary['status']} complete_events={summary['complete_events']} report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
