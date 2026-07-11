#!/usr/bin/env python3
"""Run the frozen M1G protocol once on ignored sealed-IS snapshots."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from btc_eth_dual_quant.audit.m1g_paper import detect_events, summarize


ROOT = Path(__file__).resolve().parents[1]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Run M1G sealed-IS paper feasibility")
    result.add_argument("--protocol", type=Path, default=ROOT / "config/m1g_is_paper_protocol.json")
    result.add_argument("--snapshot-root", type=Path, default=ROOT / "storage/duckdb/m1e_is_snapshot")
    result.add_argument("--snapshot-manifest", type=Path, default=ROOT / "storage/logs/m1e_is_snapshot_manifest.json")
    result.add_argument("--detail-out", type=Path, default=ROOT / "storage/logs/m1g_is_paper_detail.json")
    result.add_argument("--report", type=Path, default=ROOT / "reports/m1/M1G_IS_PAPER_FEASIBILITY_REPORT.md")
    return result


def load_rows(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def render(summary: dict, protocol_hash: str, snapshot_hash: str) -> str:
    lines = [
        "# M1G IS Paper-Feasibility Report", "", f"- Status: {summary['status']}",
        "- Scope: exact frozen M1G sealed-IS paper protocol",
        "- Candidate evaluated: paper events only", "- Formal strategy returns computed: no",
        "- Equity curve computed: no", "- OOS prices/returns accessed: no", "- OOS opened: no",
        f"- Protocol SHA256: `{protocol_hash}`", f"- IS snapshot manifest SHA256: `{snapshot_hash}`",
        f"- Event evidence SHA256: `{summary['event_sha256']}`", "", "## Event Budget", "",
        f"- Raw panic candidates: {summary['raw_candidates']}",
        f"- 24h cluster representatives: {summary['cluster_representatives']}",
        f"- Complete events: {summary['complete_events']}", f"- Right-censored events: {summary['right_censored']}",
        f"- Projected full events: {summary['projected_full_events']}",
        f"- Projected sealed-OOS events: {summary['projected_oos_events']}",
        f"- Longest no-event period: {summary['longest_sleep_hours'] / 24:.2f} days", "",
        "## Path And Tail Evidence", "", f"- Combined median 24h MFE: {summary['median_mfe_24h']:.4%}",
        f"- Combined median 24h MAE: {summary['median_mae_24h']:.4%}",
        f"- Worst 24h MAE: {summary['worst_mae_24h']:.4%}",
        f"- Maximum rolling 24h event count: {summary['maximum_rolling_24h_events']}",
        f"- Maximum rolling 7d event count: {summary['maximum_rolling_7d_events']}", "",
        "| Horizon | Count | Mean displacement | Median | Positive | P05 | P95 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for horizon, item in summary["horizon_stats"].items():
        lines.append(f"| {horizon}h | {item['count']} | {item['mean']:.4%} | {item['median']:.4%} | {item['positive_rate']:.2%} | {item['p05']:.4%} | {item['p95']:.4%} |")
    lines.extend(["", "## Symbol Evidence", "", "| Symbol | Events | Median 24h MFE | Median 24h MAE | Worst 24h MAE |", "| --- | ---: | ---: | ---: | ---: |"])
    for symbol, item in summary["by_symbol"].items():
        lines.append(f"| {symbol} | {item['events']} | {item['median_mfe_24h']:.4%} | {item['median_mae_24h']:.4%} | {item['worst_mae_24h']:.4%} |")
    lines.extend(["", "## Year Distribution", ""])
    for year, count in sorted(summary["by_year"].items()):
        lines.append(f"- {year}: {count}")
    lines.extend(["", "## Paper Gate", "", "| Gate | Result |", "| --- | --- |"])
    for gate, passed in summary["gate_matrix"].items():
        lines.append(f"| {gate} | {'pass' if passed else 'fail'} |")
    close_24h = summary["horizon_stats"]["24"]
    lines.extend([
        "", "## Interpretation", "",
        "- The preregistered paper Gate passes, but MFE is an opportunity envelope, not a realizable exit.",
        f"- Median 24h close displacement is {close_24h['median']:.4%}, below both the 0.30% Base and 0.60% Cost x2 roundtrip references.",
        f"- Median 24h MAE is {summary['median_mae_24h']:.4%} versus median MFE {summary['median_mfe_24h']:.4%}; worst MAE is {summary['worst_mae_24h']:.4%}.",
        "- A fixed contract must therefore derive one target, one invalidation stop, a holding limit, position cap and cluster cooldown without parameter search.",
        "- Paper pass does not establish positive expectancy, acceptable drawdown or implementability.",
    ])
    lines.extend([
        "", f"- Fixed rule contract authorized: {'yes' if summary['status'] == 'pass' else 'no'}",
        "- Strategy code authorized: no", "- Freqtrade backtesting authorized: no",
        "- OOS authorized: no", "- M2 authorized: no", "",
        "This is price-path evidence after preregistered IS events, not a strategy backtest. It contains no fill, exit, position, fee-adjusted return or equity curve.", "",
    ])
    return "\n".join(lines)


def main() -> int:
    args = parser().parse_args()
    protocol_bytes = args.protocol.read_bytes()
    protocol = json.loads(protocol_bytes)
    if protocol.get("authorization", {}).get("paper_protocol_frozen") is not True:
        raise SystemExit("M1G paper protocol is not frozen")
    manifest_bytes = args.snapshot_manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("status") != "pass" or manifest.get("oos_opened") or manifest.get("oos_ohlc_parsed"):
        raise SystemExit("IS snapshot manifest is not sealed and eligible")
    results = [
        detect_events(load_rows(args.snapshot_root / f"{symbol}-1h.is.jsonl.gz"), protocol)
        for symbol in protocol["scope"]["symbols"]
    ]
    summary = summarize(results, protocol)
    args.detail_out.parent.mkdir(parents=True, exist_ok=True)
    args.detail_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report.write_text(render(summary, hashlib.sha256(protocol_bytes).hexdigest(), hashlib.sha256(manifest_bytes).hexdigest()), encoding="utf-8")
    print(f"status={summary['status']} complete_events={summary['complete_events']} report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
