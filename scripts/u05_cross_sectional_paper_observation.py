#!/usr/bin/env python3
"""Execute the single preregistered U-05 sealed-IS Paper observation."""
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

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json, utc_ms
from scripts.u04_cross_sectional_paper_observation import (
    EVIDENCE,
    FIVE_MINUTES_MS,
    HORIZONS,
    ONE_HOUR_MS,
    ObservationFailure,
    build_hourly_closes,
    build_membership,
    decimal_text,
    median,
    month_for_ms,
    ordered,
    read_five_minute_rows,
)
from scripts.u05_cross_sectional_data_qualification import git_json


FOUR_HOURS_MS = 4 * ONE_HOUR_MS
ONE_DAY_MS = 24 * ONE_HOUR_MS
PROTOCOL_TARGET = "8d8652796e22a15285ba682b4524baa0218ca5a6"
PROTOCOL_PATH = "config/u05_cross_sectional_paper_protocol_v1.json"
QUALIFICATION_HASH = "348e80291ced6f7cbbb929c0b88c6bbce0b86e23cdbed33718b884810df7cb4f"


def select_events(
    *, hourly_closes: Mapping[str, Mapping[int, Decimal]],
    membership: Mapping[str, Sequence[str]], is_start_ms: int, is_end_ms: int,
    protocol_hash: str, qualification_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    events: list[dict[str, Any]] = []
    accounting = {
        "decision_times_considered": 0, "decision_times_evaluated": 0,
        "cross_section_ineligible": 0, "breadth_gate_failed": 0,
        "common_move_gate_failed": 0,
    }
    with localcontext() as context:
        context.prec = 50
        decision = is_start_ms + 2 * FOUR_HOURS_MS
        if decision % FOUR_HOURS_MS:
            decision += FOUR_HOURS_MS - decision % FOUR_HOURS_MS
        while decision <= is_end_ms:
            accounting["decision_times_considered"] += 1
            symbols = membership.get(month_for_ms(decision - 1))
            if symbols is None or len(symbols) < 10:
                accounting["cross_section_ineligible"] += 1
                decision += FOUR_HOURS_MS
                continue
            returns: dict[str, Decimal] = {}
            for symbol in symbols:
                closes = hourly_closes.get(symbol, {})
                if any(closes.get(decision - offset * ONE_HOUR_MS) is None for offset in range(8)):
                    break
                current = closes[decision]
                previous = closes[decision - FOUR_HOURS_MS]
                returns[str(symbol)] = current / previous - Decimal(1)
            if len(returns) != len(symbols):
                accounting["cross_section_ineligible"] += 1
                decision += FOUR_HOURS_MS
                continue
            accounting["decision_times_evaluated"] += 1
            positive = sum(value > 0 for value in returns.values())
            if positive * 5 < len(symbols) * 4:
                accounting["breadth_gate_failed"] += 1
                decision += FOUR_HOURS_MS
                continue
            common = median(list(returns.values()))
            if common < Decimal("0.0120"):
                accounting["common_move_gate_failed"] += 1
                decision += FOUR_HOURS_MS
                continue
            core = {
                "decision_time_ms": decision - 1,
                "reference_open_time_ms": decision,
                "active_members": list(symbols),
                "active_member_count": len(symbols),
                "positive_member_count": positive,
                "breadth_fraction": decimal_text(Decimal(positive) / Decimal(len(symbols))),
                "cross_sectional_median_4h_simple_return": decimal_text(common),
                "member_4h_simple_returns": {symbol: decimal_text(value) for symbol, value in sorted(returns.items())},
            }
            core["event_id"] = identity_hash({"protocol": protocol_hash, "qualification": qualification_hash, **core})
            events.append(core)
            decision += FOUR_HOURS_MS
    return events, accounting


def cluster_events(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    representatives: list[dict[str, Any]] = []
    previous_candidate: int | None = None
    episode_number = -1
    for event in sorted(events, key=lambda item: int(item["decision_time_ms"])):
        decision = int(event["decision_time_ms"])
        if previous_candidate is None or decision - previous_candidate > ONE_DAY_MS:
            episode_number += 1
            row = dict(event)
            row["episode_id"] = identity_hash({"episode_number": episode_number, "first_event_id": event["event_id"]})
            representatives.append(row)
        previous_candidate = decision
    return representatives


def lifecycle_ends() -> dict[str, int]:
    availability = load_json(EVIDENCE / "symbol_availability_manifest.json")["content"]
    return {str(row["symbol"]): utc_ms(str(row["end_exclusive"])) for row in availability if row.get("end_exclusive")}


def capture_path_rows(
    *, raw_root: Path, episodes: Sequence[Mapping[str, Any]],
    membership: Mapping[str, Sequence[str]], masked_slots: set[tuple[str, int]],
    is_start_ms: int, is_end_ms: int, order: str,
) -> tuple[dict[tuple[str, int], tuple[Decimal, Decimal, Decimal, Decimal]], dict[str, str]]:
    required: dict[tuple[str, str], set[int]] = defaultdict(set)
    censored: dict[str, str] = {}
    ends = lifecycle_ends()
    for episode in episodes:
        episode_id = str(episode["episode_id"])
        reference = int(episode["reference_open_time_ms"])
        end = reference + ONE_DAY_MS
        active = tuple(str(symbol) for symbol in episode["active_members"])
        if end > is_end_ms:
            censored[episode_id] = "sealed_is_boundary"
            continue
        if any(reference <= ends.get(symbol, end + 1) < end for symbol in active):
            censored[episode_id] = "lifecycle_intersection"
            continue
        times = list(range(reference, end, FIVE_MINUTES_MS))
        if any(tuple(membership.get(month_for_ms(opened), ())) != active for opened in times):
            censored[episode_id] = "membership_change"
            continue
        for opened in times:
            month = month_for_ms(opened)
            for symbol in active:
                required[(symbol, month)].add(opened)
    captured: dict[tuple[str, int], tuple[Decimal, Decimal, Decimal, Decimal]] = {}
    for symbol, month in ordered(required, order, key=lambda item: (item[1], item[0])):
        wanted = required[(symbol, month)]
        for opened, opened_value, high, low, close in read_five_minute_rows(
            raw_root, symbol, month, is_start_ms=is_start_ms, is_end_ms=is_end_ms,
        ):
            if opened in wanted and (symbol, opened) not in masked_slots:
                captured[(symbol, opened)] = (opened_value, high, low, close)
    return captured, censored


def observe_paths(
    episodes: Sequence[Mapping[str, Any]],
    captured: Mapping[tuple[str, int], tuple[Decimal, Decimal, Decimal, Decimal]],
    censored: Mapping[str, str],
) -> tuple[list[dict[str, Any]], Counter[str]]:
    paths: list[dict[str, Any]] = []
    censor_counts: Counter[str] = Counter(censored.values())
    with localcontext() as context:
        context.prec = 50
        for episode in episodes:
            episode_id = str(episode["episode_id"])
            if episode_id in censored:
                continue
            reference = int(episode["reference_open_time_ms"])
            symbols = [str(symbol) for symbol in episode["active_members"]]
            times = [reference + index * FIVE_MINUTES_MS for index in range(288)]
            if any((symbol, opened) not in captured for symbol in symbols for opened in times):
                censor_counts["missing_or_quarantined_5m"] += 1
                continue
            reference_opens = {symbol: captured[(symbol, reference)][0] for symbol in symbols}
            median_path: list[Decimal] = []
            positive_path: list[Decimal] = []
            for opened in times:
                displacements = [captured[(symbol, opened)][3] / reference_opens[symbol] - Decimal(1) for symbol in symbols]
                median_path.append(median(displacements))
                positive_path.append(Decimal(sum(value > 0 for value in displacements)) / Decimal(len(symbols)))
            close_by_horizon = {str(h): decimal_text(median_path[h * 12 - 1]) for h in HORIZONS}
            positive_by_horizon = {str(h): decimal_text(positive_path[h * 12 - 1]) for h in HORIZONS}
            first_base = next(((index + 1) * 5 for index, value in enumerate(median_path) if value >= Decimal("0.0030")), None)
            paths.append({
                "episode_id": episode_id, "event_id": episode["event_id"],
                "decision_time_ms": int(episode["decision_time_ms"]),
                "reference_open_time_ms": reference, "member_count": len(symbols),
                "common_demand_close_displacement": close_by_horizon,
                "positive_member_fraction": positive_by_horizon,
                "maximum_favorable_excursion_24h": decimal_text(max(median_path)),
                "maximum_adverse_excursion_24h": decimal_text(min(median_path)),
                "first_base_cost_recovery_minutes": first_base,
                "complete_24h": True,
            })
    return paths, censor_counts


def evaluate_gates(paths: Sequence[Mapping[str, Any]], protocol: Mapping[str, Any], *, mismatch_count: int) -> tuple[dict[str, Any], dict[str, bool]]:
    gates = protocol["paper_gates"]
    count = len(paths)
    years = Counter(datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).year for row in paths)
    quarters = Counter(datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).strftime("%Y-Q") + str((datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).month - 1) // 3 + 1) for row in paths)
    months = Counter(datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).strftime("%Y-%m") for row in paths)
    projected_full = count * int(protocol["scope"]["full_calendar_days"]) // int(protocol["scope"]["is_calendar_days"])
    projected_oos = count * int(protocol["scope"]["oos_calendar_days"]) // int(protocol["scope"]["is_calendar_days"])
    median_close = median([Decimal(str(row["common_demand_close_displacement"]["24"])) for row in paths]) if paths else Decimal("NaN")
    median_positive = median([Decimal(str(row["positive_member_fraction"]["24"])) for row in paths]) if paths else Decimal("NaN")
    year_share = Decimal(max(years.values(), default=count or 1)) / Decimal(count or 1)
    quarter_share = Decimal(max(quarters.values(), default=count or 1)) / Decimal(count or 1)
    metrics = {
        "complete_is_independent_episodes": count,
        "projected_full_independent_episodes": projected_full,
        "projected_sealed_oos_independent_episodes": projected_oos,
        "years_with_ten_complete_episodes": sum(value >= 10 for value in years.values()),
        "episodes_by_year": {str(key): value for key, value in sorted(years.items())},
        "maximum_single_year_episode_share": decimal_text(year_share),
        "episodes_by_quarter": dict(sorted(quarters.items())),
        "maximum_single_calendar_quarter_episode_share": decimal_text(quarter_share),
        "distinct_event_months": len(months),
        "median_24h_common_demand_close_displacement": decimal_text(median_close) if median_close.is_finite() else None,
        "median_24h_positive_member_fraction": decimal_text(median_positive) if median_positive.is_finite() else None,
        "qualification_quarantine_lifecycle_or_order_mismatches": mismatch_count,
    }
    checks = {
        "complete_is_independent_episodes": count >= int(gates["complete_is_independent_episodes_minimum"]),
        "projected_full_independent_episodes": projected_full >= int(gates["projected_full_independent_episodes_minimum"]),
        "projected_sealed_oos_independent_episodes": projected_oos >= int(gates["projected_sealed_oos_independent_episodes_minimum"]),
        "years_with_ten_complete_episodes": metrics["years_with_ten_complete_episodes"] >= int(gates["minimum_years_with_ten_complete_episodes"]),
        "maximum_single_year_episode_share": year_share <= Decimal(str(gates["maximum_single_year_episode_share"])),
        "maximum_single_calendar_quarter_episode_share": quarter_share <= Decimal(str(gates["maximum_single_calendar_quarter_episode_share"])),
        "distinct_event_months": len(months) >= int(gates["minimum_distinct_event_months"]),
        "median_24h_common_demand_close_displacement": median_close.is_finite() and median_close >= Decimal(str(gates["combined_median_24h_common_demand_close_displacement_minimum"])),
        "median_24h_positive_member_fraction": median_positive.is_finite() and median_positive >= Decimal(str(gates["combined_median_24h_positive_member_fraction_minimum"])),
        "authority_and_order_mismatches": mismatch_count <= int(gates["qualification_quarantine_lifecycle_or_order_mismatches_maximum"]),
    }
    return metrics, checks


