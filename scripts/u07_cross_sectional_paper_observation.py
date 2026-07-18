#!/usr/bin/env python3
"""Execute the single preregistered U-07 sealed-IS Paper observation."""
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
PATH_MS = 48 * ONE_HOUR_MS
HORIZONS = (1, 2, 4, 8, 12, 24, 48)
PROTOCOL_TARGET = "3aed4c337ff984b3e07ad9a4c7cda898425b3791"
PROTOCOL_PATH = "config/u07_cross_sectional_paper_protocol_v1.json"
QUALIFICATION_HASH = "fa65f34089854cd5faf950234b3488eb64b3058d1ab47f3dab500bbfb395e123"


def select_events(
    *, hourly_closes: Mapping[str, Mapping[int, Decimal]],
    membership: Mapping[str, Sequence[str]], is_start_ms: int, is_end_ms: int,
    protocol_hash: str, qualification_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    events: list[dict[str, Any]] = []
    accounting = {
        "decision_times_considered": 0,
        "decision_times_evaluated": 0,
        "cross_section_ineligible": 0,
        "market_stress_gate_failed": 0,
        "negative_breadth_gate_failed": 0,
        "resilience_gate_failed": 0,
        "simultaneous_candidates_discarded": 0,
    }
    decision = is_start_ms + 2 * FOUR_HOURS_MS
    if decision % FOUR_HOURS_MS:
        decision += FOUR_HOURS_MS - decision % FOUR_HOURS_MS
    with localcontext() as context:
        context.prec = 50
        while decision <= is_end_ms:
            accounting["decision_times_considered"] += 1
            symbols = membership.get(month_for_ms(decision - 1))
            if symbols is None or len(symbols) < 10:
                accounting["cross_section_ineligible"] += 1
                decision += FOUR_HOURS_MS
                continue
            simple_returns: dict[str, Decimal] = {}
            log_returns: dict[str, Decimal] = {}
            for symbol in symbols:
                closes = hourly_closes.get(symbol, {})
                if any(closes.get(decision - offset * ONE_HOUR_MS) is None for offset in range(8)):
                    break
                log_return = (closes[decision] / closes[decision - FOUR_HOURS_MS]).ln()
                log_returns[str(symbol)] = log_return
                simple_returns[str(symbol)] = log_return.exp() - Decimal(1)
            if len(simple_returns) != len(symbols):
                accounting["cross_section_ineligible"] += 1
                decision += FOUR_HOURS_MS
                continue
            accounting["decision_times_evaluated"] += 1
            common = median(list(simple_returns.values()))
            if common > Decimal("-0.0250"):
                accounting["market_stress_gate_failed"] += 1
                decision += FOUR_HOURS_MS
                continue
            negative = sum(value < 0 for value in simple_returns.values())
            if negative * 5 < len(symbols) * 4:
                accounting["negative_breadth_gate_failed"] += 1
                decision += FOUR_HOURS_MS
                continue
            candidates = []
            for symbol in symbols:
                residual = simple_returns[symbol] - common
                if residual >= Decimal("0.0200") and simple_returns[symbol] >= Decimal("-0.0050"):
                    candidates.append((symbol, residual, simple_returns[symbol]))
            if not candidates:
                accounting["resilience_gate_failed"] += 1
                decision += FOUR_HOURS_MS
                continue
            candidates.sort(key=lambda item: (-item[1], -item[2], item[0]))
            accounting["simultaneous_candidates_discarded"] += len(candidates) - 1
            symbol, residual, simple_return = candidates[0]
            core = {
                "decision_time_ms": decision - 1,
                "reference_open_time_ms": decision,
                "symbol": symbol,
                "active_members": list(symbols),
                "active_member_count": len(symbols),
                "negative_member_count": negative,
                "negative_breadth_fraction": decimal_text(Decimal(negative) / Decimal(len(symbols))),
                "cross_sectional_median_4h_simple_return": decimal_text(common),
                "candidate_4h_log_return": decimal_text(log_returns[symbol]),
                "candidate_4h_simple_return": decimal_text(simple_return),
                "candidate_relative_residual": decimal_text(residual),
                "member_4h_simple_returns": {
                    member: decimal_text(value) for member, value in sorted(simple_returns.items())
                },
            }
            core["event_id"] = identity_hash({
                "protocol": protocol_hash,
                "qualification": qualification_hash,
                **core,
            })
            events.append(core)
            decision += FOUR_HOURS_MS
    return events, accounting


def cluster_events(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    representatives: list[dict[str, Any]] = []
    previous_candidate: int | None = None
    episode_number = -1
    for event in sorted(events, key=lambda item: int(item["decision_time_ms"])):
        decision = int(event["decision_time_ms"])
        if previous_candidate is None or decision - previous_candidate > PATH_MS:
            episode_number += 1
            row = dict(event)
            row["episode_id"] = identity_hash({
                "episode_number": episode_number,
                "first_event_id": event["event_id"],
            })
            representatives.append(row)
        previous_candidate = decision
    return representatives


def lifecycle_ends() -> dict[str, int]:
    availability = load_json(EVIDENCE / "symbol_availability_manifest.json")["content"]
    return {
        str(row["symbol"]): utc_ms(str(row["end_exclusive"]))
        for row in availability if row.get("end_exclusive")
    }


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
        stop = reference + PATH_MS
        active = tuple(str(symbol) for symbol in episode["active_members"])
        if stop > is_end_ms:
            censored[episode_id] = "sealed_is_boundary"
            continue
        if any(reference <= ends.get(symbol, stop + 1) < stop for symbol in active):
            censored[episode_id] = "lifecycle_intersection"
            continue
        times = list(range(reference, stop, FIVE_MINUTES_MS))
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
            candidate = str(episode["symbol"])
            peers = [str(symbol) for symbol in episode["active_members"] if symbol != candidate]
            times = [reference + index * FIVE_MINUTES_MS for index in range(576)]
            if any((symbol, opened) not in captured for symbol in [candidate, *peers] for opened in times):
                censor_counts["missing_or_quarantined_5m"] += 1
                continue
            reference_opens = {
                symbol: captured[(symbol, reference)][0] for symbol in [candidate, *peers]
            }
            absolute: list[Decimal] = []
            peer_medians: list[Decimal] = []
            relative: list[Decimal] = []
            for opened in times:
                candidate_move = captured[(candidate, opened)][3] / reference_opens[candidate] - Decimal(1)
                peer_move = median([
                    captured[(peer, opened)][3] / reference_opens[peer] - Decimal(1)
                    for peer in peers
                ])
                absolute.append(candidate_move)
                peer_medians.append(peer_move)
                relative.append(candidate_move - peer_move)
            paths.append({
                "episode_id": episode_id,
                "event_id": episode["event_id"],
                "symbol": candidate,
                "decision_time_ms": int(episode["decision_time_ms"]),
                "reference_open_time_ms": reference,
                "peer_count": len(peers),
                "candidate_absolute_close_displacement": {
                    str(horizon): decimal_text(absolute[horizon * 12 - 1]) for horizon in HORIZONS
                },
                "peer_median_close_displacement": {
                    str(horizon): decimal_text(peer_medians[horizon * 12 - 1]) for horizon in HORIZONS
                },
                "relative_continuation": {
                    str(horizon): decimal_text(relative[horizon * 12 - 1]) for horizon in HORIZONS
                },
                "candidate_maximum_favorable_excursion_48h": decimal_text(max(absolute)),
                "candidate_maximum_adverse_excursion_48h": decimal_text(min(absolute)),
                "first_base_cost_relative_continuation_minutes": next(
                    ((index + 1) * 5 for index, value in enumerate(relative) if value >= Decimal("0.0030")),
                    None,
                ),
                "complete_48h": True,
            })
    return paths, censor_counts


def evaluate_gates(
    paths: Sequence[Mapping[str, Any]], protocol: Mapping[str, Any], *, mismatch_count: int,
) -> tuple[dict[str, Any], dict[str, bool]]:
    gates = protocol["paper_gates"]
    count = len(paths)
    years = Counter(
        datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).year
        for row in paths
    )
    symbols = Counter(str(row["symbol"]) for row in paths)
    months = Counter(
        datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).strftime("%Y-%m")
        for row in paths
    )
    projected_full = count * int(protocol["scope"]["full_calendar_days"]) // int(protocol["scope"]["is_calendar_days"])
    projected_oos = count * int(protocol["scope"]["oos_calendar_days"]) // int(protocol["scope"]["is_calendar_days"])
    relative_values = [Decimal(str(row["relative_continuation"]["24"])) for row in paths]
    absolute_values = [Decimal(str(row["candidate_absolute_close_displacement"]["24"])) for row in paths]
    relative_median = median(relative_values) if paths else Decimal("NaN")
    absolute_median = median(absolute_values) if paths else Decimal("NaN")
    positive_fraction = Decimal(sum(value > 0 for value in relative_values)) / Decimal(count) if count else Decimal("NaN")
    year_share = Decimal(max(years.values(), default=count or 1)) / Decimal(count or 1)
    symbol_share = Decimal(max(symbols.values(), default=count or 1)) / Decimal(count or 1)
    metrics = {
        "complete_is_independent_episodes": count,
        "projected_full_independent_episodes": projected_full,
        "projected_sealed_oos_independent_episodes": projected_oos,
        "years_with_eight_complete_episodes": sum(value >= 8 for value in years.values()),
        "episodes_by_year": {str(key): value for key, value in sorted(years.items())},
        "maximum_single_year_episode_share": decimal_text(year_share),
        "episodes_by_symbol": dict(sorted(symbols.items())),
        "maximum_single_symbol_episode_share": decimal_text(symbol_share),
        "distinct_event_symbols": len(symbols),
        "distinct_event_months": len(months),
        "median_24h_relative_continuation": decimal_text(relative_median) if relative_median.is_finite() else None,
        "median_24h_candidate_absolute_close_displacement": decimal_text(absolute_median) if absolute_median.is_finite() else None,
        "fraction_complete_episodes_with_positive_24h_relative_continuation": decimal_text(positive_fraction) if positive_fraction.is_finite() else None,
        "qualification_quarantine_lifecycle_or_order_mismatches": mismatch_count,
    }
    checks = {
        "complete_is_independent_episodes": count >= int(gates["complete_is_independent_episodes_minimum"]),
        "projected_full_independent_episodes": projected_full >= int(gates["projected_full_independent_episodes_minimum"]),
        "projected_sealed_oos_independent_episodes": projected_oos >= int(gates["projected_sealed_oos_independent_episodes_minimum"]),
        "years_with_eight_complete_episodes": metrics["years_with_eight_complete_episodes"] >= int(gates["minimum_years_with_eight_complete_episodes"]),
        "maximum_single_year_episode_share": year_share <= Decimal(str(gates["maximum_single_year_episode_share"])),
        "maximum_single_symbol_episode_share": symbol_share <= Decimal(str(gates["maximum_single_symbol_episode_share"])),
        "distinct_event_symbols": len(symbols) >= int(gates["minimum_distinct_event_symbols"]),
        "distinct_event_months": len(months) >= int(gates["minimum_distinct_event_months"]),
        "median_24h_relative_continuation": relative_median.is_finite() and relative_median >= Decimal(str(gates["combined_median_24h_relative_continuation_minimum"])),
        "median_24h_candidate_absolute_close_displacement": absolute_median.is_finite() and absolute_median >= Decimal(str(gates["combined_median_24h_candidate_absolute_close_displacement_minimum"])),
        "fraction_positive_24h_relative_continuation": positive_fraction.is_finite() and positive_fraction >= Decimal(str(gates["fraction_complete_episodes_with_positive_24h_relative_continuation_minimum"])),
        "authority_and_order_mismatches": mismatch_count <= int(gates["qualification_quarantine_lifecycle_or_order_mismatches_maximum"]),
    }
    return metrics, checks


