#!/usr/bin/env python3
"""Execute the single preregistered U-10 sealed-IS Paper observation."""
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
from scripts.u04_cross_sectional_paper_observation import (
    EVIDENCE,
    FIVE_MINUTES_MS,
    ONE_DAY_MS,
    ObservationFailure,
    build_membership,
    decimal_text,
    median,
    month_for_ms,
)
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u06_cross_sectional_paper_observation import build_daily, capture


PROTOCOL_TARGET = "f468b7aeaaf02f803125b4ab6037086fb353776f"
PROTOCOL_PATH = "config/u10_cross_sectional_paper_protocol_v1.json"
QUALIFICATION_HASH = "0029def278eeadf6b3951e1e1f62d16b0919889950eb68e0cdd3fe97fe727ee2"
QUALIFICATION_PATH = ROOT / "reports/m1/evidence/u10_cross_sectional_data_qualification_v1.json"
HORIZONS = (1, 2, 4, 8, 12, 24, 48, 72)
PATH_MS = 72 * 60 * 60 * 1000


def descending_scores(values: Mapping[str, Decimal]) -> dict[str, int]:
    ordered = sorted(values, key=lambda symbol: (-values[symbol], symbol))
    count = len(ordered)
    return {symbol: count - index for index, symbol in enumerate(ordered)}


