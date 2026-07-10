#!/usr/bin/env python3
"""Render the immutable M1C P3 report from Freqtrade exports."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any
from zipfile import ZipFile

STRATEGY = "BTCETHRelativeStrengthRotation"
DAY_MS = 86_400_000


@dataclass(frozen=True)
class RunResult:
    label: str
    stats: dict[str, Any]
    trades: list[dict[str, Any]]
    archive_sha256: str

    @property
    def complete_trades(self) -> list[dict[str, Any]]:
        return [trade for trade in self.trades if trade.get("exit_reason") != "force_exit"]


@dataclass(frozen=True)
class DataProfile:
    symbol: str
    rows: int
    start_utc: str
    end_utc: str
    gaps: int
    sha256: str


def load_run(label: str, directory: Path) -> RunResult:
    archives = []
    for archive in directory.glob("*.zip"):
        metadata_path = archive.with_suffix(".meta.json")
        if not metadata_path.is_file():
            continue
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        notes = metadata.get(STRATEGY, {}).get("notes")
        if notes == f"m1c-p3:{label}":
            archives.append(archive)
    archives.sort(key=lambda path: path.stat().st_mtime)
    if len(archives) != 1:
        raise ValueError(f"{label}: expected one note-matched Freqtrade archive, found {len(archives)}")
    archive_path = archives[0]
    with ZipFile(archive_path) as archive:
        candidates = [
            name
            for name in archive.namelist()
            if name.endswith(".json") and not name.endswith("_config.json") and not name.endswith(f"_{STRATEGY}.json")
        ]
        if len(candidates) != 1:
            raise ValueError(f"{label}: expected one stats JSON, found {len(candidates)}")
        payload = json.loads(archive.read(candidates[0]))
    stats = payload.get("strategy", {}).get(STRATEGY)
    if not isinstance(stats, dict):
        raise ValueError(f"{label}: strategy stats missing")
    trades = stats.get("trades", [])
    if not isinstance(trades, list):
        raise ValueError(f"{label}: trades must be a list")
    return RunResult(label, stats, trades, hashlib.sha256(archive_path.read_bytes()).hexdigest())


def _load_json_rows(path: Path) -> list[list[Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("data", payload.get("candles", []))
    return [row for row in payload if isinstance(row, list) and len(row) >= 6]


def profile_data(data_dir: Path, symbol: str, start: date, end_exclusive: date) -> DataProfile:
    stem = symbol.replace("/", "_").replace(":", "_")
    candidates = sorted(data_dir.rglob(f"{stem}*1d*.json"))
    if len(candidates) != 1:
        raise ValueError(f"{symbol}: expected one 1d JSON file, found {len(candidates)}")
    path = candidates[0]
    start_ms = int(datetime.combine(start, datetime.min.time(), tzinfo=UTC).timestamp() * 1000)
    end_ms = int(datetime.combine(end_exclusive, datetime.min.time(), tzinfo=UTC).timestamp() * 1000)
    timestamps = sorted({int(row[0]) for row in _load_json_rows(path) if start_ms <= int(row[0]) < end_ms})
    if not timestamps:
        raise ValueError(f"{symbol}: no rows in P3 range")
    gaps = sum(max(0, (right - left) // DAY_MS - 1) for left, right in zip(timestamps, timestamps[1:]))
    return DataProfile(
        symbol=symbol,
        rows=len(timestamps),
        start_utc=datetime.fromtimestamp(timestamps[0] / 1000, tz=UTC).isoformat(),
        end_utc=datetime.fromtimestamp(timestamps[-1] / 1000, tz=UTC).isoformat(),
        gaps=gaps,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def _pct(value: Any) -> str:
    return f"{_num(value):.4%}"


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _delete_best_three_return(run: RunResult) -> float:
    best = sorted((_num(trade.get("profit_abs")) for trade in run.trades), reverse=True)[:3]
    return (_num(run.stats.get("profit_total_abs")) - sum(best)) / _num(run.stats.get("starting_balance"))


def _lookahead_pass(path: Path) -> tuple[bool, int, int, int]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("strategy") == STRATEGY]
    if len(rows) != 1:
        return False, 0, 0, 0
    row = rows[0]
    biased_entries = int(row.get("biased_entry_signals", 0))
    biased_exits = int(row.get("biased_exit_signals", 0))
    signals = int(row.get("total_signals", 0))
    passed = row.get("has_bias", "").casefold() in {"false", "no", "0"} and biased_entries == 0 and biased_exits == 0
    return passed, signals, biased_entries, biased_exits


def build_report(
    runs: dict[str, RunResult],
    profiles: list[DataProfile],
    lookahead_csv: Path,
    recursive_log: Path,
    start: date,
    end_exclusive: date,
    oos_start: date,
    workflow_url: str = "not_recorded",
) -> str:
    required = {"base-full", "x2-full", "base-oos", "x2-oos", *(f"segment-{index}" for index in range(1, 5))}
    missing = sorted(required - set(runs))
    if missing:
        raise ValueError(f"missing P3 runs: {', '.join(missing)}")

    base = runs["base-full"]
    x2 = runs["x2-full"]
    base_oos = runs["base-oos"]
    x2_oos = runs["x2-oos"]
    segments = [runs[f"segment-{index}"] for index in range(1, 5)]
    lookahead_pass, signals, biased_entries, biased_exits = _lookahead_pass(lookahead_csv)
    recursive_text = recursive_log.read_text(encoding="utf-8")
    recursive_pass = (
        "No variance on indicator(s) found due to recursive formula." in recursive_text
        and "No lookahead bias on indicators found." in recursive_text
    )
    complete_count = len(base.complete_trades)
    oos_complete_count = len(base_oos.complete_trades)
    delete_best_three = _delete_best_three_return(base)
    positive_segments = sum(_num(run.stats.get("profit_total")) > 0 for run in segments)
    data_gaps = sum(profile.gaps for profile in profiles)
    worst_drawdown = max(_num(base.stats.get("max_drawdown_account")), _num(x2.stats.get("max_drawdown_account")))

    gates = {
        "Backtest code": True,
        "Complete trades >= 80": complete_count >= 80,
        "OOS complete trades >= 20": oos_complete_count >= 20,
        "OOS Sharpe >= 1.0": _num(base_oos.stats.get("sharpe")) >= 1.0,
        "Base total return > 0": _num(base.stats.get("profit_total")) > 0,
        "Cost x2 total return > 0": _num(x2.stats.get("profit_total")) > 0,
        "Base OOS return > 0": _num(base_oos.stats.get("profit_total")) > 0,
        "Cost x2 OOS return > 0": _num(x2_oos.stats.get("profit_total")) > 0,
        "Maximum drawdown <= 15%": worst_drawdown <= 0.15,
        "Delete best 3 return >= 0": delete_best_three >= 0,
        "At least 3/4 IS segments positive": positive_segments >= 3,
        "lookahead-analysis": lookahead_pass,
        "recursive-analysis": recursive_pass,
        "Unexplained data gaps = 0": data_gaps == 0,
    }
    status = "under_review" if all(gates.values()) else "failed_validation"
    completed = sorted(base.complete_trades, key=lambda trade: str(trade.get("open_date")))
    best_trade = max(completed, key=lambda trade: _num(trade.get("profit_ratio")), default={})
    worst_trade = min(completed, key=lambda trade: _num(trade.get("profit_ratio")), default={})

    lines = [
        "# M1C BTC/ETH Rotation Backtest Report",
        "",
        f"- Status: {status}",
        f"- Generated UTC: {datetime.now(tz=UTC).isoformat(timespec='seconds')}",
        f"- Evidence workflow: {workflow_url}",
        "- Scope: Freqtrade historical backtest validation only",
        "- Strategy: BTCETHRelativeStrengthRotation",
        "- No live trading / no dry-run / no execution/live / no order placement",
        "- Freqtrade is the sole strategy-return authority",
        "- Not investment advice",
        "",
        "## Data and Split",
        "",
        f"- Full data range: {start.isoformat()} through {(end_exclusive - timedelta(days=1)).isoformat()} UTC",
        f"- Effective full backtest range after startup: {base.stats.get('backtest_start')} through {base.stats.get('backtest_end')} UTC",
        f"- IS range: {start.isoformat()} through {(oos_start - timedelta(days=1)).isoformat()} UTC",
        f"- OOS range: {oos_start.isoformat()} through {(end_exclusive - timedelta(days=1)).isoformat()} UTC",
        f"- Effective OOS backtest range: {base_oos.stats.get('backtest_start')} through {base_oos.stats.get('backtest_end')} UTC",
        "- OOS policy: sealed final 30% by calendar time",
        "- Data source: Freqtrade Binance public spot JSON cache",
        "",
        "| Symbol | Rows | Start UTC | End UTC | Missing daily bars | File SHA256 |",
        "|---|---:|---|---|---:|---|",
    ]
    for profile in profiles:
        lines.append(f"| `{profile.symbol}` | {profile.rows} | `{profile.start_utc}` | `{profile.end_utc}` | {profile.gaps} | `{profile.sha256}` |")

    lines.extend(
        [
            "",
            "## Fixed Rules and Costs",
            "",
            "- Weekly Sunday-close decision, next daily open execution",
            "- close > SMA200 and positive 90-day return",
            "- stronger eligible asset wins; BTC wins exact ties; otherwise cash",
            "- one position, 50% maximum tradable equity, no short or leverage",
            "- emergency stoploss: -20%",
            "- Base cost: 0.15% per side (0.10% fee + 0.05% slippage equivalent)",
            "- Cost x2: 0.30% per side",
            "",
            "## Core Results",
            "",
            "| Run | Complete trades | Total return | Sharpe | Max drawdown | Final balance |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for run in (base, x2, base_oos, x2_oos):
        lines.append(
            f"| `{run.label}` | {len(run.complete_trades)} | {_pct(run.stats.get('profit_total'))} | "
            f"{_num(run.stats.get('sharpe')):.4f} | {_pct(run.stats.get('max_drawdown_account'))} | "
            f"{_num(run.stats.get('final_balance')):.4f} USDT |"
        )

    lines.extend(["", "## IS Segment Robustness", "", "| Segment | Range | Complete trades | Net return |", "|---|---|---:|---:|"])
    for run in segments:
        lines.append(
            f"| `{run.label}` | `{run.stats.get('backtest_start')} -> {run.stats.get('backtest_end')}` | "
            f"{len(run.complete_trades)} | {_pct(run.stats.get('profit_total'))} |"
        )

    yearly = base.stats.get("periodic_breakdown", {}).get("year", [])
    lines.extend(["", "## Annual Breakdown (Base)", "", "| Year | Trades | Profit |", "|---|---:|---:|"])
    for row in yearly:
        if row.get("profit_abs") is not None:
            year_return = _num(row.get("profit_abs")) / _num(base.stats.get("starting_balance"))
        else:
            year_return = _num(row.get("profit_total"))
        lines.append(f"| {row.get('date')} | {row.get('trades', 0)} | {_pct(year_return)} |")

    lines.extend(
        [
            "",
            "## Concentration and Extremes",
            "",
            f"- Return after deleting best 3 trades: {_pct(delete_best_three)}",
            f"- Best complete trade: `{best_trade.get('pair', 'not_available')}` {best_trade.get('open_date', '')} -> {best_trade.get('close_date', '')}, {_pct(best_trade.get('profit_ratio'))}",
            f"- Worst complete trade: `{worst_trade.get('pair', 'not_available')}` {worst_trade.get('open_date', '')} -> {worst_trade.get('close_date', '')}, {_pct(worst_trade.get('profit_ratio'))}",
            f"- lookahead-analysis: {'pass' if lookahead_pass else 'fail'}; signals={signals}, biased_entries={biased_entries}, biased_exits={biased_exits}",
            f"- recursive-analysis: {'pass' if recursive_pass else 'fail'}",
            "",
            "## Gate Matrix",
            "",
            "| Gate | Status |",
            "|---|---|",
        ]
    )
    for name, passed in gates.items():
        lines.append(f"| {name} | {'pass' if passed else 'fail'} |")

    lines.extend(["", "## Complete Trade Detail (Base)", "", "| # | Pair | Open UTC | Close UTC | Days | Exit | Profit |", "|---:|---|---|---|---:|---|---:|"])
    for index, trade in enumerate(completed, start=1):
        lines.append(
            f"| {index} | `{trade.get('pair')}` | `{trade.get('open_date')}` | `{trade.get('close_date')}` | "
            f"{_num(trade.get('trade_duration')) / 1440:.2f} | `{trade.get('exit_reason')}` | {_pct(trade.get('profit_ratio'))} |"
        )

    lines.extend(
        [
            "",
            "## Known Limitations",
            "",
            "- Freqtrade assumes backtest orders fill according to its candle model.",
            "- Slippage is represented conservatively through the per-side fee override, not an order-book replay.",
            "- M0 dual-source audit remains blocked independently; a numerical pass could not authorize M2 until P4 and M0 pass.",
            "- No parameters were selected from OOS or segment results.",
            "",
            "## Decision",
            "",
            (
                "Every fixed numerical gate passed, so the highest possible status is `under_review`; P4 and the M0 audit would still be required before any M2 discussion."
                if status == "under_review"
                else "At least one fixed gate failed. M1C is `failed_validation`; parameter rescue and progression to P4 or M2 are prohibited."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="append", required=True, help="LABEL=directory")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--lookahead-csv", type=Path, required=True)
    parser.add_argument("--recursive-log", type=Path, required=True)
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end-exclusive", type=date.fromisoformat, required=True)
    parser.add_argument("--oos-start", type=date.fromisoformat, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workflow-url", default="not_recorded")
    args = parser.parse_args()

    runs: dict[str, RunResult] = {}
    for mapping in args.run:
        label, separator, directory = mapping.partition("=")
        if not separator:
            raise SystemExit(f"invalid --run mapping: {mapping}")
        runs[label] = load_run(label, Path(directory))
    profiles = [
        profile_data(args.data_dir, symbol, args.start, args.end_exclusive)
        for symbol in ("BTC/USDT", "ETH/USDT")
    ]
    report = build_report(
        runs,
        profiles,
        args.lookahead_csv,
        args.recursive_log,
        args.start,
        args.end_exclusive,
        args.oos_start,
        args.workflow_url,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