def wrap(name: str, content: Any) -> dict[str, Any]:
    document = {"schema_version": 1, "manifest_type": f"u07_{name}_manifest", "content": content}
    document["content_hash"] = identity_hash(document)
    return document


def run_order(
    *, raw_root: Path, protocol: Mapping[str, Any], qualification: Mapping[str, Any], order: str,
) -> dict[str, Any]:
    if qualification.get("qualification_content_hash") != QUALIFICATION_HASH:
        raise ObservationFailure("data qualification binding changed")
    start = utc_ms(protocol["scope"]["is_start"])
    end = utc_ms(protocol["scope"]["is_end_exclusive"])
    membership = build_membership(load_json(EVIDENCE / "membership_manifest.json"))
    masked = {
        (str(row["symbol"]), int(row["open_time_ms"]))
        for row in load_json(EVIDENCE / "invalid_interval_slot_mask_manifest.json")["content"]
    }
    hourly = build_hourly_closes(
        raw_root=raw_root, membership=membership, masked_slots=masked,
        is_start_ms=start, is_end_ms=end, order=order,
    )
    events, scan_accounting = select_events(
        hourly_closes=hourly, membership=membership, is_start_ms=start, is_end_ms=end,
        protocol_hash=protocol["content_hash"],
        qualification_hash=qualification["qualification_content_hash"],
    )
    episodes = cluster_events(events)
    captured, pre_censored = capture_path_rows(
        raw_root=raw_root, episodes=episodes, membership=membership, masked_slots=masked,
        is_start_ms=start, is_end_ms=end, order=order,
    )
    paths, censor_counts = observe_paths(episodes, captured, pre_censored)
    content = {
        "events": sorted(events, key=lambda row: int(row["decision_time_ms"])),
        "episodes": sorted(episodes, key=lambda row: int(row["decision_time_ms"])),
        "paths": sorted(paths, key=lambda row: int(row["decision_time_ms"])),
        "accounting": {
            **scan_accounting,
            "candidate_events": len(events),
            "independent_episodes": len(episodes),
            "complete_48h_episodes": len(paths),
            "right_censored_episodes": len(episodes) - len(paths),
            "right_censor_reasons": dict(sorted(censor_counts.items())),
            "oos_rows_decoded": 0,
            "formal_returns_computed": 0,
            "fills_positions_or_equity_rows": 0,
        },
    }
    manifests = {name: wrap(name, content[name]) for name in ("events", "episodes", "paths", "accounting")}
    hashes = {name: manifests[name]["content_hash"] for name in sorted(manifests)}
    return {
        "order": order,
        "manifests": manifests,
        "manifest_hashes": hashes,
        "content_identity_hash": identity_hash(hashes),
    }


