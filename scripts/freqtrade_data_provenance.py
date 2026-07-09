#!/usr/bin/env python3
"""Compare reproducible Freqtrade JSON cache with canonical M0 raw data."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import gzip
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.data.quality import interval_to_ms
from btc_eth_dual_quant.data.storage import AppendOnlyRawStore


FIELDS = ("open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class ProvenanceResult:
    symbol: str
    timeframe: str
    start_ms: int | None
    end_ms: int | None
    m0_rows: int
    freqtrade_rows: int
    overlap_rows: int
    missing_timestamp_rows: int
    field_differences: int
    m0_gaps: int
    freqtrade_gaps: int
    m0_sha256: str
    freqtrade_file_sha256: str
    overlap_sha256: str

    @property
    def status(self) -> str:
        return "pass" if self.overlap_rows > 0 and self.missing_timestamp_rows == 0 and self.field_differences == 0 else "blocked"


def _number(value: Any) -> str:
    decimal = Decimal(str(value))
    normalized = format(decimal.normalize(), "f")
    return "0" if normalized in {"-0", ""} else normalized


def _canonical_row(timestamp: Any, values: list[Any]) -> tuple[int, tuple[str, ...]]:
    return int(timestamp), tuple(_number(value) for value in values[:5])


def _load_freqtrade_json(path: Path) -> dict[int, tuple[str, ...]]:
    opener = gzip.open if path.suffix == ".gz" else Path.open
    if path.suffix == ".gz":
        with opener(path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
    else:
        with opener(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    if isinstance(payload, dict):
        payload = payload.get("data", payload.get("candles", []))
    rows: dict[int, tuple[str, ...]] = {}
    for row in payload if isinstance(payload, list) else []:
        if isinstance(row, list) and len(row) >= 6:
            timestamp, values = _canonical_row(row[0], row[1:6])
            rows[timestamp] = values
    return rows


def _load_m0_rows(raw_root: str | Path, symbol: str, timeframe: str) -> dict[int, tuple[str, ...]]:
    rows: dict[int, tuple[str, ...]] = {}
    for envelope in AppendOnlyRawStore(raw_root).iter_envelopes("spot_klines"):
        envelope_symbol = str(envelope.params.get("symbol", "")).upper()
        envelope_interval = str(envelope.params.get("interval", timeframe))
        if envelope_symbol != symbol.upper() or envelope_interval != timeframe:
            continue
        for row in envelope.payload if isinstance(envelope.payload, list) else []:
            if isinstance(row, list) and len(row) >= 6:
                timestamp, values = _canonical_row(row[0], row[1:6])
                rows[timestamp] = values
    return rows


def _digest(rows: dict[int, tuple[str, ...]]) -> str:
    payload = json.dumps(sorted(rows.items()), separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _gap_count(rows: dict[int, tuple[str, ...]], timeframe: str) -> int:
    step = interval_to_ms(timeframe)
    times = sorted(rows)
    return sum(1 for left, right in zip(times, times[1:]) if right - left != step)


def compare_provenance(
    symbol: str,
    timeframe: str,
    freqtrade_file: str | Path,
    raw_root: str | Path,
) -> ProvenanceResult:
    path = Path(freqtrade_file)
    freqtrade_rows = _load_freqtrade_json(path)
    m0_rows = _load_m0_rows(raw_root, symbol, timeframe)
    overlap = sorted(set(freqtrade_rows) & set(m0_rows))
    differences = sum(1 for timestamp in overlap if freqtrade_rows[timestamp] != m0_rows[timestamp])
    missing = len(set(freqtrade_rows) ^ set(m0_rows))
    overlap_rows = {timestamp: m0_rows[timestamp] for timestamp in overlap}
    all_times = sorted(set(freqtrade_rows) | set(m0_rows))
    return ProvenanceResult(
        symbol=symbol.upper(),
        timeframe=timeframe,
        start_ms=all_times[0] if all_times else None,
        end_ms=all_times[-1] if all_times else None,
        m0_rows=len(m0_rows),
        freqtrade_rows=len(freqtrade_rows),
        overlap_rows=len(overlap),
        missing_timestamp_rows=missing,
        field_differences=differences,
        m0_gaps=_gap_count(m0_rows, timeframe),
        freqtrade_gaps=_gap_count(freqtrade_rows, timeframe),
        m0_sha256=_digest(m0_rows),
        freqtrade_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        overlap_sha256=_digest(overlap_rows),
    )


def _utc(ms: int | None) -> str:
    if ms is None:
        return "not_available"
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat(timespec="seconds")


def render_report(results: list[ProvenanceResult]) -> str:
    passed = bool(results) and all(result.status == "pass" for result in results)
    lines = [
        "# Freqtrade / M0 Data Provenance",
        "",
        f"- Status: {'pass' if passed else 'blocked'}",
        f"- Generated UTC: {datetime.now(tz=timezone.utc).isoformat(timespec='seconds')}",
        "- Scope: public spot research data comparison only",
        "- M0 role: canonical audit authority",
        "- Freqtrade role: reproducible runtime cache",
        "- API key used: no",
        "- Runtime data committed: no",
        "",
        "| Symbol | Timeframe | Start UTC | End UTC | M0 rows | Freqtrade rows | Overlap | Missing timestamps | Field differences | M0 gaps | Freqtrade gaps | Status |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for result in results:
        lines.append(
            f"| `{result.symbol}` | `{result.timeframe}` | `{_utc(result.start_ms)}` | `{_utc(result.end_ms)}` | "
            f"{result.m0_rows} | {result.freqtrade_rows} | {result.overlap_rows} | "
            f"{result.missing_timestamp_rows} | {result.field_differences} | {result.m0_gaps} | "
            f"{result.freqtrade_gaps} | {result.status} |"
        )
    lines.extend(["", "## Hashes", ""])
    for result in results:
        lines.extend(
            [
                f"### {result.symbol} {result.timeframe}",
                "",
                f"- M0 normalized SHA256: `{result.m0_sha256}`",
                f"- Freqtrade file SHA256: `{result.freqtrade_file_sha256}`",
                f"- Overlap normalized SHA256: `{result.overlap_sha256}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision",
            "",
            "Freqtrade cache may be deleted and regenerated. Any mismatch remains blocked until explained against M0; this report does not approve M2 or trading.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Freqtrade JSON data cache with M0 raw data")
    parser.add_argument("--mapping", action="append", required=True, help="SYMBOL=path/to/freqtrade.json")
    parser.add_argument("--timeframe", default="1d")
    parser.add_argument("--raw-root", default="storage/raw")
    parser.add_argument("--out", default="reports/m1/FREQTRADE_M0_DATA_PROVENANCE.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results: list[ProvenanceResult] = []
    for mapping in args.mapping:
        symbol, separator, path = mapping.partition("=")
        if not separator:
            raise SystemExit(f"invalid mapping: {mapping}")
        results.append(compare_provenance(symbol, args.timeframe, path, args.raw_root))
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(results), encoding="utf-8")
    print(f"Wrote Freqtrade/M0 provenance report: {output}")
    return 0 if all(result.status == "pass" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
