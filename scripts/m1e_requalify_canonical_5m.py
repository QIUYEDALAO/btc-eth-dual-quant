#!/usr/bin/env python3
"""Requalify M1E from canonical 5m public evidence without network access."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from btc_eth_dual_quant.data.golden_data import FREQTRADE_IMAGE_REF, FREQTRADE_VERSION, parse_freqtrade_list_data, write_freqtrade_jsongz, write_jsonl_gz
from btc_eth_dual_quant.data.m1e_qualification import (
    INTERVAL_MS,
    aggregate_bars,
    build_canonical_5m,
    classify_audit_parity,
    determine_research_start,
    merge_archive_month,
)
from btc_eth_dual_quant.data.minute_archive import month_bounds_ms
from m0_dual_source_audit import _decode_zip_rows

SYMBOLS = ("BTCUSDT", "ETHUSDT")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="M1E canonical-5m contract-v2 requalification")
    parser.add_argument("--qualification-run", default="storage/raw/m1e_1h_qualification/run=20260710T183135Z")
    parser.add_argument("--qualification-manifest", default="storage/logs/m1e_1h_data_manifest.json")
    parser.add_argument("--diagnostics", default="storage/logs/m1e_conflict_diagnostics.json")
    parser.add_argument("--derived-root", default="storage/duckdb/m1e_canonical_5m_v2")
    parser.add_argument("--freqtrade-dir", default="freqtrade_lab/user_data/data/binance-m1e-v2")
    parser.add_argument("--manifest-out", default="storage/logs/m1e_canonical_5m_v2_manifest.json")
    parser.add_argument("--report-path", default="reports/m1/M1E_CANONICAL_5M_REQUALIFICATION_REPORT.md")
    parser.add_argument("--skip-runtime", action="store_true")
    parser.add_argument("--runtime-output", default=None, help="Ignored output from the pinned public-data runtime")
    return parser.parse_args()


def load_rows(run: Path, symbol: str, timeframe: str, month: str) -> tuple[list[dict], list[dict], list[dict]]:
    root = run / f"spot_klines_{timeframe}" / symbol / f"month={month}"
    monthly_path = root / "zip_monthly" / "response-0000.zip"
    monthly = _decode_zip_rows(monthly_path.read_bytes(), "spot_klines")
    daily: list[dict] = []
    sources = [{"source": "monthly", "sha256": hashlib.sha256(monthly_path.read_bytes()).hexdigest()}]
    for path in sorted(root.glob("zip_daily_*/response-0000.zip")):
        body = path.read_bytes()
        daily.extend(_decode_zip_rows(body, "spot_klines"))
        sources.append({"source": path.parent.name, "sha256": hashlib.sha256(body).hexdigest()})
    return monthly, daily, sources


def runtime_check(data_dir: Path, expected: dict[tuple[str, str], int], skip: bool, runtime_output: str | None) -> dict:
    if skip:
        return {"status": "not_run", "entries": []}
    command = [
        "docker", "run", "--rm", "-v", f"{data_dir.resolve()}:/freqtrade/user_data/data/binance:ro",
        FREQTRADE_IMAGE_REF, "list-data", "--datadir", "/freqtrade/user_data/data/binance",
        "--data-format-ohlcv", "jsongz", "--show-timerange", "--no-color",
    ]
    try:
        if runtime_output:
            output = Path(runtime_output).read_text(encoding="utf-8")
            returncode = 0
        else:
            completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300, check=False)
            output, returncode = completed.stdout, completed.returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "fail", "error": type(exc).__name__, "entries": []}
    entries = [asdict(item) for item in parse_freqtrade_list_data(output)]
    actual = {(item["pair"], item["timeframe"]): item["rows"] for item in entries}
    passed = returncode == 0 and FREQTRADE_VERSION in output and actual == expected
    return {
        "status": "pass" if passed else "fail", "entries": entries,
        "image_ref": FREQTRADE_IMAGE_REF, "version": FREQTRADE_VERSION,
        "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "execution_location": "external_public_runtime" if runtime_output else "local",
    }


def render_report(manifest: dict) -> str:
    audit_counts = Counter(item["classification"] for item in manifest["audit_parity"])
    lines = [
        "# M1E Canonical 5m Requalification Report", "",
        f"- Status: {manifest['status']}",
        "- Contract: M1E data contract v2 / ADR-0009",
        "- Scope: public-data requalification only",
        f"- Range: {manifest['range_start']} through {manifest['range_end']}",
        f"- Research start: {manifest['research_start'] or 'not_qualified'}",
        f"- Canonical 5m REST-confirmed daily revisions: {manifest['patched_5m_rows']}",
        f"- Unresolved canonical 5m conflicts: {manifest['unresolved_5m_conflicts']}",
        f"- Canonical incomplete child buckets: {manifest['incomplete_child_buckets']}",
        f"- Confirmed-outage child buckets isolated: {manifest['isolated_incomplete_child_buckets']}",
        f"- Manifest SHA256: `{manifest['manifest_sha256']}`", "",
        "## Canonical Datasets", "",
        "| Symbol | Timeframe | Rows | SHA256 |", "| --- | --- | ---: | --- |",
    ]
    for item in manifest["datasets"]:
        lines.append(f"| {item['symbol']} | {item['timeframe']} | {item['rows']} | `{item['sha256']}` |")
    lines += ["", "## Audit-Only Higher-Timeframe Evidence", ""]
    for classification, count in sorted(audit_counts.items()):
        lines.append(f"- {classification}: {count}")
    lines += [
        "- Higher-timeframe audit differences do not replace canonical 5m-derived OHLC.",
        "- Flow-field revisions are quarantined and are not admissible for a future volume-based strategy.", "",
        "## Gate", "",
        f"- Canonical 5m traceable: {'pass' if manifest['canonical_traceable'] else 'blocked'}",
        f"- Unresolved canonical price conflicts zero: {'pass' if not manifest['unresolved_5m_conflicts'] else 'blocked'}",
        f"- Deterministic 1h/4h derivation: {'pass' if not manifest['incomplete_child_buckets'] else 'blocked'}",
        f"- Freqtrade list-data: {manifest['freqtrade_runtime']['status']}",
        f"- Metadata-only sample-budget stage authorized: {'yes' if manifest['status'] == 'pass' else 'no'}",
        "- Candidate evaluated: no", "- OOS prices/returns accessed: no",
        "- Strategy code authorized: no", "- Freqtrade backtesting run: no",
        "- API key used: no", "- Private data used: no", "- M2 authorized: no", "",
        "## Historical Evidence", "",
        "ADR-0008 and the original blocked qualification report remain unchanged. This report supersedes only their admission decision under the explicitly revised source-authority contract.", "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    run = Path(args.qualification_run)
    old = json.loads(Path(args.qualification_manifest).read_text(encoding="utf-8"))
    diagnostics = json.loads(Path(args.diagnostics).read_text(encoding="utf-8"))
    supported = {
        (item["symbol"], item["month"], int(item["open_time"]))
        for item in diagnostics["diagnostics"]
        if item["timeframe"] == "5m" and item["classification"] == "monthly_daily_conflict_rest_supports_daily"
    }
    months = [item["month"] for item in old["months"]]
    derived_root, cache_root = Path(args.derived_root), Path(args.freqtrade_dir)
    canonical_by_symbol: dict[str, dict[str, list[dict]]] = {symbol: {} for symbol in SYMBOLS}
    month_states = []
    audit_parity = []
    source_hashes = []
    patched = unresolved = incomplete = isolated_incomplete = 0

    for month in months:
        symbol_blockers: list[str] = []
        missing: dict[str, set[int]] = {}
        for symbol in SYMBOLS:
            monthly5, daily5, hashes = load_rows(run, symbol, "5m", month)
            evidence = {timestamp for sym, mon, timestamp in supported if sym == symbol and mon == month}
            canonical = build_canonical_5m(monthly_rows=monthly5, daily_rows=daily5, rest_supported_daily_timestamps=evidence)
            canonical_by_symbol[symbol][month] = list(canonical.rows)
            patched += len(canonical.patched_timestamps)
            unresolved += len(canonical.unresolved_timestamps)
            if canonical.unresolved_timestamps:
                symbol_blockers.append(f"{symbol}:unresolved_5m_conflict")
            start, end = month_bounds_ms(month)
            missing[symbol] = set(range(start, end, INTERVAL_MS["5m"])) - {int(row["open_time"]) for row in canonical.rows}
            source_hashes.extend(dict(item, symbol=symbol, month=month, timeframe="5m") for item in hashes)

            derived1 = aggregate_bars(canonical.rows, "5m", "1h", month)
            derived4 = aggregate_bars(derived1.rows, "1h", "4h", month)
            for timeframe, derived in (("1h", derived1), ("4h", derived4)):
                monthly, daily, hashes = load_rows(run, symbol, timeframe, month)
                official = merge_archive_month(symbol=symbol, month=month, timeframe=timeframe, monthly_rows=monthly, daily_rows=daily)
                parity = classify_audit_parity(derived.rows, official.rows)
                audit_parity.append(dict(asdict(parity), symbol=symbol, month=month, timeframe=timeframe))
                source_hashes.extend(dict(item, symbol=symbol, month=month, timeframe=timeframe) for item in hashes)
        if missing["BTCUSDT"] != missing["ETHUSDT"]:
            symbol_blockers.append("single_symbol_5m_gap")
        common_missing = missing["BTCUSDT"] & missing["ETHUSDT"]
        expected_1h = {timestamp - timestamp % INTERVAL_MS["1h"] for timestamp in common_missing}
        expected_4h = {timestamp - timestamp % INTERVAL_MS["4h"] for timestamp in common_missing}
        for symbol in SYMBOLS:
            derived1 = aggregate_bars(canonical_by_symbol[symbol][month], "5m", "1h", month)
            derived4 = aggregate_bars(derived1.rows, "1h", "4h", month)
            unexpected_1h = set(derived1.incomplete_buckets) - expected_1h
            unexpected_4h = set(derived4.incomplete_buckets) - expected_4h
            incomplete += len(unexpected_1h) + len(unexpected_4h)
            isolated_incomplete += len(set(derived1.incomplete_buckets) & expected_1h) + len(set(derived4.incomplete_buckets) & expected_4h)
            if unexpected_1h or unexpected_4h:
                symbol_blockers.append(f"{symbol}:unexpected_incomplete_child_bucket")
        state = "blocked" if symbol_blockers else "audit_complete_with_confirmed_outage" if common_missing else "audit_complete"
        month_states.append({
            "month": month, "state": state, "blockers": sorted(set(symbol_blockers)),
            "confirmed_common_5m_gaps": len(common_missing),
        })

    # Liquidity and the original common six-month policy are unchanged.
    t1 = json.loads((ROOT / "storage/logs/t1_minute_archive_manifest.json").read_text(encoding="utf-8"))
    from decimal import Decimal
    from btc_eth_dual_quant.data.m1e_qualification import PairMonthQualification
    liquidity = {(item["symbol"], item["month"]): Decimal(item["p95_spread_proxy"]) for item in t1["months"]}
    qualifications = [PairMonthQualification(item["month"], item["state"], (), (), (), tuple(item["blockers"])) for item in month_states]
    research_start = determine_research_start(qualifications, liquidity)
    research_month = research_start[:7] if research_start else None

    datasets = []
    expected = {}
    for symbol in SYMBOLS:
        five = [row for month in months if research_month and month >= research_month for row in canonical_by_symbol[symbol][month]]
        one = [row for month in months if research_month and month >= research_month for row in aggregate_bars(canonical_by_symbol[symbol][month], "5m", "1h", month).rows]
        four = [row for month in months if research_month and month >= research_month for row in aggregate_bars(aggregate_bars(canonical_by_symbol[symbol][month], "5m", "1h", month).rows, "1h", "4h", month).rows]
        for timeframe, rows in (("5m", five), ("1h", one), ("4h", four)):
            sha = write_jsonl_gz(derived_root / f"{symbol}-{timeframe}.jsonl.gz", rows)
            write_freqtrade_jsongz(cache_root / f"{symbol.replace('USDT', '_USDT')}-{timeframe}.json.gz", rows)
            datasets.append({"symbol": symbol, "timeframe": timeframe, "rows": len(rows), "sha256": sha})
            expected[(symbol.replace("USDT", "/USDT"), timeframe)] = len(rows)
    runtime = runtime_check(cache_root, expected, args.skip_runtime, args.runtime_output)
    canonical_traceable = bool(source_hashes) and all(item["sha256"] for item in source_hashes)
    research_states = [item for item in month_states if research_month and item["month"] >= research_month]
    passed = bool(research_start) and canonical_traceable and not unresolved and not incomplete and all(item["state"] != "blocked" for item in research_states) and runtime["status"] == "pass"
    manifest = {
        "schema_version": 2, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if passed else "blocked", "range_start": old["range_start"], "range_end": old["range_end"],
        "research_start": research_start, "patched_5m_rows": patched, "unresolved_5m_conflicts": unresolved,
        "incomplete_child_buckets": incomplete, "isolated_incomplete_child_buckets": isolated_incomplete,
        "canonical_traceable": canonical_traceable,
        "months": month_states, "datasets": datasets, "audit_parity": audit_parity,
        "source_hashes": source_hashes, "freqtrade_runtime": runtime,
        "candidate_evaluated": False, "oos_accessed": False, "strategy_returns_computed": False,
        "api_key_used": False, "private_data_used": False, "runtime_artifacts_committed": False,
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    manifest["manifest_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    output = Path(args.manifest_out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = Path(args.report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(manifest), encoding="utf-8")
    print(f"report={report} status={manifest['status']} research_start={research_start}")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