def wrap(manifest_type: str, content: Any) -> dict[str, Any]:
    document = {"schema_version": 1, "manifest_type": manifest_type, "content": content}
    document["content_hash"] = identity_hash(document)
    return document


def run_order(*, raw_root: Path, protocol: Mapping[str, Any], qualification: Mapping[str, Any], order: str) -> dict[str, Any]:
    if qualification.get("qualification_content_hash") != QUALIFICATION_HASH:
        raise ObservationFailure("data qualification binding changed")
    is_start_ms = utc_ms(protocol["scope"]["is_start"])
    is_end_ms = utc_ms(protocol["scope"]["is_end_exclusive"])
    membership = build_membership(load_json(EVIDENCE / "membership_manifest.json"))
    masked = {(str(row["symbol"]), int(row["open_time_ms"])) for row in load_json(EVIDENCE / "invalid_interval_slot_mask_manifest.json")["content"]}
    hourly = build_hourly_closes(raw_root=raw_root, membership=membership, masked_slots=masked, is_start_ms=is_start_ms, is_end_ms=is_end_ms, order=order)
    events, scan_accounting = select_events(
        hourly_closes=hourly, membership=membership, is_start_ms=is_start_ms, is_end_ms=is_end_ms,
        protocol_hash=protocol["content_hash"], qualification_hash=qualification["qualification_content_hash"],
    )
    episodes = cluster_events(events)
    captured, pre_censored = capture_path_rows(
        raw_root=raw_root, episodes=episodes, membership=membership, masked_slots=masked,
        is_start_ms=is_start_ms, is_end_ms=is_end_ms, order=order,
    )
    paths, censor_counts = observe_paths(episodes, captured, pre_censored)
    content = {
        "events": sorted(events, key=lambda item: int(item["decision_time_ms"])),
        "episodes": sorted(episodes, key=lambda item: int(item["decision_time_ms"])),
        "paths": sorted(paths, key=lambda item: int(item["decision_time_ms"])),
        "accounting": {
            **scan_accounting, "candidate_events": len(events), "independent_episodes": len(episodes),
            "complete_24h_episodes": len(paths), "right_censored_episodes": len(episodes) - len(paths),
            "right_censor_reasons": dict(sorted(censor_counts.items())), "oos_rows_decoded": 0,
            "formal_returns_computed": 0, "fills_positions_or_equity_rows": 0,
        },
    }
    manifests = {name: wrap(f"u05_{name}_manifest", content[name]) for name in ("events", "episodes", "paths", "accounting")}
    hashes = {name: manifests[name]["content_hash"] for name in sorted(manifests)}
    return {"order": order, "manifests": manifests, "manifest_hashes": hashes, "content_identity_hash": identity_hash(hashes)}