def execute(*, raw_root: Path) -> dict[str, Any]:
    protocol = git_json(PROTOCOL_TARGET, PROTOCOL_PATH)
    qualification = load_json(ROOT / "reports/m1/evidence/u07_cross_sectional_data_qualification_v1.json")
    runs = [
        run_order(raw_root=raw_root, protocol=protocol, qualification=qualification, order=order)
        for order in ("normal", "reverse", "deterministic_shuffled")
    ]
    mismatch = 0 if len({run["content_identity_hash"] for run in runs}) == 1 else 1
    primary = runs[0]
    metrics, checks = evaluate_gates(
        primary["manifests"]["paths"]["content"], protocol, mismatch_count=mismatch,
    )
    status = "pass" if all(checks.values()) else "failed_feasibility"
    summary = {
        "schema_version": 1,
        "run_id": "U07-06-SEALED-IS-PAPER-OBSERVATION-V1",
        "status": status,
        "protocol_content_hash": protocol["content_hash"],
        "qualification_content_hash": qualification["qualification_content_hash"],
        "is_start": protocol["scope"]["is_start"],
        "is_end_exclusive": protocol["scope"]["is_end_exclusive"],
        "orders": [
            {"order": run["order"], "content_identity_hash": run["content_identity_hash"], "manifest_hashes": run["manifest_hashes"]}
            for run in runs
        ],
        "metrics": metrics,
        "paper_gate_checks": checks,
        "oos_opened": False,
        "oos_rows_decoded": 0,
        "formal_returns_computed": False,
        "fills_positions_or_equity_generated": False,
        "parameters_changed_after_result": False,
        "second_run_executed": False,
        "network_accessed": False,
        "authorizations": {
            "paper_result_independent_review": status == "pass",
            "lifecycle_or_fixed_rule_work": False,
            "strategy": False,
            "backtesting": False,
            "oos": False,
            "api_trading": False,
            "execution_live": False,
            "m2": False,
        },
    }
    summary["run_content_hash"] = identity_hash(summary)
    return {"summary": summary, "manifests": primary["manifests"]}


