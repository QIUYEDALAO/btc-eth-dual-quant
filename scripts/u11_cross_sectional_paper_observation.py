#!/usr/bin/env python3
"""U-11 sealed-IS observation: frozen asymmetric-capture event core."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json, utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE, ONE_HOUR_MS, build_hourly_closes, build_membership, decimal_text, median, month_for_ms
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u06_cross_sectional_paper_observation import capture as capture_path_rows
from scripts.u10_cross_sectional_paper_observation import observe_paths as observe_base_paths

STEP_MS = 4 * ONE_HOUR_MS
LOOKBACK = 360
HALF = 180
PATH_MS = 72 * ONE_HOUR_MS
PROTOCOL_TARGET = "e7f621ec400fcb24833038f9201df5ffa5fa166a"
PROTOCOL_PATH = "config/u11_cross_sectional_paper_protocol_v1.json"
QUALIFICATION_HASH = "b0476b5e8cdd60769f49312e682329376daf5fa6f4163358d9bd4c84f0ca05b6"
QUALIFICATION_PATH = ROOT / "reports/m1/evidence/u11_cross_sectional_data_qualification_v1.json"


def capture(common: Sequence[Decimal], asset: Sequence[Decimal], positive: bool) -> Decimal | None:
    pairs = [(c, a) for c, a in zip(common, asset) if (c > 0 if positive else c < 0)]
    denominator = sum((c * c for c, _ in pairs), Decimal(0))
    if denominator <= 0:
        return None
    value = sum((c * a for c, a in pairs), Decimal(0)) / denominator
    return value if value.is_finite() else None


def window_stats(common: Sequence[Decimal], asset: Sequence[Decimal]) -> dict[str, Decimal] | None:
    positive = sum(value > 0 for value in common)
    negative = sum(value < 0 for value in common)
    required = (60, 60) if len(common) == LOOKBACK else (24, 24)
    if positive < required[0] or negative < required[1]:
        return None
    upside = capture(common, asset, True)
    downside = capture(common, asset, False)
    if upside is None or downside is None:
        return None
    return {"upside": upside, "downside": downside, "score": upside - downside}


def descending_scores(values: Mapping[str, Decimal]) -> dict[str, int]:
    ordered = sorted(values, key=lambda symbol: (-values[symbol], symbol))
    return {symbol: len(ordered) - index for index, symbol in enumerate(ordered)}


def select_events(
    returns_by_end: Mapping[int, Mapping[str, Decimal]],
    common_by_end: Mapping[int, Decimal],
    membership: Mapping[str, Sequence[str]],
    start: int,
    end: int,
    protocol_hash: str,
    qualification_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    events: list[dict[str, Any]] = []
    accounting = {"decision_times_considered": 0, "cross_section_ineligible": 0, "state_sample_ineligible": 0, "threshold_or_persistence_failed": 0, "simultaneous_candidates_discarded": 0}
    decision = start + LOOKBACK * STEP_MS
    with localcontext() as context:
        context.prec = 50
        while decision <= end:
            accounting["decision_times_considered"] += 1
            symbols = tuple(membership.get(month_for_ms(decision - 1), ()))
            ends = [decision - offset * STEP_MS for offset in range(LOOKBACK - 1, -1, -1)]
            if len(symbols) < 10 or any(value not in common_by_end for value in ends):
                accounting["cross_section_ineligible"] += 1
                decision += STEP_MS
                continue
            common = [common_by_end[value] for value in ends]
            stats: dict[str, tuple[dict[str, Decimal], dict[str, Decimal], dict[str, Decimal]]] = {}
            for symbol in symbols:
                if any(symbol not in returns_by_end[value] for value in ends):
                    continue
                asset = [returns_by_end[value][symbol] for value in ends]
                full = window_stats(common, asset)
                first = window_stats(common[:HALF], asset[:HALF])
                second = window_stats(common[HALF:], asset[HALF:])
                if full and first and second:
                    stats[symbol] = (full, first, second)
            if len(stats) < 10:
                accounting["state_sample_ineligible"] += 1
                decision += STEP_MS
                continue
            quartile = (len(stats) + 3) // 4
            rank_maps = [descending_scores({symbol: rows[index]["score"] for symbol, rows in stats.items()}) for index in range(3)]
            top_sets = [{symbol for symbol, _ in sorted(rank.items(), key=lambda item: (-item[1], item[0]))[:quartile]} for rank in rank_maps]
            candidates = [symbol for symbol in set.intersection(*top_sets) if stats[symbol][0]["upside"] >= Decimal("0.80") and stats[symbol][0]["downside"] <= Decimal("0.70") and stats[symbol][0]["score"] >= Decimal("0.30")]
            if not candidates:
                accounting["threshold_or_persistence_failed"] += 1
                decision += STEP_MS
                continue
            candidates.sort(key=lambda symbol: (-sum(rank[symbol] for rank in rank_maps), -stats[symbol][0]["score"], -stats[symbol][0]["upside"], stats[symbol][0]["downside"], symbol))
            accounting["simultaneous_candidates_discarded"] += len(candidates) - 1
            symbol = candidates[0]
            full, first, second = stats[symbol]
            core = {"decision_time_ms": decision - 1, "reference_open_time_ms": decision, "symbol": symbol, "active_members": list(symbols), "active_member_count": len(symbols), "full_upside_capture": decimal_text(full["upside"]), "full_downside_capture": decimal_text(full["downside"]), "full_asymmetric_capture_score": decimal_text(full["score"]), "first_half_score": decimal_text(first["score"]), "second_half_score": decimal_text(second["score"])}
            core["event_id"] = identity_hash({"protocol": protocol_hash, "qualification": qualification_hash, **core})
            events.append(core)
            decision += STEP_MS
    return events, accounting


def cluster_events(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    previous: int | None = None
    number = -1
    for event in sorted(events, key=lambda row: (int(row["decision_time_ms"]), str(row["symbol"]))):
        decision = int(event["decision_time_ms"])
        if previous is None or decision - previous > PATH_MS:
            number += 1
            row = dict(event)
            row["episode_id"] = identity_hash({"episode_number": number, "first_event_id": event["event_id"]})
            output.append(row)
        previous = decision
    return output


def build_returns(hourly: Mapping[str, Mapping[int, Decimal]], membership: Mapping[str, Sequence[str]], start: int, end: int) -> tuple[dict[int, dict[str, Decimal]], dict[int, Decimal]]:
    returns: dict[int, dict[str, Decimal]] = {}
    common: dict[int, Decimal] = {}
    with localcontext() as context:
        context.prec = 50
        boundary = start + STEP_MS
        while boundary <= end:
            members = tuple(membership.get(month_for_ms(boundary - 1), ()))
            row: dict[str, Decimal] = {}
            for symbol in members:
                closes = hourly.get(symbol, {})
                if boundary not in closes or boundary - STEP_MS not in closes:
                    break
                row[symbol] = (closes[boundary] / closes[boundary - STEP_MS]).ln()
            if len(row) == len(members) and len(row) >= 10:
                returns[boundary] = row
                common[boundary] = median(list(row.values()))
            boundary += STEP_MS
    return returns, common


def evaluate_gates(paths: Sequence[Mapping[str, Any]], protocol: Mapping[str, Any], mismatch: int) -> tuple[dict[str, Any], dict[str, bool]]:
    gates = protocol["paper_gates"]
    count = len(paths)
    years = Counter(datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).year for row in paths)
    symbols = Counter(str(row["symbol"]) for row in paths)
    months = Counter(datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).strftime("%Y-%m") for row in paths)
    relative = [Decimal(str(row["relative_quality_persistence"]["72"])) for row in paths]
    absolute = [Decimal(str(row["candidate_absolute_close_displacement"]["72"])) for row in paths]
    relative_median = median(relative) if paths else Decimal("NaN")
    absolute_median = median(absolute) if paths else Decimal("NaN")
    positive = Decimal(sum(value > 0 for value in relative)) / Decimal(count) if count else Decimal("NaN")
    year_share = Decimal(max(years.values(), default=count or 1)) / Decimal(count or 1)
    symbol_share = Decimal(max(symbols.values(), default=count or 1)) / Decimal(count or 1)
    full = count * 2373 // 1715
    oos = count * 658 // 1715
    metrics = {"complete_is_independent_episodes": count, "projected_full_independent_episodes": full, "projected_sealed_oos_independent_episodes": oos, "years_with_twelve_complete_episodes": sum(value >= 12 for value in years.values()), "episodes_by_year": {str(key): value for key, value in sorted(years.items())}, "maximum_single_year_episode_share": decimal_text(year_share), "episodes_by_symbol": dict(sorted(symbols.items())), "maximum_single_symbol_episode_share": decimal_text(symbol_share), "distinct_event_symbols": len(symbols), "distinct_event_months": len(months), "median_72h_relative_quality_persistence": decimal_text(relative_median) if relative_median.is_finite() else None, "median_72h_candidate_absolute_close_displacement": decimal_text(absolute_median) if absolute_median.is_finite() else None, "fraction_complete_episodes_with_positive_72h_relative_quality_persistence": decimal_text(positive) if positive.is_finite() else None, "qualification_quarantine_lifecycle_or_order_mismatches": mismatch}
    checks = {"complete_is_independent_episodes": count >= gates["complete_is_independent_episodes_minimum"], "projected_full_independent_episodes": full >= gates["projected_full_independent_episodes_minimum"], "projected_sealed_oos_independent_episodes": oos >= gates["projected_sealed_oos_independent_episodes_minimum"], "years_with_twelve_complete_episodes": metrics["years_with_twelve_complete_episodes"] >= gates["minimum_years_with_twelve_complete_episodes"], "maximum_single_year_episode_share": year_share <= Decimal(gates["maximum_single_year_episode_share"]), "maximum_single_symbol_episode_share": symbol_share <= Decimal(gates["maximum_single_symbol_episode_share"]), "distinct_event_symbols": len(symbols) >= gates["minimum_distinct_event_symbols"], "distinct_event_months": len(months) >= gates["minimum_distinct_event_months"], "median_72h_relative_quality_persistence": relative_median.is_finite() and relative_median >= Decimal(gates["combined_median_72h_relative_quality_persistence_minimum"]), "median_72h_candidate_absolute_close_displacement": absolute_median.is_finite() and absolute_median >= Decimal(gates["combined_median_72h_candidate_absolute_close_displacement_minimum"]), "fraction_positive_72h_relative_quality_persistence": positive.is_finite() and positive >= Decimal(gates["fraction_complete_episodes_with_positive_72h_relative_quality_persistence_minimum"]), "authority_and_order_mismatches": mismatch <= gates["qualification_quarantine_lifecycle_or_order_mismatches_maximum"]}
    return metrics, checks


def wrap(name: str, content: Any) -> dict[str, Any]:
    document = {"schema_version": 1, "manifest_type": f"u11_{name}_manifest", "content": content}
    document["content_hash"] = identity_hash(document)
    return document


def run_order(raw_root: Path, protocol: Mapping[str, Any], qualification: Mapping[str, Any], order: str) -> dict[str, Any]:
    start = utc_ms(protocol["scope"]["is_start"]); end = utc_ms(protocol["scope"]["is_end_exclusive"])
    membership = build_membership(load_json(EVIDENCE / "membership_manifest.json"))
    masked = {(str(row["symbol"]), int(row["open_time_ms"])) for row in load_json(EVIDENCE / "invalid_interval_slot_mask_manifest.json")["content"]}
    hourly = build_hourly_closes(raw_root=raw_root, membership=membership, masked_slots=masked, is_start_ms=start, is_end_ms=end, order=order)
    returns, common = build_returns(hourly, membership, start, end)
    events, accounting = select_events(returns, common, membership, start, end, protocol["content_hash"], qualification["qualification_content_hash"])
    episodes = cluster_events(events)
    captured, pre_censored = capture_path_rows(raw_root, episodes, membership, masked, start, end, order)
    base_paths, censor_counts = observe_base_paths(episodes, captured, pre_censored)
    paths = []
    for row in base_paths:
        converted = dict(row)
        converted["relative_quality_persistence"] = converted.pop("relative_continuation")
        paths.append(converted)
    content = {"events": events, "episodes": episodes, "paths": paths, "accounting": {**accounting, "common_state_boundaries": len(common), "candidate_events": len(events), "independent_episodes": len(episodes), "complete_72h_episodes": len(paths), "right_censored_episodes": len(episodes) - len(paths), "right_censor_reasons": dict(sorted(censor_counts.items())), "oos_rows_decoded": 0, "formal_returns_computed": 0, "fills_positions_or_equity_rows": 0}}
    manifests = {name: wrap(name, content[name]) for name in ("events", "episodes", "paths", "accounting")}
    hashes = {name: manifests[name]["content_hash"] for name in sorted(manifests)}
    return {"order": order, "manifests": manifests, "manifest_hashes": hashes, "content_identity_hash": identity_hash(hashes)}


def execute(raw_root: Path) -> dict[str, Any]:
    protocol = git_json(PROTOCOL_TARGET, PROTOCOL_PATH); qualification = load_json(QUALIFICATION_PATH)
    if qualification.get("qualification_content_hash") != QUALIFICATION_HASH:
        raise ValueError("qualification drift")
    runs = [run_order(raw_root, protocol, qualification, order) for order in ("normal", "reverse", "deterministic_shuffled")]
    mismatch = 0 if len({run["content_identity_hash"] for run in runs}) == 1 else 1
    primary = runs[0]; metrics, checks = evaluate_gates(primary["manifests"]["paths"]["content"], protocol, mismatch)
    status = "pass" if all(checks.values()) else "failed_feasibility"
    summary = {"schema_version": 1, "run_id": "U11-06-SEALED-IS-PAPER-OBSERVATION-V1", "status": status, "protocol_target_commit": PROTOCOL_TARGET, "protocol_content_hash": protocol["content_hash"], "qualification_content_hash": qualification["qualification_content_hash"], "is_start": protocol["scope"]["is_start"], "is_end_exclusive": protocol["scope"]["is_end_exclusive"], "orders": [{"order": run["order"], "content_identity_hash": run["content_identity_hash"], "manifest_hashes": run["manifest_hashes"]} for run in runs], "metrics": metrics, "paper_gate_checks": checks, "oos_opened": False, "oos_rows_decoded": 0, "formal_returns_computed": False, "fills_positions_or_equity_generated": False, "parameters_changed_after_result": False, "second_run_executed": False, "network_accessed": False, "authorizations": {"paper_result_independent_review": status == "pass", "lifecycle_or_fixed_rule_work": False, "strategy": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}}
    summary["run_content_hash"] = identity_hash(summary)
    return {"summary": summary, "manifests": primary["manifests"]}


def render(result: Mapping[str, Any]) -> str:
    summary = result["summary"]; metrics = summary["metrics"]
    lines = ["# U-11 Sealed-IS Paper Observation", "", f"- Status: `{summary['status']}`", f"- Run hash: `{summary['run_content_hash']}`", f"- Complete independent episodes: `{metrics['complete_is_independent_episodes']}`", "", "## Frozen Paper Gates", "", *[f"- {key}: `{str(value).lower()}`" for key, value in summary["paper_gate_checks"].items()], "", "## Metrics", "", f"- Projected full / sealed OOS episodes: `{metrics['projected_full_independent_episodes']} / {metrics['projected_sealed_oos_independent_episodes']}`", f"- Median 72h relative quality persistence: `{metrics['median_72h_relative_quality_persistence']}`", f"- Median 72h absolute displacement: `{metrics['median_72h_candidate_absolute_close_displacement']}`", f"- Positive relative fraction: `{metrics['fraction_complete_episodes_with_positive_72h_relative_quality_persistence']}`", "", "## Isolation", "", "- OOS opened / rows decoded: `false / 0`", "- Formal returns, fills, positions or equity generated: `false`", "- Parameters changed or second run executed: `false / false`", "", "A failed Gate closes U-11 without tuning. A pass authorizes only independent Paper-result review.", ""]
    return "\n".join(lines)


def historical_attempt_main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe"); parser.add_argument("--evidence-dir", type=Path, default=ROOT / "reports/m1/evidence/u11_cross_sectional_paper_observation"); parser.add_argument("--report", type=Path, default=ROOT / "reports/m1/U11_CROSS_SECTIONAL_PAPER_OBSERVATION.md"); args = parser.parse_args()
    result = execute(args.raw_root); args.evidence_dir.mkdir(parents=True, exist_ok=True)
    for name, document in result["manifests"].items(): (args.evidence_dir / f"{name}.json").write_text(json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n")
    (args.evidence_dir / "run_manifest.json").write_text(json.dumps(result["summary"], sort_keys=True, separators=(",", ":")) + "\n"); args.report.write_text(render(result)); print(json.dumps(result["summary"], sort_keys=True, separators=(",", ":")))
    return 0 if result["summary"]["status"] == "pass" else 1


def main() -> int:
    print(
        "U-11 is closed as failed_execution_invalid_observation; "
        "a repair or second result-bearing run is not authorized.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