def execute(*, raw_root: Path) -> dict[str, Any]:
    protocol = git_json(PROTOCOL_TARGET, PROTOCOL_PATH)
    qualification = load_json(ROOT / "reports/m1/evidence/u05_cross_sectional_data_qualification_v1.json")
    runs = [run_order(raw_root=raw_root, protocol=protocol, qualification=qualification, order=order) for order in ("normal", "reverse", "deterministic_shuffled")]
    mismatch = 0 if len({run["content_identity_hash"] for run in runs}) == 1 else 1
    primary = runs[0]
    metrics, checks = evaluate_gates(primary["manifests"]["paths"]["content"], protocol, mismatch_count=mismatch)
    status = "pass" if all(checks.values()) else "failed_feasibility"
    summary = {
        "schema_version": 1, "run_id": "U05-06-SEALED-IS-PAPER-OBSERVATION-V1", "status": status,
        "protocol_content_hash": protocol["content_hash"], "qualification_content_hash": qualification["qualification_content_hash"],
        "is_start": protocol["scope"]["is_start"], "is_end_exclusive": protocol["scope"]["is_end_exclusive"],
        "orders": [{"order": run["order"], "content_identity_hash": run["content_identity_hash"], "manifest_hashes": run["manifest_hashes"]} for run in runs],
        "metrics": metrics, "paper_gate_checks": checks, "oos_opened": False, "oos_rows_decoded": 0,
        "formal_returns_computed": False, "fills_positions_or_equity_generated": False,
        "parameters_changed_after_result": False, "second_run_executed": False, "network_accessed": False,
        "authorizations": {
            "paper_result_independent_review": status == "pass", "lifecycle_or_fixed_rule_work": False,
            "strategy": False, "backtesting": False, "oos": False, "api_trading": False,
            "execution_live": False, "m2": False,
        },
    }
    summary["run_content_hash"] = identity_hash(summary)
    return {"summary": summary, "manifests": primary["manifests"]}


