#!/usr/bin/env python3
"""Check sanitized Freqtrade M1C runtime outputs without calculating returns."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

STRATEGY = "BTCETHRelativeStrengthRotation"


def _load_trades(results_dir: Path) -> list[dict]:
    archives = sorted(results_dir.glob("*.zip"), key=lambda path: path.stat().st_mtime)
    if not archives:
        raise ValueError("no Freqtrade backtest archive found")
    with ZipFile(archives[-1]) as archive:
        candidates = [
            name
            for name in archive.namelist()
            if name.endswith(".json") and not name.endswith("_config.json") and not name.endswith(f"_{STRATEGY}.json")
        ]
        if len(candidates) != 1:
            raise ValueError(f"expected one backtest stats JSON, found {len(candidates)}")
        payload = json.loads(archive.read(candidates[0]))
    try:
        return list(payload["strategy"][STRATEGY]["trades"])
    except (KeyError, TypeError) as exc:
        raise ValueError("M1C strategy trades missing from backtest archive") from exc


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError(f"naive trade timestamp: {value}")
    return parsed


def validate_runtime_outputs(results_dir: Path, lookahead_csv: Path, recursive_log: Path) -> list[str]:
    failures: list[str] = []
    try:
        trades = sorted(_load_trades(results_dir), key=lambda trade: _parse_utc(trade["open_date"]))
    except (OSError, ValueError, KeyError) as exc:
        return [str(exc)]

    if len(trades) < 2:
        failures.append("runtime backtest must produce at least two trades")
    same_open_switches = 0
    for trade in trades:
        opened = _parse_utc(str(trade["open_date"]))
        if opened.weekday() != 0 or opened.hour != 0 or opened.minute != 0:
            failures.append(f"entry is not Monday 00:00 UTC: {trade['open_date']}")
    for previous, current in zip(trades, trades[1:]):
        previous_close = _parse_utc(str(previous["close_date"]))
        current_open = _parse_utc(str(current["open_date"]))
        if current_open < previous_close:
            failures.append("max_open_trades=1 violated by overlapping trades")
        if previous["pair"] != current["pair"] and previous_close == current_open:
            same_open_switches += 1
    if same_open_switches == 0:
        failures.append("no same-open BTC/ETH rotation was observed")

    try:
        with lookahead_csv.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        failures.append(f"lookahead result unavailable: {exc}")
        rows = []
    strategy_rows = [row for row in rows if row.get("strategy") == STRATEGY]
    if len(strategy_rows) != 1:
        failures.append("lookahead result must contain exactly one M1C strategy row")
    elif strategy_rows[0].get("has_bias", "").casefold() not in {"false", "no", "0"}:
        failures.append("Freqtrade lookahead-analysis reported bias")

    try:
        recursive_text = recursive_log.read_text(encoding="utf-8")
    except OSError as exc:
        failures.append(f"recursive result unavailable: {exc}")
        recursive_text = ""
    if "No variance on indicator(s) found due to recursive formula." not in recursive_text:
        failures.append("recursive-analysis did not report zero indicator variance")
    if "No lookahead bias on indicators found." not in recursive_text:
        failures.append("recursive-analysis did not clear indicator lookahead")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--lookahead-csv", type=Path, required=True)
    parser.add_argument("--recursive-log", type=Path, required=True)
    args = parser.parse_args()
    failures = validate_runtime_outputs(args.results_dir, args.lookahead_csv, args.recursive_log)
    if failures:
        print("m1c_freqtrade_runtime_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1c_freqtrade_runtime_check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