def render_report(result: Mapping[str, Any]) -> str:
    summary = result["summary"]
    metrics = summary["metrics"]
    lines = [
        "# U-07 Sealed-IS Paper Observation", "",
        f"- Status: `{summary['status']}`",
        f"- Run hash: `{summary['run_content_hash']}`",
        f"- Complete independent episodes: `{metrics['complete_is_independent_episodes']}`", "",
        "## Frozen Paper Gates", "",
    ]
    lines.extend(f"- {key}: `{str(value).lower()}`" for key, value in summary["paper_gate_checks"].items())
    lines.extend([
        "", "## Metrics", "",
        f"- Projected full / sealed OOS episodes: `{metrics['projected_full_independent_episodes']} / {metrics['projected_sealed_oos_independent_episodes']}`",
        f"- Distinct event symbols / months: `{metrics['distinct_event_symbols']} / {metrics['distinct_event_months']}`",
        f"- Median 24h relative continuation: `{metrics['median_24h_relative_continuation']}`",
        f"- Median 24h candidate absolute displacement: `{metrics['median_24h_candidate_absolute_close_displacement']}`",
        f"- Positive 24h relative-continuation fraction: `{metrics['fraction_complete_episodes_with_positive_24h_relative_continuation']}`",
        "", "## Isolation", "",
        "- OOS opened / rows decoded: `false / 0`",
        "- Formal returns, fills, positions or equity generated: `false`",
        "- Parameters changed or second run executed: `false / false`", "",
        "A failed Gate closes U-07 without tuning. A pass authorizes only independent Paper-result review.", "",
    ])
    return "\n".join(lines)


def write_result(result: Mapping[str, Any], evidence_dir: Path, report: Path) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for name, document in result["manifests"].items():
        (evidence_dir / f"{name}.json").write_text(
            json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
    (evidence_dir / "run_manifest.json").write_text(
        json.dumps(result["summary"], sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    report.write_text(render_report(result), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe")
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "reports/m1/evidence/u07_cross_sectional_paper_observation")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/m1/U07_CROSS_SECTIONAL_PAPER_OBSERVATION.md")
    args = parser.parse_args()
    result = execute(raw_root=args.raw_root)
    write_result(result, args.evidence_dir, args.report)
    print(json.dumps(result["summary"], sort_keys=True, separators=(",", ":")))
    return 0 if result["summary"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
