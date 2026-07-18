#!/usr/bin/env python3
"""Execute the unique frozen U-18 sealed-IS Paper observation."""
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
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.data.u18_downside_tail_risk import TailRiskCandidatePath, evaluate_candidate
from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json, utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE, FIVE_MINUTES_MS, ONE_HOUR_MS, ObservationFailure, build_membership, decimal_text, median, month_for_ms
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u14_cross_sectional_paper_observation import capture_paths, cluster_events
from scripts.u16_cross_sectional_paper_observation import build_hourly_closes

FOUR_HOURS_MS = 4 * ONE_HOUR_MS
HORIZONS = (1, 2, 4, 8, 12, 24)
PROTOCOL_TARGET = "39a766c50de5a0855d7ee85c2aab743ec8b738e5"
PROTOCOL_PATH = "config/u18_cross_sectional_paper_protocol_v1.json"
QUALIFICATION_HASH = "088ebed218ce7960621ebeda539ec78c5aeebbef5b98f608a4f044f78e3dc6e0"


def select_events(
    closes: Mapping[tuple[str, int], Decimal],
    membership: Mapping[str, Sequence[str]],
    start: int,
    end: int,
    protocol_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    events: list[dict[str, Any]] = []
    accounting = {
        "decision_times_considered": 0,
        "history_or_membership_ineligible": 0,
        "zero_scale_or_tail_gate_failed": 0,
        "candidate_events": 0,
    }
    decision = start
    with localcontext() as context:
        context.prec = 50
        while decision < end:
            symbols = tuple(membership.get(month_for_ms(decision - 1), ()))
            if len(symbols) < 10:
                decision += FOUR_HOURS_MS
                continue
            accounting["decision_times_considered"] += 1
            history_starts = range(decision - 168 * ONE_HOUR_MS, decision, ONE_HOUR_MS)
            if any(tuple(membership.get(month_for_ms(opened), ())) != symbols for opened in history_starts):
                accounting["history_or_membership_ineligible"] += 1
                decision += FOUR_HOURS_MS
                continue
            endpoints = tuple(decision - (168 - index) * ONE_HOUR_MS for index in range(169))
            if any((symbol, endpoint) not in closes for symbol in symbols for endpoint in endpoints):
                accounting["history_or_membership_ineligible"] += 1
                decision += FOUR_HOURS_MS
                continue
            returns = {
                symbol: tuple((closes[(symbol, endpoint)] / closes[(symbol, endpoint - ONE_HOUR_MS)]).ln() for endpoint in endpoints[1:])
                for symbol in symbols
            }
            candidates: list[tuple[Decimal, Decimal, str, dict[str, Any]]] = []
            for symbol in symbols:
                peers = tuple(peer for peer in symbols if peer != symbol)
                common = tuple(median([returns[peer][index] for peer in peers]) for index in range(168))
                selected = evaluate_candidate(
                    TailRiskCandidatePath(
                        decision,
                        symbol,
                        tuple(float(value) for value in returns[symbol]),
                        tuple(float(value) for value in common),
                        (0.0,) * 6,
                    )
                )
                if selected is not None:
                    candidates.append(
                        (
                            Decimal(selected["minimum_tail_energy_share"]),
                            Decimal(selected["minimum_standardized_tail"]),
                            symbol,
                            selected,
                        )
                    )
            if not candidates:
                accounting["zero_scale_or_tail_gate_failed"] += 1
                decision += FOUR_HOURS_MS
                continue
            minimum_share, minimum_standardized, symbol, selected = sorted(
                candidates, key=lambda row: (-row[0], row[1], row[2])
            )[0]
            core = {
                "decision_time_ms": decision - 1,
                "reference_open_time_ms": decision,
                "symbol": symbol,
                "active_members": list(symbols),
                "active_member_count": len(symbols),
                "first_half_tail_count": selected["first_tail_count"],
                "second_half_tail_count": selected["second_tail_count"],
                "minimum_two_half_tail_energy_share": decimal_text(minimum_share),
                "maximum_two_half_single_tail_dominance": selected["maximum_tail_dominance"],
                "minimum_standardized_tail": decimal_text(minimum_standardized),
            }
            core["event_id"] = identity_hash({"protocol": protocol_hash, "qualification": QUALIFICATION_HASH, **core})
            events.append(core)
            accounting["candidate_events"] += 1
            decision += FOUR_HOURS_MS
    return events, accounting


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
            times = [reference + index * FIVE_MINUTES_MS for index in range(288)]
            members = [candidate, *peers]
            if any((symbol, opened) not in captured for symbol in members for opened in times):
                counts["missing_or_quarantined_5m"] += 1
                continue
            reference_opens = {symbol: captured[(symbol, reference)][0] for symbol in members}
            absolute: list[Decimal] = []
            peer_moves: list[Decimal] = []
            relative: list[Decimal] = []
            highs: list[Decimal] = []
            lows: list[Decimal] = []
            for opened in times:
                candidate_move = captured[(candidate, opened)][3] / reference_opens[candidate] - Decimal(1)
                peer_move = median([captured[(peer, opened)][3] / reference_opens[peer] - Decimal(1) for peer in peers])
                absolute.append(candidate_move)
                peer_moves.append(peer_move)
                relative.append(candidate_move - peer_move)
                highs.append(captured[(candidate, opened)][1] / reference_opens[candidate] - Decimal(1))
                lows.append(captured[(candidate, opened)][2] / reference_opens[candidate] - Decimal(1))
            paths.append(
                {
                    "episode_id": episode_id,
                    "event_id": episode["event_id"],
                    "symbol": candidate,
                    "decision_time_ms": int(episode["decision_time_ms"]),
                    "reference_open_time_ms": reference,
                    "peer_count": len(peers),
                    "candidate_absolute_close_displacement": {str(hour): decimal_text(absolute[hour * 12 - 1]) for hour in HORIZONS},
                    "peer_median_close_displacement": {str(hour): decimal_text(peer_moves[hour * 12 - 1]) for hour in HORIZONS},
                    "relative_downside_tail_risk_premium": {str(hour): decimal_text(relative[hour * 12 - 1]) for hour in HORIZONS},
                    "candidate_maximum_favorable_excursion_24h": decimal_text(max(highs)),
                    "candidate_maximum_adverse_excursion_24h": decimal_text(min(lows)),
                    "first_base_cost_relative_premium_minutes": next(((index + 1) * 5 for index, value in enumerate(relative) if value >= Decimal("0.0030")), None),
                    "complete_24h": True,
                }
            )
    return paths, counts


def evaluate_gates(paths: Sequence[Mapping[str, Any]], mismatch: int) -> tuple[dict[str, Any], dict[str, bool]]:
    count = len(paths)
    years = Counter(datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).year for row in paths)
    symbols = Counter(str(row["symbol"]) for row in paths)
    months = Counter(datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).strftime("%Y-%m") for row in paths)
    projected_full = count * 2373 // 1715
    projected_oos = count * 658 // 1715
    relative = [Decimal(str(row["relative_downside_tail_risk_premium"]["24"])) for row in paths]
    absolute = [Decimal(str(row["candidate_absolute_close_displacement"]["24"])) for row in paths]
    relative_median = median(relative) if paths else Decimal("NaN")
    absolute_median = median(absolute) if paths else Decimal("NaN")
    positive = Decimal(sum(value > 0 for value in relative)) / Decimal(count) if count else Decimal("NaN")
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
        "median_24h_relative_downside_tail_risk_premium": decimal_text(relative_median) if relative_median.is_finite() else None,
        "median_24h_candidate_absolute_close_displacement": decimal_text(absolute_median) if absolute_median.is_finite() else None,
        "fraction_complete_episodes_with_positive_24h_relative_downside_tail_risk_premium": decimal_text(positive) if positive.is_finite() else None,
        "qualification_preflight_complexity_quarantine_lifecycle_or_order_mismatches": mismatch,
    }
    checks = {
        "complete_is_independent_episodes": count >= 90,
        "projected_full_independent_episodes": projected_full >= 120,
        "projected_sealed_oos_independent_episodes": projected_oos >= 30,
        "years_with_twelve_complete_episodes": metrics["years_with_twelve_complete_episodes"] >= 4,
        "maximum_single_year_episode_share": year_share <= Decimal("0.35"),
        "maximum_single_symbol_episode_share": symbol_share <= Decimal("0.25"),
        "distinct_event_symbols": len(symbols) >= 8,
        "distinct_event_months": len(months) >= 30,
        "median_24h_relative_downside_tail_risk_premium": relative_median.is_finite() and relative_median >= Decimal("0.0180"),
        "median_24h_candidate_absolute_close_displacement": absolute_median.is_finite() and absolute_median >= Decimal("0.0180"),
        "fraction_positive_24h_relative_downside_tail_risk_premium": positive.is_finite() and positive >= Decimal("0.60"),
        "authority_and_order_mismatches": mismatch == 0,
    }
    return metrics, checks