def render_report(result: Mapping[str, Any]) -> str:
    summary, metrics = result["summary"], result["summary"]["metrics"]
    lines = [
        "# U-05 Sealed-IS Paper Observation", "", f"- Status: `{summary['status']}`",
        f"- Run hash: `{summary['run_content_hash']}`",
        f"- Complete independent episodes: `{metrics['complete_is_independent_episodes']}`", "",
        "## Frozen Paper Gates", "",
    ]
    lines.extend(f"- {key}: `{str(value).lower()}`" for key, value in summary["paper_gate_checks"].items())
    lines.extend([
        "", "## Metrics", "",
        f"- Projected full / sealed OOS episodes: `{metrics['projected_full_independent_episodes']} / {metrics['projected_sealed_oos_independent_episodes']}`",
        f"- Years with at least ten complete episodes: `{metrics['years_with_ten_complete_episodes']}`",
        f"- Maximum year / quarter share: `{metrics['maximum_single_year_episode_share']} / {metrics['maximum_single_calendar_quarter_episode_share']}`",
        f"- Distinct event months: `{metrics['distinct_event_months']}`",
        f"- Median 24h common-demand close displacement: `{metrics['median_24h_common_demand_close_displacement']}`",
        f"- Median 24h positive-member fraction: `{metrics['median_24h_positive_member_fraction']}`",
        "", "## Isolation", "", "- OOS opened / rows decoded: `false / 0`",
        "- Formal returns, fills, positions or equity generated: `false`",
        "- Parameters changed or second run executed: `false / false`", "",
        "A failed Gate closes the candidate without tuning. A pass authorizes only an independent Paper-result review; it does not authorize fixed rules, strategy code, backtesting, OOS, trading or M2.", "",
    ])
    return "\n".join(lines)


def write_result(result: Mapping[str, Any], evidence_dir: Path, report: Path) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for name, document in result["manifests"].items():
        (evidence_dir / f"{name}.json").write_text(json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n", encoding="utf-8")
    (evidence_dir / "run_manifest.json").write_text(json.dumps(result["summary"], sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n", encoding="utf-8")
    report.write_text(render_report(result), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe")
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "reports/m1/evidence/u05_cross_sectional_paper_observation")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/m1/U05_CROSS_SECTIONAL_PAPER_OBSERVATION.md")
    args = parser.parse_args()
    result = execute(raw_root=args.raw_root)
    write_result(result, args.evidence_dir, args.report)
    print(json.dumps(result["summary"], sort_keys=True, separators=(",", ":")))
    return 0 if result["summary"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
