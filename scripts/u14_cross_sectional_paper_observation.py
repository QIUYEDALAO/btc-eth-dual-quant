#!/usr/bin/env python3
"""Execute the single frozen U-14 sealed-IS Paper observation."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.data.u14_downside_rejection import AuctionPathRow, evaluate_decision
from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json, utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE, FIVE_MINUTES_MS, ONE_HOUR_MS, ObservationFailure, build_membership, decimal_text, median, month_for_ms, ordered, read_five_minute_rows
from scripts.u05_cross_sectional_data_qualification import git_json

FOUR_HOURS_MS = 4 * ONE_HOUR_MS
PATH_MS = 24 * ONE_HOUR_MS
HORIZONS = (1, 2, 4, 8, 12, 24)
PROTOCOL_TARGET = "dd8eb34aa0cae8455ba15163831b992820461ebf"
PROTOCOL_PATH = "config/u14_cross_sectional_paper_protocol_v1.json"
QUALIFICATION_HASH = "4db5eb7938cbf7f8063a00164fa6986d53629968ea0a8a4516de01e3a859dec5"


def build_auctions(*, raw_root: Path, membership: Mapping[str, Sequence[str]], masked: set[tuple[str, int]], start: int, end: int, order: str) -> dict[int, dict[str, tuple[Decimal, Decimal, Decimal, Decimal]]]:
    tasks = sorted({(symbol, month) for month, symbols in membership.items() for symbol in symbols if month <= month_for_ms(end - 1)})
    accum: dict[tuple[int, str], list[Any]] = {}
    for symbol, month in ordered(tasks, order, key=lambda item: (item[1], item[0])):
        for opened, open_value, high, low, close in read_five_minute_rows(raw_root, symbol, month, is_start_ms=start, is_end_ms=end):
            if symbol not in membership.get(month_for_ms(opened), ()) or (symbol, opened) in masked:
                continue
            block = opened - opened % FOUR_HOURS_MS
            decision = block + FOUR_HOURS_MS
            key = (decision, symbol)
            row = accum.get(key)
            if row is None:
                accum[key] = [1, opened, opened, open_value, high, low, close]
            else:
                row[0] += 1; row[2] = opened; row[4] = max(row[4], high); row[5] = min(row[5], low); row[6] = close
    auctions: dict[int, dict[str, tuple[Decimal, Decimal, Decimal, Decimal]]] = defaultdict(dict)
    for (decision, symbol), row in accum.items():
        block = decision - FOUR_HOURS_MS
        if row[0] == 48 and row[1] == block and row[2] == decision - FIVE_MINUTES_MS:
            auctions[decision][symbol] = (row[3], row[4], row[5], row[6])
    return {decision: values for decision, values in auctions.items() if tuple(sorted(values)) == tuple(sorted(membership.get(month_for_ms(decision - 1), ()))) and len(values) >= 10}


def select_events(auctions: Mapping[int, Mapping[str, tuple[Decimal, Decimal, Decimal, Decimal]]], membership: Mapping[str, Sequence[str]], protocol_hash: str, qualification_hash: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    events: list[dict[str, Any]] = []
    accounting = {"decision_times_evaluated": 0, "cross_section_ineligible": 0, "common_or_event_gate_failed": 0, "candidate_events": 0}
    for decision, values in sorted(auctions.items()):
        symbols = tuple(membership.get(month_for_ms(decision - 1), ()))
        if tuple(sorted(values)) != tuple(sorted(symbols)):
            accounting["cross_section_ineligible"] += 1; continue
        accounting["decision_times_evaluated"] += 1
        rows = [AuctionPathRow(decision, symbol, *(float(value) for value in values[symbol]), float(values[symbol][3]), (float(values[symbol][3]),) * 6) for symbol in symbols]
        selected = evaluate_decision(rows, minimum_members=10)
        if selected is None:
            accounting["common_or_event_gate_failed"] += 1; continue
        symbol = selected.symbol
        open_value, high, low, close = values[symbol]
        with localcontext() as context:
            context.prec = 50
            log_returns = {member: (values[member][3] / values[member][0]).ln() for member in symbols}
            close_locations = {member: (values[member][3] - values[member][2]) / (values[member][1] - values[member][2]) for member in symbols}
            residual = close_locations[symbol] - median([close_locations[member] for member in symbols if member != symbol])
            core = {"decision_time_ms": decision - 1, "reference_open_time_ms": decision, "symbol": symbol, "active_members": list(symbols), "active_member_count": len(symbols), "negative_member_count": sum(value < 0 for value in log_returns.values()), "common_4h_log_return": decimal_text(median(list(log_returns.values()))), "candidate_4h_log_return": decimal_text(log_returns[symbol]), "candidate_normalized_range": decimal_text((high - low) / open_value), "candidate_downside_excursion": decimal_text(low / open_value - Decimal(1)), "candidate_close_location": decimal_text(close_locations[symbol]), "candidate_close_location_residual": decimal_text(residual)}
        core["event_id"] = identity_hash({"protocol": protocol_hash, "qualification": qualification_hash, **core})
        events.append(core); accounting["candidate_events"] += 1
    return events, accounting


def cluster_events(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    representatives: list[dict[str, Any]] = []
    previous: int | None = None
    episode_number = -1
    for event in sorted(events, key=lambda row: int(row["decision_time_ms"])):
        decision = int(event["decision_time_ms"])
        if previous is None or decision - previous > PATH_MS:
            episode_number += 1
            row = dict(event); row["episode_id"] = identity_hash({"episode_number": episode_number, "first_event_id": event["event_id"]}); representatives.append(row)
        previous = decision
    return representatives


def lifecycle_ends() -> dict[str, int]:
    return {str(row["symbol"]): utc_ms(str(row["end_exclusive"])) for row in load_json(EVIDENCE / "symbol_availability_manifest.json")["content"] if row.get("end_exclusive")}


def capture_paths(*, raw_root: Path, episodes: Sequence[Mapping[str, Any]], membership: Mapping[str, Sequence[str]], masked: set[tuple[str, int]], start: int, end: int, order: str) -> tuple[dict[tuple[str, int], tuple[Decimal, Decimal, Decimal, Decimal]], dict[str, str]]:
    required: dict[tuple[str, str], set[int]] = defaultdict(set)
    censored: dict[str, str] = {}
    ends = lifecycle_ends()
    for episode in episodes:
        episode_id, reference = str(episode["episode_id"]), int(episode["reference_open_time_ms"])
        stop = reference + PATH_MS
        active = tuple(str(symbol) for symbol in episode["active_members"])
        if stop > end: censored[episode_id] = "sealed_is_boundary"; continue
        if any(reference <= ends.get(symbol, stop + 1) < stop for symbol in active): censored[episode_id] = "lifecycle_intersection"; continue
        times = range(reference, stop, FIVE_MINUTES_MS)
        if any(tuple(membership.get(month_for_ms(opened), ())) != active for opened in times): censored[episode_id] = "membership_change"; continue
        for opened in times:
            for symbol in active: required[(symbol, month_for_ms(opened))].add(opened)
    captured: dict[tuple[str, int], tuple[Decimal, Decimal, Decimal, Decimal]] = {}
    for symbol, month in ordered(required, order, key=lambda item: (item[1], item[0])):
        wanted = required[(symbol, month)]
        for opened, open_value, high, low, close in read_five_minute_rows(raw_root, symbol, month, is_start_ms=start, is_end_ms=end):
            if opened in wanted and (symbol, opened) not in masked: captured[(symbol, opened)] = (open_value, high, low, close)
    return captured, censored


def observe_paths(episodes: Sequence[Mapping[str, Any]], captured: Mapping[tuple[str, int], tuple[Decimal, Decimal, Decimal, Decimal]], censored: Mapping[str, str]) -> tuple[list[dict[str, Any]], Counter[str]]:
    paths: list[dict[str, Any]] = []; censor_counts: Counter[str] = Counter(censored.values())
    with localcontext() as context:
        context.prec = 50
        for episode in episodes:
            episode_id = str(episode["episode_id"])
            if episode_id in censored: continue
            reference, candidate = int(episode["reference_open_time_ms"]), str(episode["symbol"])
            peers = [str(symbol) for symbol in episode["active_members"] if symbol != candidate]
            times = [reference + index * FIVE_MINUTES_MS for index in range(288)]
            members = [candidate, *peers]
            if any((symbol, opened) not in captured for symbol in members for opened in times): censor_counts["missing_or_quarantined_5m"] += 1; continue
            reference_opens = {symbol: captured[(symbol, reference)][0] for symbol in members}
            absolute, peer_medians, relative = [], [], []
            highs, lows = [], []
            for opened in times:
                absolute_move = captured[(candidate, opened)][3] / reference_opens[candidate] - Decimal(1)
                peer_move = median([captured[(peer, opened)][3] / reference_opens[peer] - Decimal(1) for peer in peers])
                absolute.append(absolute_move); peer_medians.append(peer_move); relative.append(absolute_move - peer_move)
                highs.append(captured[(candidate, opened)][1] / reference_opens[candidate] - Decimal(1)); lows.append(captured[(candidate, opened)][2] / reference_opens[candidate] - Decimal(1))
            paths.append({"episode_id": episode_id, "event_id": episode["event_id"], "symbol": candidate, "decision_time_ms": int(episode["decision_time_ms"]), "reference_open_time_ms": reference, "peer_count": len(peers), "candidate_absolute_close_displacement": {str(h): decimal_text(absolute[h * 12 - 1]) for h in HORIZONS}, "peer_median_close_displacement": {str(h): decimal_text(peer_medians[h * 12 - 1]) for h in HORIZONS}, "relative_rejection_persistence": {str(h): decimal_text(relative[h * 12 - 1]) for h in HORIZONS}, "candidate_maximum_favorable_excursion_24h": decimal_text(max(highs)), "candidate_maximum_adverse_excursion_24h": decimal_text(min(lows)), "first_base_cost_relative_recovery_minutes": next(((index + 1) * 5 for index, value in enumerate(relative) if value >= Decimal("0.0030")), None), "complete_24h": True})
    return paths, censor_counts


def evaluate_gates(paths: Sequence[Mapping[str, Any]], protocol: Mapping[str, Any], mismatch_count: int) -> tuple[dict[str, Any], dict[str, bool]]:
    count = len(paths)
    years = Counter(datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).year for row in paths)
    symbols = Counter(str(row["symbol"]) for row in paths)
    months = Counter(datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).strftime("%Y-%m") for row in paths)
    projected_full = count * 2373 // 1715; projected_oos = count * 658 // 1715
    relative = [Decimal(str(row["relative_rejection_persistence"]["24"])) for row in paths]; absolute = [Decimal(str(row["candidate_absolute_close_displacement"]["24"])) for row in paths]
    rel_median = median(relative) if paths else Decimal("NaN"); abs_median = median(absolute) if paths else Decimal("NaN"); positive = Decimal(sum(value > 0 for value in relative)) / Decimal(count) if count else Decimal("NaN")
    year_share = Decimal(max(years.values(), default=count or 1)) / Decimal(count or 1); symbol_share = Decimal(max(symbols.values(), default=count or 1)) / Decimal(count or 1)
    metrics = {"complete_is_independent_episodes": count, "projected_full_independent_episodes": projected_full, "projected_sealed_oos_independent_episodes": projected_oos, "years_with_twelve_complete_episodes": sum(value >= 12 for value in years.values()), "episodes_by_year": {str(k): v for k, v in sorted(years.items())}, "maximum_single_year_episode_share": decimal_text(year_share), "episodes_by_symbol": dict(sorted(symbols.items())), "maximum_single_symbol_episode_share": decimal_text(symbol_share), "distinct_event_symbols": len(symbols), "distinct_event_months": len(months), "median_24h_relative_rejection_persistence": decimal_text(rel_median) if rel_median.is_finite() else None, "median_24h_candidate_absolute_close_displacement": decimal_text(abs_median) if abs_median.is_finite() else None, "fraction_complete_episodes_with_positive_24h_relative_rejection_persistence": decimal_text(positive) if positive.is_finite() else None, "qualification_preflight_complexity_quarantine_lifecycle_or_order_mismatches": mismatch_count}
    checks = {"complete_is_independent_episodes": count >= 90, "projected_full_independent_episodes": projected_full >= 120, "projected_sealed_oos_independent_episodes": projected_oos >= 30, "years_with_twelve_complete_episodes": metrics["years_with_twelve_complete_episodes"] >= 4, "maximum_single_year_episode_share": year_share <= Decimal("0.35"), "maximum_single_symbol_episode_share": symbol_share <= Decimal("0.25"), "distinct_event_symbols": len(symbols) >= 8, "distinct_event_months": len(months) >= 30, "median_24h_relative_rejection_persistence": rel_median.is_finite() and rel_median >= Decimal("0.0180"), "median_24h_candidate_absolute_close_displacement": abs_median.is_finite() and abs_median >= Decimal("0.0180"), "fraction_positive_24h_relative_rejection_persistence": positive.is_finite() and positive >= Decimal("0.60"), "authority_and_order_mismatches": mismatch_count <= 0}
    return metrics, checks


def wrap(name: str, content: Any) -> dict[str, Any]:
    document = {"schema_version": 1, "manifest_type": f"u14_{name}_manifest", "content": content}; document["content_hash"] = identity_hash(document); return document


def run_order(raw_root: Path, protocol: Mapping[str, Any], qualification: Mapping[str, Any], order: str) -> dict[str, Any]:
    if qualification.get("qualification_content_hash") != QUALIFICATION_HASH: raise ObservationFailure("qualification binding changed")
    start, end = utc_ms(protocol["scope"]["is_start"]), utc_ms(protocol["scope"]["is_end_exclusive"])
    membership = build_membership(load_json(EVIDENCE / "membership_manifest.json")); masked = {(str(row["symbol"]), int(row["open_time_ms"])) for row in load_json(EVIDENCE / "invalid_interval_slot_mask_manifest.json")["content"]}
    auctions = build_auctions(raw_root=raw_root, membership=membership, masked=masked, start=start, end=end, order=order)
    events, scan = select_events(auctions, membership, protocol["content_hash"], QUALIFICATION_HASH); episodes = cluster_events(events)
    captured, precensored = capture_paths(raw_root=raw_root, episodes=episodes, membership=membership, masked=masked, start=start, end=end, order=order); paths, censors = observe_paths(episodes, captured, precensored)
    content = {"events": sorted(events, key=lambda row: int(row["decision_time_ms"])), "episodes": sorted(episodes, key=lambda row: int(row["decision_time_ms"])), "paths": sorted(paths, key=lambda row: int(row["decision_time_ms"])), "accounting": {**scan, "independent_episodes": len(episodes), "complete_24h_episodes": len(paths), "right_censored_episodes": len(episodes) - len(paths), "right_censor_reasons": dict(sorted(censors.items())), "oos_rows_decoded": 0, "formal_returns_computed": 0, "fills_positions_or_equity_rows": 0}}
    manifests = {name: wrap(name, content[name]) for name in content}; hashes = {name: manifests[name]["content_hash"] for name in sorted(manifests)}
    return {"order": order, "manifests": manifests, "manifest_hashes": hashes, "content_identity_hash": identity_hash(hashes)}


def execute(raw_root: Path) -> dict[str, Any]:
    protocol = git_json(PROTOCOL_TARGET, PROTOCOL_PATH); qualification = load_json(ROOT / "reports/m1/evidence/u14_cross_sectional_data_qualification_v1.json")
    runs = [run_order(raw_root, protocol, qualification, order) for order in ("normal", "reverse", "deterministic_shuffled")]
    mismatch = 0 if len({run["content_identity_hash"] for run in runs}) == 1 else 1; primary = runs[0]
    metrics, checks = evaluate_gates(primary["manifests"]["paths"]["content"], protocol, mismatch); status = "pass" if all(checks.values()) else "failed_feasibility"
    summary = {"schema_version": 1, "run_id": "U14-06-SEALED-IS-PAPER-OBSERVATION-V1", "status": status, "protocol_content_hash": protocol["content_hash"], "qualification_content_hash": QUALIFICATION_HASH, "orders": [{"order": run["order"], "content_identity_hash": run["content_identity_hash"], "manifest_hashes": run["manifest_hashes"]} for run in runs], "metrics": metrics, "paper_gate_checks": checks, "oos_opened": False, "oos_rows_decoded": 0, "formal_returns_computed": False, "fills_positions_or_equity_generated": False, "parameters_changed_after_result": False, "second_run_executed": False, "network_accessed": False, "authorizations": {"paper_result_independent_review": status == "pass", "lifecycle_or_fixed_rule_work": False, "strategy": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}}; summary["run_content_hash"] = identity_hash(summary)
    return {"summary": summary, "manifests": primary["manifests"]}


def render_report(result: Mapping[str, Any]) -> str:
    s, m = result["summary"], result["summary"]["metrics"]
    lines = ["# U-14 Sealed-IS Paper Observation", "", f"- Status: `{s['status']}`", f"- Run hash: `{s['run_content_hash']}`", f"- Complete independent episodes: `{m['complete_is_independent_episodes']}`", "", "## Frozen Paper Gates", ""]
    lines += [f"- {key}: `{str(value).lower()}`" for key, value in s["paper_gate_checks"].items()]
    lines += ["", "## Metrics", "", f"- Projected full / sealed OOS episodes: `{m['projected_full_independent_episodes']} / {m['projected_sealed_oos_independent_episodes']}`", f"- Distinct symbols / months: `{m['distinct_event_symbols']} / {m['distinct_event_months']}`", f"- Median 24h relative rejection persistence: `{m['median_24h_relative_rejection_persistence']}`", f"- Median 24h absolute displacement: `{m['median_24h_candidate_absolute_close_displacement']}`", f"- Positive relative-persistence fraction: `{m['fraction_complete_episodes_with_positive_24h_relative_rejection_persistence']}`", "", "## Isolation", "", "- OOS opened / rows decoded: `false / 0`", "- Formal returns, fills, positions or equity generated: `false`", "- Parameters changed or second run executed: `false / false`", "", "Any failed Gate closes U-14 without tuning. A pass authorizes only an independent Paper-result review.", ""]
    return "\n".join(lines)


def write_result(result: Mapping[str, Any], evidence_dir: Path, report: Path) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for name, document in result["manifests"].items(): (evidence_dir / f"{name}.json").write_text(json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n")
    (evidence_dir / "run_manifest.json").write_text(json.dumps(result["summary"], sort_keys=True, separators=(",", ":")) + "\n"); report.write_text(render_report(result))


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe"); parser.add_argument("--evidence-dir", type=Path, default=ROOT / "reports/m1/evidence/u14_cross_sectional_paper_observation"); parser.add_argument("--report", type=Path, default=ROOT / "reports/m1/U14_CROSS_SECTIONAL_PAPER_OBSERVATION.md"); args = parser.parse_args()
    if (args.evidence_dir / "run_manifest.json").exists():
        print("U-14 is closed after its unique Paper observation; a second result-bearing run is not authorized.")
        return 2
    result = execute(args.raw_root); write_result(result, args.evidence_dir, args.report); print(json.dumps(result["summary"], sort_keys=True, separators=(",", ":"))); return 0 if result["summary"]["status"] == "pass" else 1


if __name__ == "__main__": raise SystemExit(main())
