#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.u22_cross_sectional_design_check import CONTENT_HASH as DESIGN_HASH, validate_all as validate_design

PROTOCOL = ROOT / "config/u22_cross_sectional_paper_protocol_v1.json"
FEASIBILITY = ROOT / "reports/m1/evidence/u22_synthetic_core_feasibility_v1.json"
CORE = ROOT / "src/btc_eth_dual_quant/data/u22_dispersion_expansion.py"
CONTENT_HASH = "0fdc7eb264e5f9a24dbcb746bbee6af0b1af2218cc101d6674099769f5d1b4fa"
FEASIBILITY_HASH = "4476d5b5cc38b23c3f031b2438e77224a8da3c80ee011dba719cf43b76e6940b"
CORE_HASH = "18ceb5d8a13450e298b99bb0664acd7c9d4d2893ac37a00d9635f3c2c5de7264"


def identity_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_feasibility(value: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    identity = {key: item for key, item in value.items() if key not in {"content_hash", "generated_utc"}}
    if value.get("content_hash") != FEASIBILITY_HASH or identity_hash(identity) != FEASIBILITY_HASH:
        findings.append("feasibility identity changed")
    passes = value.get("passes", [])
    if value.get("status") != "pass_before_protocol_freeze" or len(passes) != 3 or value.get("actual_logical_hourly_member_rows_per_pass", 0) < 1_000_000:
        findings.append("feasibility Gate changed")
    if any(float(item.get("elapsed_seconds", 31)) > 30 or float(item.get("peak_rss_mib", 1025)) > 1024 for item in passes) or len({item.get("event_digest") for item in passes}) != 1:
        findings.append("feasibility result changed")
    if value.get("public_data_read") is not False or value.get("frozen_source_archives_opened") != 0 or value.get("market_outcome_rows") != 0 or value.get("oos_values_decoded") != 0:
        findings.append("feasibility isolation changed")
    if hashlib.sha256(CORE.read_bytes()).hexdigest() != CORE_HASH or value.get("core_sha256") != CORE_HASH:
        findings.append("exact core changed")
    return findings


def validate_protocol(protocol: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    identity = {key: value for key, value in protocol.items() if key not in {"content_hash", "generated_utc"}}
    if protocol.get("content_hash") != CONTENT_HASH or identity_hash(identity) != CONTENT_HASH:
        findings.append("protocol identity changed")
    if protocol.get("design_content_hash") != DESIGN_HASH or protocol.get("candidate_id") != "U22-CROSS-SECTIONAL-DISPERSION-EXPANSION-LEADER-CONTINUATION":
        findings.append("design binding changed")
    bindings = protocol.get("authority_bindings", {})
    if bindings.get("u22_design_authorization_hash") != "82aef7f378a1aaa46ded62cfc21dedb67e6d86a8d0c27c24f66280d8c124e29d" or bindings.get("u21_qualification_content_hash") != "33e53b7fd32c6610349f99bb01cf71143ab9837289198266fd1b25f6e7147a1b" or bindings.get("synthetic_core_feasibility_hash") != FEASIBILITY_HASH or bindings.get("exact_core_sha256") != CORE_HASH:
        findings.append("authority binding changed")
    history = protocol.get("history_contract", {})
    dispersion = protocol.get("dispersion_contract", {})
    leader = protocol.get("leader_contract", {})
    if history.get("history_hours") != 24 or history.get("baseline_hours") != 12 or history.get("recent_hours") != 12 or history.get("all_24_completed_hourly_returns_for_every_decision_time_active_member_required") is not True:
        findings.append("history changed")
    if dispersion.get("minimum_recent_dispersion") != "0.0040" or dispersion.get("minimum_recent_over_baseline_dispersion_ratio") != "1.50":
        findings.append("dispersion changed")
    if leader.get("minimum_relative_log_displacement") != "0.02371652661731604" or leader.get("minimum_positive_recent_hours") != 8 or leader.get("maximum_single_positive_residual_share_of_total_positive_residual") != "0.50" or leader.get("both_oldest_6_and_newest_6_recent_residual_sums_must_be_positive") is not True:
        findings.append("leader changed")
    if protocol.get("episode_clustering", {}).get("connected_window_hours") != 24:
        findings.append("clustering changed")
    observation = protocol.get("observation_contract", {})
    if protocol.get("scope", {}).get("oos_opened") is not False or observation.get("horizon_hours") != [1, 2, 4, 8, 12, 24] or observation.get("formal_strategy_return") is not False:
        findings.append("scope or observation changed")
    gates = protocol.get("paper_gates", {})
    if len(gates) != 12 or gates.get("complete_is_independent_episodes_minimum") != 90 or gates.get("combined_median_24h_relative_leader_continuation_minimum") != "0.0180" or gates.get("fraction_complete_episodes_with_positive_24h_relative_leader_continuation_minimum") != "0.60":
        findings.append("paper Gates changed")
    expected = {"paper_protocol_frozen": True, "exact_head_independent_review": True, "data_qualification_and_preflight": False, "return_dispersion_leader_scan": False, "event_scan": False, "path_observation": False, "signals": False, "formal_returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if protocol.get("authorizations") != expected:
        findings.append("authorization changed")
    return findings


def validate_all() -> list[str]:
    return validate_design() + validate_feasibility(json.loads(FEASIBILITY.read_text())) + validate_protocol(json.loads(PROTOCOL.read_text()))


def main() -> int:
    findings = validate_all()
    if findings:
        print("u22_cross_sectional_paper_protocol_check FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"u22_cross_sectional_paper_protocol_check PASS hash={CONTENT_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