def wrap(name: str, content: Any) -> dict[str, Any]:
    document = {"schema_version": 1, "manifest_type": f"u18_{name}_manifest", "content": content}
    document["content_hash"] = identity_hash(document)
    return document


def run_order(raw_root: Path, protocol: Mapping[str, Any], qualification: Mapping[str, Any], order: str) -> dict[str, Any]:
    if qualification.get("qualification_content_hash") != QUALIFICATION_HASH:
        raise ObservationFailure("qualification binding changed")
    start, end = utc_ms(protocol["scope"]["is_start"]), utc_ms(protocol["scope"]["is_end_exclusive"])
    membership = build_membership(load_json(EVIDENCE / "membership_manifest.json"))
    masked = {(str(row["symbol"]), int(row["open_time_ms"])) for row in load_json(EVIDENCE / "invalid_interval_slot_mask_manifest.json")["content"]}
    closes = build_hourly_closes(raw_root=raw_root, membership=membership, masked=masked, start=start, end=end, order=order)
    events, scan = select_events(closes, membership, start, end, protocol["content_hash"])
    episodes = cluster_events(events)
    captured, precensored = capture_paths(raw_root=raw_root, episodes=episodes, membership=membership, masked=masked, start=start, end=end, order=order)
    paths, censors = observe_paths(episodes, captured, precensored)
    content = {
        "events": sorted(events, key=lambda row: int(row["decision_time_ms"])),
        "episodes": sorted(episodes, key=lambda row: int(row["decision_time_ms"])),
        "paths": sorted(paths, key=lambda row: int(row["decision_time_ms"])),
        "accounting": {
            **scan,
            "independent_episodes": len(episodes),
            "complete_24h_episodes": len(paths),
            "right_censored_episodes": len(episodes) - len(paths),
            "right_censor_reasons": dict(sorted(censors.items())),
            "oos_rows_decoded": 0,
            "formal_returns_computed": 0,
            "fills_positions_or_equity_rows": 0,
        },
    }
    manifests = {name: wrap(name, content[name]) for name in content}
    hashes = {name: manifests[name]["content_hash"] for name in sorted(manifests)}
    return {"order": order, "manifests": manifests, "manifest_hashes": hashes, "content_identity_hash": identity_hash(hashes)}


