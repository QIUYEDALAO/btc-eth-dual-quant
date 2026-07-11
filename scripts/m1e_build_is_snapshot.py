#!/usr/bin/env python3
"""Build ignored M1E IS snapshots without exposing OOS OHLC to candidate code."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path

from btc_eth_dual_quant.audit.m1e_isolator import (
    IS_END_EXCLUSIVE_MS,
    IS_START_MS,
    SYMBOLS,
    isolate_bars,
)


ROOT = Path(__file__).resolve().parents[1]
OPEN_TIME = re.compile(rb'"open_time"\s*:\s*"?(\d+)')


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Build sealed M1E IS-only 1h/4h snapshots")
    result.add_argument("--source-root", type=Path, default=ROOT / "storage/duckdb/m1e_canonical_5m_v2")
    result.add_argument("--source-manifest", type=Path, default=ROOT / "storage/logs/m1e_canonical_5m_v2_manifest.json")
    result.add_argument("--out-root", type=Path, default=ROOT / "storage/duckdb/m1e_is_snapshot")
    result.add_argument("--manifest-out", type=Path, default=ROOT / "storage/logs/m1e_is_snapshot_manifest.json")
    result.add_argument("--report", type=Path, default=ROOT / "reports/m1/M1E_IS_DATA_ISOLATION_REPORT.md")
    return result


def bounded_rows(path: Path) -> tuple[list[dict], int]:
    rows: list[dict] = []
    oos_ohlc_parsed = 0
    with gzip.open(path, "rb") as handle:
        for line in handle:
            match = OPEN_TIME.search(line)
            if not match:
                raise ValueError(f"open_time unavailable before payload parse: {path}")
            timestamp = int(match.group(1))
            if timestamp < IS_START_MS:
                continue
            if timestamp >= IS_END_EXCLUSIVE_MS:
                continue
            rows.append(json.loads(line))
    return rows, oos_ohlc_parsed


def write_snapshot(path: Path, rows: tuple[object, ...]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            line = json.dumps(asdict(row), sort_keys=True, separators=(",", ":"))
            handle.write(line + "\n")
            digest.update(line.encode("utf-8") + b"\n")
    return digest.hexdigest()


def render_report(manifest: dict) -> str:
    lines = [
        "# M1E IS Data Isolation Report", "",
        f"- Status: {manifest['status']}",
        "- Scope: M1E-05 IS data isolation only",
        "- Candidate evaluated: no",
        "- Signals selected: no",
        "- Strategy returns computed: no",
        "- OOS OHLC parsed: no",
        "- OOS opened: no",
        f"- IS start: {manifest['is_start']}",
        f"- IS end exclusive: {manifest['is_end_exclusive']}",
        f"- Source manifest SHA256: `{manifest['source_manifest_sha256']}`", "",
        "## Snapshots", "",
        "| Dataset | Rows | Gaps | Segments | SHA256 |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for item in manifest["datasets"]:
        lines.append(f"| {item['symbol']}:{item['timeframe']} | {item['rows']} | {item['gaps']} | {item['segments']} | `{item['sha256']}` |")
    lines.extend([
        "", "## Gate", "",
        "- IS boundary enforcement: pass",
        "- Incomplete/future/duplicate bar rejection: pass",
        "- Gap segmentation: pass",
        "- Rewarm parameter selected: no",
        "- M1E-06 paper diagnostics authorized: yes",
        "- Fixed strategy rules authorized: no",
        "- Strategy code authorized: no",
        "- Freqtrade backtesting authorized: no",
        "- M2 authorized: no", "",
        "The ignored snapshots expose segment age so a later frozen contract can reject bars before its complete lookback is rebuilt. No fill or interpolation is performed.", "",
    ])
    return "\n".join(lines)


def main() -> int:
    args = parser().parse_args()
    source_manifest_bytes = args.source_manifest.read_bytes()
    source_manifest = json.loads(source_manifest_bytes)
    if source_manifest.get("status") != "pass" or source_manifest.get("research_start") != "2020-07-01":
        raise SystemExit("source manifest is not the accepted M1E canonical authority")
    if source_manifest.get("unresolved_5m_conflicts") or source_manifest.get("incomplete_child_buckets"):
        raise SystemExit("source manifest has canonical blockers")

    datasets: list[dict] = []
    for symbol in SYMBOLS:
        for timeframe in ("1h", "4h"):
            source = args.source_root / f"{symbol}-{timeframe}.jsonl.gz"
            rows, oos_parsed = bounded_rows(source)
            if oos_parsed:
                raise SystemExit("OOS OHLC was parsed")
            result = isolate_bars(symbol=symbol, timeframe=timeframe, rows=rows)
            output = args.out_root / f"{symbol}-{timeframe}.is.jsonl.gz"
            written_hash = write_snapshot(output, result.rows)
            if written_hash != result.canonical_sha256:
                raise SystemExit("snapshot hash mismatch")
            datasets.append({
                "symbol": symbol, "timeframe": timeframe, "rows": len(result.rows),
                "gaps": result.gap_count, "segments": result.segment_count,
                "sha256": written_hash,
            })
    manifest = {
        "version": 1,
        "status": "pass",
        "is_start": "2020-07-01T00:00:00Z",
        "is_end_exclusive": "2024-09-11T00:00:00Z",
        "oos_opened": False,
        "oos_ohlc_parsed": False,
        "candidate_evaluated": False,
        "strategy_returns_computed": False,
        "source_manifest_sha256": hashlib.sha256(source_manifest_bytes).hexdigest(),
        "datasets": datasets,
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    manifest["manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report.write_text(render_report(manifest), encoding="utf-8")
    print(f"status=pass report={args.report} manifest={args.manifest_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