def select_events(
    daily: Mapping[str, Mapping[int, Mapping[str, Decimal]]],
    membership: Mapping[str, Sequence[str]],
    start: int,
    end: int,
    protocol_hash: str,
    qualification_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    events: list[dict[str, Any]] = []
    accounting = {
        "days_considered": 0,
        "days_evaluated": 0,
        "cross_section_ineligible": 0,
        "relative_trend_gate_failed": 0,
        "volume_share_gate_failed": 0,
        "joint_candidate_days": 0,
        "simultaneous_candidates_discarded": 0,
    }
    day = ((start + ONE_DAY_MS - 1) // ONE_DAY_MS) * ONE_DAY_MS
    with localcontext() as context:
        context.prec = 50
        while day + ONE_DAY_MS <= end:
            accounting["days_considered"] += 1
            symbols = tuple(membership.get(month_for_ms(day), ()))
            history_days = [day - offset * ONE_DAY_MS for offset in range(28, 0, -1)]
            if len(symbols) < 10:
                accounting["cross_section_ineligible"] += 1
                day += ONE_DAY_MS
                continue
            eligible = True
            shares: dict[str, dict[int, Decimal]] = {symbol: {} for symbol in symbols}
            for historical_day in [*history_days, day]:
                historical_members = tuple(membership.get(month_for_ms(historical_day), ()))
                if any(symbol not in historical_members for symbol in symbols):
                    eligible = False
                    break
                rows = {symbol: daily.get(symbol, {}).get(historical_day) for symbol in historical_members}
                if any(row is None for row in rows.values()):
                    eligible = False
                    break
                total_quote = sum((rows[symbol]["quote"] for symbol in historical_members), Decimal(0))
                if total_quote <= 0:
                    eligible = False
                    break
                for symbol in symbols:
                    shares[symbol][historical_day] = rows[symbol]["quote"] / total_quote
            if not eligible:
                accounting["cross_section_ineligible"] += 1
                day += ONE_DAY_MS
                continue
            closes = {
                symbol: (
                    daily[symbol][day]["close"],
                    daily[symbol][day - 7 * ONE_DAY_MS]["close"],
                )
                for symbol in symbols
            }
            log_returns = {
                symbol: (current / prior).ln() for symbol, (current, prior) in closes.items()
            }
            common = median(list(log_returns.values()))
            trends = {symbol: log_returns[symbol] - common for symbol in symbols}
            ratios: dict[str, Decimal] = {}
            persistent: dict[str, bool] = {}
            for symbol in symbols:
                recent = [shares[symbol][day - offset * ONE_DAY_MS] for offset in (2, 1, 0)]
                baseline = [shares[symbol][day - offset * ONE_DAY_MS] for offset in range(23, 2, -1)]
                baseline_median = median(baseline)
                ratios[symbol] = median(recent) / baseline_median if baseline_median > 0 else Decimal(0)
                persistent[symbol] = baseline_median > 0 and all(value > baseline_median for value in recent)
            accounting["days_evaluated"] += 1
            quartile_size = (len(symbols) + 3) // 4
            trend_order = sorted(symbols, key=lambda symbol: (-trends[symbol], symbol))
            ratio_order = sorted(symbols, key=lambda symbol: (-ratios[symbol], symbol))
            trend_set = set(trend_order[:quartile_size])
            ratio_set = set(ratio_order[:quartile_size])
            trend_pass = {
                symbol for symbol in trend_set if trends[symbol] >= Decimal("0.0300")
            }
            ratio_pass = {
                symbol for symbol in ratio_set
                if ratios[symbol] >= Decimal("1.25") and persistent[symbol]
            }
            if not trend_pass:
                accounting["relative_trend_gate_failed"] += 1
            if not ratio_pass:
                accounting["volume_share_gate_failed"] += 1
            candidates = sorted(trend_pass & ratio_pass)
            if candidates:
                accounting["joint_candidate_days"] += 1
                trend_scores = descending_scores(trends)
                ratio_scores = descending_scores(ratios)
                candidates.sort(key=lambda symbol: (
                    -(trend_scores[symbol] + ratio_scores[symbol]),
                    -trends[symbol], -ratios[symbol], symbol,
                ))
                accounting["simultaneous_candidates_discarded"] += len(candidates) - 1
                symbol = candidates[0]
                core = {
                    "decision_time_ms": day + ONE_DAY_MS - 1,
                    "reference_open_time_ms": day + ONE_DAY_MS,
                    "symbol": symbol,
                    "active_members": list(symbols),
                    "active_member_count": len(symbols),
                    "candidate_7d_log_return": decimal_text(log_returns[symbol]),
                    "cross_sectional_median_7d_log_return": decimal_text(common),
                    "candidate_relative_trend": decimal_text(trends[symbol]),
                    "candidate_recent_3d_median_volume_share": decimal_text(median([
                        shares[symbol][day - offset * ONE_DAY_MS] for offset in (2, 1, 0)
                    ])),
                    "candidate_preceding_21d_median_volume_share": decimal_text(median([
                        shares[symbol][day - offset * ONE_DAY_MS] for offset in range(23, 2, -1)
                    ])),
                    "candidate_volume_share_ratio": decimal_text(ratios[symbol]),
                    "candidate_trend_rank_score": trend_scores[symbol],
                    "candidate_volume_share_rank_score": ratio_scores[symbol],
                }
                core["event_id"] = identity_hash({
                    "protocol": protocol_hash,
                    "qualification": qualification_hash,
                    **core,
                })
                events.append(core)
            day += ONE_DAY_MS
    return events, accounting


def cluster_events(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    representatives: list[dict[str, Any]] = []
    previous_candidate: int | None = None
    episode_number = -1
    for event in sorted(events, key=lambda row: (int(row["decision_time_ms"]), str(row["symbol"]))):
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


def observe_paths(
    episodes: Sequence[Mapping[str, Any]],
    captured: Mapping[tuple[str, int], tuple[Decimal, Decimal, Decimal, Decimal]],
    censored: Mapping[str, str],
) -> tuple[list[dict[str, Any]], Counter[str]]:
    paths: list[dict[str, Any]] = []
    counts: Counter[str] = Counter(censored.values())
    with localcontext() as context:
        context.prec = 50
        for episode in episodes:
            episode_id = str(episode["episode_id"])
            if episode_id in censored:
                continue
            reference = int(episode["reference_open_time_ms"])
            candidate = str(episode["symbol"])
            peers = [str(symbol) for symbol in episode["active_members"] if symbol != candidate]
            times = [reference + index * FIVE_MINUTES_MS for index in range(864)]
            if any((symbol, opened) not in captured for symbol in [candidate, *peers] for opened in times):
                counts["missing_or_quarantined_5m"] += 1
                continue
            reference_opens = {symbol: captured[(symbol, reference)][0] for symbol in [candidate, *peers]}
            absolute: list[Decimal] = []
            peer_medians: list[Decimal] = []
            relative: list[Decimal] = []
            for opened in times:
                candidate_move = captured[(candidate, opened)][3] / reference_opens[candidate] - 1
                peer_move = median([
                    captured[(peer, opened)][3] / reference_opens[peer] - 1 for peer in peers
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
                "candidate_maximum_favorable_excursion_72h": decimal_text(max(absolute)),
                "candidate_maximum_adverse_excursion_72h": decimal_text(min(absolute)),
                "first_base_cost_relative_continuation_minutes": next(
                    ((index + 1) * 5 for index, value in enumerate(relative) if value >= Decimal("0.0030")),
                    None,
                ),
                "complete_72h": True,
            })
    return paths, counts


def evaluate_gates(
    paths: Sequence[Mapping[str, Any]], protocol: Mapping[str, Any], mismatch_count: int,
) -> tuple[dict[str, Any], dict[str, bool]]:
    gates = protocol["paper_gates"]
    count = len(paths)
    years = Counter(datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).year for row in paths)
    symbols = Counter(str(row["symbol"]) for row in paths)
    months = Counter(datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).strftime("%Y-%m") for row in paths)
    projected_full = count * int(protocol["scope"]["full_calendar_days"]) // int(protocol["scope"]["is_calendar_days"])
    projected_oos = count * int(protocol["scope"]["oos_calendar_days"]) // int(protocol["scope"]["is_calendar_days"])
    relative = [Decimal(str(row["relative_continuation"]["72"])) for row in paths]
    absolute = [Decimal(str(row["candidate_absolute_close_displacement"]["72"])) for row in paths]
    relative_median = median(relative) if paths else Decimal("NaN")
    absolute_median = median(absolute) if paths else Decimal("NaN")
    positive_fraction = Decimal(sum(value > 0 for value in relative)) / Decimal(count) if count else Decimal("NaN")
    year_share = Decimal(max(years.values(), default=count or 1)) / Decimal(count or 1)
    symbol_share = Decimal(max(symbols.values(), default=count or 1)) / Decimal(count or 1)
    metrics = {
        "complete_is_independent_episodes": count,
        "projected_full_independent_episodes": projected_full,
        "projected_sealed_oos_independent_episodes": projected_oos,
        "years_with_twelve_complete_episodes": sum(value >= 12 for value in years.values()),
        "episodes_by_year": {str(key): value for key, value in sorted(years.items())},
        "maximum_single_year_episode_share": decimal_text(year_share),
        "episodes_by_symbol": dict(sorted(symbols.items())),
        "maximum_single_symbol_episode_share": decimal_text(symbol_share),
        "distinct_event_symbols": len(symbols),
        "distinct_event_months": len(months),
        "median_72h_relative_continuation": decimal_text(relative_median) if relative_median.is_finite() else None,
        "median_72h_candidate_absolute_close_displacement": decimal_text(absolute_median) if absolute_median.is_finite() else None,
        "fraction_complete_episodes_with_positive_72h_relative_continuation": decimal_text(positive_fraction) if positive_fraction.is_finite() else None,
        "qualification_quarantine_lifecycle_or_order_mismatches": mismatch_count,
    }
    checks = {
        "complete_is_independent_episodes": count >= int(gates["complete_is_independent_episodes_minimum"]),
        "projected_full_independent_episodes": projected_full >= int(gates["projected_full_independent_episodes_minimum"]),
        "projected_sealed_oos_independent_episodes": projected_oos >= int(gates["projected_sealed_oos_independent_episodes_minimum"]),
        "years_with_twelve_complete_episodes": metrics["years_with_twelve_complete_episodes"] >= int(gates["minimum_years_with_twelve_complete_episodes"]),
        "maximum_single_year_episode_share": year_share <= Decimal(str(gates["maximum_single_year_episode_share"])),
        "maximum_single_symbol_episode_share": symbol_share <= Decimal(str(gates["maximum_single_symbol_episode_share"])),
        "distinct_event_symbols": len(symbols) >= int(gates["minimum_distinct_event_symbols"]),
        "distinct_event_months": len(months) >= int(gates["minimum_distinct_event_months"]),
        "median_72h_relative_continuation": relative_median.is_finite() and relative_median >= Decimal(str(gates["combined_median_72h_relative_continuation_minimum"])),
        "median_72h_candidate_absolute_close_displacement": absolute_median.is_finite() and absolute_median >= Decimal(str(gates["combined_median_72h_candidate_absolute_close_displacement_minimum"])),
        "fraction_positive_72h_relative_continuation": positive_fraction.is_finite() and positive_fraction >= Decimal(str(gates["fraction_complete_episodes_with_positive_72h_relative_continuation_minimum"])),
        "authority_and_order_mismatches": mismatch_count <= int(gates["qualification_quarantine_lifecycle_or_order_mismatches_maximum"]),
    }
    return metrics, checks


def wrap(name: str, content: Any) -> dict[str, Any]:
    document = {"schema_version": 1, "manifest_type": f"u10_{name}_manifest", "content": content}
    document["content_hash"] = identity_hash(document)
    return document


def run_order(raw_root: Path, protocol: Mapping[str, Any], qualification: Mapping[str, Any], order: str) -> dict[str, Any]:
    if qualification.get("qualification_content_hash") != QUALIFICATION_HASH:
        raise ObservationFailure("data qualification binding changed")
    start = utc_ms(protocol["scope"]["is_start"])
    end = utc_ms(protocol["scope"]["is_end_exclusive"])
    membership = build_membership(load_json(EVIDENCE / "membership_manifest.json"))
    masked = {(str(row["symbol"]), int(row["open_time_ms"])) for row in load_json(EVIDENCE / "invalid_interval_slot_mask_manifest.json")["content"]}
    daily = build_daily(raw_root, membership, masked, start, end, order)
    events, accounting = select_events(daily, membership, start, end, protocol["content_hash"], qualification["qualification_content_hash"])
    episodes = cluster_events(events)
    captured, pre_censored = capture(raw_root, episodes, membership, masked, start, end, order)
    paths, censor_counts = observe_paths(episodes, captured, pre_censored)
    content = {
        "events": sorted(events, key=lambda row: (int(row["decision_time_ms"]), str(row["symbol"]))),
        "episodes": sorted(episodes, key=lambda row: int(row["decision_time_ms"])),
        "paths": sorted(paths, key=lambda row: int(row["decision_time_ms"])),
        "accounting": {
            **accounting,
            "candidate_events": len(events),
            "independent_episodes": len(episodes),
            "complete_72h_episodes": len(paths),
            "right_censored_episodes": len(episodes) - len(paths),
            "right_censor_reasons": dict(sorted(censor_counts.items())),
            "oos_rows_decoded": 0,
            "formal_returns_computed": 0,
            "fills_positions_or_equity_rows": 0,
        },
    }
    manifests = {name: wrap(name, content[name]) for name in ("events", "episodes", "paths", "accounting")}
    hashes = {name: manifests[name]["content_hash"] for name in sorted(manifests)}
    return {"order": order, "manifests": manifests, "manifest_hashes": hashes, "content_identity_hash": identity_hash(hashes)}


def execute(raw_root: Path) -> dict[str, Any]:
    protocol = git_json(PROTOCOL_TARGET, PROTOCOL_PATH)
    qualification = load_json(QUALIFICATION_PATH)
    runs = [run_order(raw_root, protocol, qualification, order) for order in ("normal", "reverse", "deterministic_shuffled")]
    mismatch = 0 if len({run["content_identity_hash"] for run in runs}) == 1 else 1
    primary = runs[0]
    metrics, checks = evaluate_gates(primary["manifests"]["paths"]["content"], protocol, mismatch)
    status = "pass" if all(checks.values()) else "failed_feasibility"
    summary = {
        "schema_version": 1,
        "run_id": "U10-05-SEALED-IS-PAPER-OBSERVATION-V1",
        "status": status,
        "protocol_target_commit": PROTOCOL_TARGET,
        "protocol_content_hash": protocol["content_hash"],
        "qualification_content_hash": qualification["qualification_content_hash"],
        "is_start": protocol["scope"]["is_start"],
        "is_end_exclusive": protocol["scope"]["is_end_exclusive"],
        "orders": [{"order": run["order"], "content_identity_hash": run["content_identity_hash"], "manifest_hashes": run["manifest_hashes"]} for run in runs],
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


def render(result: Mapping[str, Any]) -> str:
    summary = result["summary"]
    metrics = summary["metrics"]
    lines = [
        "# U-10 Sealed-IS Paper Observation", "",
        f"- Status: `{summary['status']}`",
        f"- Run hash: `{summary['run_content_hash']}`",
        f"- Complete independent episodes: `{metrics['complete_is_independent_episodes']}`",
        "", "## Frozen Paper Gates", "",
        *[f"- {key}: `{str(value).lower()}`" for key, value in summary["paper_gate_checks"].items()],
        "", "## Metrics", "",
        f"- Projected full / sealed OOS episodes: `{metrics['projected_full_independent_episodes']} / {metrics['projected_sealed_oos_independent_episodes']}`",
        f"- Distinct event symbols / months: `{metrics['distinct_event_symbols']} / {metrics['distinct_event_months']}`",
        f"- Median 72h relative continuation: `{metrics['median_72h_relative_continuation']}`",
        f"- Median 72h candidate absolute displacement: `{metrics['median_72h_candidate_absolute_close_displacement']}`",
        f"- Positive 72h relative-continuation fraction: `{metrics['fraction_complete_episodes_with_positive_72h_relative_continuation']}`",
        "", "## Isolation", "",
        "- OOS opened / rows decoded: `false / 0`",
        "- Formal returns, fills, positions or equity generated: `false`",
        "- Parameters changed or second run executed: `false / false`",
        "", "A failed Gate closes the candidate without tuning. A pass authorizes only independent Paper-result review.", "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe")
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "reports/m1/evidence/u10_cross_sectional_paper_observation")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/m1/U10_CROSS_SECTIONAL_PAPER_OBSERVATION.md")
    args = parser.parse_args()
    result = execute(args.raw_root)
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    for name, document in result["manifests"].items():
        (args.evidence_dir / f"{name}.json").write_text(json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n")
    (args.evidence_dir / "run_manifest.json").write_text(json.dumps(result["summary"], sort_keys=True, separators=(",", ":")) + "\n")
    args.report.write_text(render(result))
    print(json.dumps(result["summary"], sort_keys=True, separators=(",", ":")))
    return 0 if result["summary"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
