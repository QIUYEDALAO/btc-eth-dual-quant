#!/usr/bin/env python3
"""Build ignored sealed-IS M1H inputs and a sanitized qualification report."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from btc_eth_dual_quant.audit.m1h_paper import (
    FIVE_MINUTE_MS,
    IS_END_EXCLUSIVE_MS,
    IS_START_MS,
    SYMBOLS,
    qualify_funding_rows,
    validate_spot_bars,
)


ROOT = Path(__file__).resolve().parents[1]
FUNDING_OBJECT = re.compile(rb'\{[^{}\n]*"fundingTime"[^{}\n]*\}')
FUNDING_TIME = re.compile(rb'"fundingTime"\s*:\s*"?(\d+)')
OPEN_TIME = re.compile(rb'"open_time"\s*:\s*"?(\d+)')


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Qualify public funding and canonical 5m data for M1H")
    result.add_argument("--raw-funding", type=Path, default=ROOT / "storage/raw/funding_rate_history/year=2026/month=07/day=09/raw.jsonl")
    result.add_argument("--spot-root", type=Path, default=ROOT / "storage/duckdb/m1e_canonical_5m_v2")
    result.add_argument("--spot-manifest", type=Path, default=ROOT / "storage/logs/m1e_canonical_5m_v2_manifest.json")
    result.add_argument("--snapshot-root", type=Path, default=ROOT / "storage/duckdb/m1h_is_snapshot")
    result.add_argument("--manifest-out", type=Path, default=ROOT / "storage/logs/m1h_funding_qualification_manifest.json")
    result.add_argument("--report", type=Path, default=ROOT / "reports/m1/M1H_FUNDING_DATA_QUALIFICATION_REPORT.md")
    return result


def _json_string(line: bytes, field: str) -> str:
    match = re.search(rb'"' + field.encode("ascii") + rb'"\s*:\s*("(?:\\.|[^"\\])*")', line)
    if not match:
        raise ValueError(f"raw envelope missing {field}")
    return str(json.loads(match.group(1)))


def bounded_funding_rows(path: Path, symbol: str) -> tuple[list[dict], list[dict], int]:
    """Parse only pre-OOS payload objects; later values remain unparsed bytes."""

    rows: list[dict] = []
    sources: list[dict] = []
    skipped_oos_objects = 0
    with path.open("rb") as handle:
        for line in handle:
            content_hash = _json_string(line, "content_sha256")
            source_name = _json_string(line, "source")
            bounded = 0
            for match in FUNDING_OBJECT.finditer(line):
                time_match = FUNDING_TIME.search(match.group(0))
                if not time_match:
                    continue
                time_ms = int(time_match.group(1))
                if time_ms >= IS_END_EXCLUSIVE_MS:
                    skipped_oos_objects += 1
                    continue
                row = json.loads(match.group(0))
                if str(row.get("symbol") or "").upper() != symbol:
                    continue
                row["source_sha256"] = content_hash
                rows.append(row)
                bounded += 1
            if bounded:
                sources.append({
                    "source": source_name,
                    "content_sha256": content_hash,
                    "bounded_rows": bounded,
                    "endpoint_family": "data.binance.vision monthly fundingRate ZIP",
                })
    if not rows:
        raise ValueError(f"no bounded public funding rows for {symbol}")
    return rows, sources, skipped_oos_objects


def bounded_spot_rows(path: Path) -> tuple[list[dict], list[bytes], int]:
    rows: list[dict] = []
    canonical_lines: list[bytes] = []
    oos_values_parsed = 0
    with gzip.open(path, "rb") as handle:
        for line in handle:
            match = OPEN_TIME.search(line)
            if not match:
                raise ValueError(f"open_time unavailable before payload parse: {path}")
            time_ms = int(match.group(1))
            if time_ms < IS_START_MS or time_ms >= IS_END_EXCLUSIVE_MS:
                continue
            rows.append(json.loads(line))
            canonical_lines.append(line.rstrip(b"\n"))
    return rows, canonical_lines, oos_values_parsed


def write_jsonl_gz(path: Path, records: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as handle:
        for record in records:
            line = json.dumps(record, sort_keys=True, separators=(",", ":"))
            handle.write(line + "\n")
            digest.update(line.encode("utf-8") + b"\n")
    return digest.hexdigest()


def render(manifest: dict) -> str:
    lines = [
        "# M1H Funding Data Qualification Report", "",
        f"- Status: {manifest['status']}",
        "- Scope: M1H-03A public funding-data qualification only",
        "- Candidate: FUNDING-EXTREME-SPOT-CONTRARIAN",
        "- Funding event scan executed: no",
        "- Funding event count computed: no",
        "- MFE/MAE/recovery computed: no",
        "- Formal strategy returns computed: no",
        "- OOS funding values parsed: no",
        "- OOS spot OHLC parsed: no",
        "- OOS opened: no",
        "- API key used: no",
        "- Private data used: no", "",
        "## Lineage And Settlement Semantics", "",
        "- Funding source: Binance public monthly USD-M fundingRate ZIP, preserved in M0 append-only raw envelopes.",
        "- Symbols: BTCUSDT, ETHUSDT.",
        f"- Qualified boundary: before {manifest['is_end_exclusive']}.",
        "- fundingTime is the public settlement timestamp in UTC epoch milliseconds.",
        "- A funding observation is available no earlier than its fundingTime.",
        "- Per-event intervals are inferred from adjacent settlement timestamps and checked against each public row's declared interval.",
        "- No default funding cadence is supplied.", "",
        "## Funding Qualification", "",
        "| Symbol | Unique rows | Raw duplicates | Conflicts | Invalid rows | Invalid intervals | Missing settlements | Start UTC | End UTC | SHA256 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for item in manifest["funding"]:
        lines.append(
            f"| {item['symbol']} | {item['unique_rows']} | {item['identical_duplicates']} | "
            f"{item['conflicting_duplicates']} | {item['invalid_rows']} | {item['invalid_intervals']} | "
            f"{item['missing_settlements']} | {item['start_utc']} | {item['end_utc']} | `{item['sha256']}` |"
        )
    lines.extend([
        "", "### Public Raw Payload Hashes", "",
    ])
    for item in manifest["funding"]:
        hashes = ", ".join(f"`{source['content_sha256']}`" for source in item["sources"])
        lines.append(f"- {item['symbol']}: {hashes}")
    lines.extend([
        "", "Identical duplicate timestamps come from repeated append-only public backfills; they are canonicalized only after their rate and declared interval agree exactly.",
        "", "## Canonical Spot 5m Dependency", "",
        "| Symbol | IS rows | Known gaps | Start UTC | End UTC | SHA256 |",
        "| --- | ---: | ---: | --- | --- | --- |",
    ])
    for item in manifest["spot_5m"]:
        lines.append(f"| {item['symbol']} | {item['rows']} | {item['gaps']} | {item['start_utc']} | {item['end_utc']} | `{item['sha256']}` |")
    lines.extend([
        "", "Known canonical gaps remain explicit. No missing bar is filled or shifted; a later paper observation touching one is censored or invalid under the frozen protocol.",
        "", "## Qualification Gate", "",
        f"- Funding lineage: {manifest['gates']['funding_lineage']}",
        f"- Settlement timestamps/order/timezone: {manifest['gates']['settlement_timing']}",
        f"- Per-event interval continuity: {manifest['gates']['per_event_interval']}",
        f"- Duplicate/conflict handling: {manifest['gates']['duplicate_conflict']}",
        f"- Canonical spot 5m dependency: {manifest['gates']['canonical_spot_5m']}",
        f"- OOS isolation: {manifest['gates']['oos_isolation']}",
        f"- M1H-03B authorized in this task: {'yes' if manifest['status'] == 'pass' else 'no'}",
        "- Strategy code authorized: no",
        "- Backtesting authorized: no",
        "- OOS authorized: no",
        "- M2 authorized: no", "",
    ])
    return "\n".join(lines)


def utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    args = parser().parse_args()
    source_manifest_bytes = args.spot_manifest.read_bytes()
    source_manifest = json.loads(source_manifest_bytes)
    if source_manifest.get("status") != "pass" or source_manifest.get("research_start") != "2020-07-01":
        raise SystemExit("canonical 5m authority is not qualified")
    if source_manifest.get("unresolved_5m_conflicts") or source_manifest.get("incomplete_child_buckets"):
        raise SystemExit("canonical 5m authority has unresolved blockers")

    funding_items: list[dict] = []
    funding_snapshots: list[dict] = []
    for symbol in SYMBOLS:
        rows, sources, skipped = bounded_funding_rows(args.raw_funding, symbol)
        result = qualify_funding_rows(
            symbol=symbol,
            rows=rows,
            source_hashes=[item["content_sha256"] for item in sources],
            raw_rows=len(rows),
            oos_values_parsed=0,
        )
        snapshot_records = [asdict(point) for point in result.points]
        snapshot_hash = write_jsonl_gz(args.snapshot_root / f"{symbol}-funding.is.jsonl.gz", snapshot_records)
        if snapshot_hash != result.canonical_sha256:
            raise SystemExit("funding snapshot hash mismatch")
        funding_items.append({
            "symbol": symbol,
            "unique_rows": len(result.points),
            "raw_rows": result.raw_rows,
            "identical_duplicates": result.identical_duplicates,
            "conflicting_duplicates": result.conflicting_duplicates,
            "invalid_rows": result.invalid_rows,
            "invalid_intervals": result.invalid_intervals,
            "missing_settlements": result.missing_settlements,
            "oos_values_parsed": result.oos_values_parsed,
            "oos_objects_skipped_before_value_parse": skipped,
            "start_utc": utc(result.first_time_ms),
            "end_utc": utc(result.last_time_ms),
            "sha256": result.canonical_sha256,
            "sources": sources,
            "passed": result.passed,
        })
        funding_snapshots.append({"symbol": symbol, "path": f"{symbol}-funding.is.jsonl.gz", "sha256": snapshot_hash})

    spot_items: list[dict] = []
    for symbol in SYMBOLS:
        source = args.spot_root / f"{symbol}-5m.jsonl.gz"
        rows, _, oos_parsed = bounded_spot_rows(source)
        bars = validate_spot_bars(symbol, rows)
        gaps = sum(right.open_time_ms - left.open_time_ms != FIVE_MINUTE_MS for left, right in zip(bars, bars[1:]))
        snapshot_hash = write_jsonl_gz(args.snapshot_root / f"{symbol}-5m.is.jsonl.gz", rows)
        spot_items.append({
            "symbol": symbol,
            "rows": len(bars),
            "gaps": gaps,
            "oos_values_parsed": oos_parsed,
            "start_utc": utc(bars[0].open_time_ms),
            "end_utc": utc(bars[-1].close_time_ms),
            "sha256": snapshot_hash,
        })

    gates = {
        "funding_lineage": "pass" if all(item["sources"] for item in funding_items) else "fail",
        "settlement_timing": "pass" if all(not item["invalid_rows"] for item in funding_items) else "fail",
        "per_event_interval": "pass" if all(not item["invalid_intervals"] and not item["missing_settlements"] for item in funding_items) else "fail",
        "duplicate_conflict": "pass" if all(not item["conflicting_duplicates"] for item in funding_items) else "fail",
        "canonical_spot_5m": "pass" if all(item["rows"] and not item["oos_values_parsed"] for item in spot_items) else "fail",
        "oos_isolation": "pass" if all(not item["oos_values_parsed"] for item in funding_items + spot_items) else "fail",
    }
    manifest = {
        "version": 1,
        "status": "pass" if all(value == "pass" for value in gates.values()) else "blocked",
        "candidate_id": "FUNDING-EXTREME-SPOT-CONTRARIAN",
        "protocol_id": "M1H-02-FUNDING-EXTREME-SPOT-PAPER-V1",
        "is_start": "2020-07-01T00:00:00Z",
        "is_end_exclusive": "2024-09-11T00:00:00Z",
        "event_scan_executed": False,
        "event_count_computed": False,
        "path_diagnostics_computed": False,
        "returns_computed": False,
        "oos_opened": False,
        "oos_values_parsed": False,
        "private_data_used": False,
        "api_key_used": False,
        "source_manifest_sha256": hashlib.sha256(source_manifest_bytes).hexdigest(),
        "funding": funding_items,
        "funding_snapshots": funding_snapshots,
        "spot_5m": spot_items,
        "gates": gates,
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    manifest["manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report.write_text(render(manifest), encoding="utf-8")
    print(f"status={manifest['status']} report={args.report}")
    return 0 if manifest["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