def execute(raw_root: Path) -> dict[str, Any]:
    protocol = git_json(PROTOCOL_TARGET, PROTOCOL_PATH)
    qualification = load_json(ROOT / "reports/m1/evidence/u18_cross_sectional_data_qualification_v1.json")
    runs = [run_order(raw_root, protocol, qualification, order) for order in ("normal", "reverse", "deterministic_shuffled")]
    mismatch = 0 if len({run["content_identity_hash"] for run in runs}) == 1 else 1
    primary = runs[0]
    metrics, checks = evaluate_gates(primary["manifests"]["paths"]["content"], mismatch)
    status = "pass" if all(checks.values()) else "failed_feasibility"
    summary = {
        "schema_version": 1,
        "run_id": "U18-06-SEALED-IS-PAPER-OBSERVATION-V1",
        "status": status,
        "protocol_content_hash": protocol["content_hash"],
        "qualification_content_hash": QUALIFICATION_HASH,
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
    summary, metrics = result["summary"], result["summary"]["metrics"]
    lines = [
        "# U-18 Sealed-IS Paper Observation",
        "",
        f"- Status: `{summary['status']}`",
        f"- Run hash: `{summary['run_content_hash']}`",
        f"- Complete independent episodes: `{metrics['complete_is_independent_episodes']}`",
        "",
        "## Frozen Paper Gates",
        "",
        *[f"- {key}: `{str(value).lower()}`" for key, value in summary["paper_gate_checks"].items()],
        "",
        "## Metrics",
        "",
        f"- Projected full / sealed OOS episodes: `{metrics['projected_full_independent_episodes']} / {metrics['projected_sealed_oos_independent_episodes']}`",
        f"- Distinct symbols / months: `{metrics['distinct_event_symbols']} / {metrics['distinct_event_months']}`",
        f"- Median 24h relative downside-tail risk premium: `{metrics['median_24h_relative_downside_tail_risk_premium']}`",
        f"- Median 24h absolute displacement: `{metrics['median_24h_candidate_absolute_close_displacement']}`",
        f"- Positive relative-premium fraction: `{metrics['fraction_complete_episodes_with_positive_24h_relative_downside_tail_risk_premium']}`",
        "",
        "## Isolation",
        "",
        "- OOS opened / rows decoded: `false / 0`",
        "- Formal returns, fills, positions or equity generated: `false`",
        "- Parameters changed or second run executed: `false / false`",
        "",
    ]
    return "\n".join(lines)


def write(result: Mapping[str, Any], evidence: Path, report: Path) -> None:
    evidence.mkdir(parents=True, exist_ok=True)
    for name, document in result["manifests"].items():
        (evidence / f"{name}.json").write_text(json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n")
    (evidence / "run_manifest.json").write_text(json.dumps(result["summary"], sort_keys=True, separators=(",", ":")) + "\n")
    report.write_text(render(result))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe")
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "reports/m1/evidence/u18_cross_sectional_paper_observation")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/m1/U18_CROSS_SECTIONAL_PAPER_OBSERVATION.md")
    args = parser.parse_args()
    if (args.evidence_dir / "run_manifest.json").exists():
        print("U-18 is closed after its unique Paper observation; a second result-bearing run is not authorized.")
        return 2
    result = execute(args.raw_root)
    write(result, args.evidence_dir, args.report)
    print(json.dumps(result["summary"], sort_keys=True, separators=(",", ":")))
    return 0 if result["summary"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
