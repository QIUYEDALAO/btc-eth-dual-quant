#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.u23_cross_sectional_design_check import CONTENT_HASH as DESIGN_HASH, validate_all as validate_design

PROTOCOL = ROOT / "config/u23_cross_sectional_paper_protocol_v1.json"
FEASIBILITY = ROOT / "reports/m1/evidence/u23_synthetic_core_feasibility_v1.json"
CORE = ROOT / "src/btc_eth_dual_quant/data/u23_range_expansion.py"
CONTENT_HASH = "52807bd0e2c0bd2276c88e1d919a7e4a375c480f51fe479f0934d8c0063e5611"
FEASIBILITY_HASH = "6010529c89627e8607919272af3c85c7dd5c3fdd4e48f549b8fe055e3245637e"
CORE_HASH = "ffba8a38981c954024e1efa96dce3595a13a1f3be53330b9b9c776fef6881aa7"


def identity_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_feasibility(value: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    identity = {key: item for key, item in value.items() if key not in {"content_hash", "generated_utc"}}
    if value.get("content_hash") != FEASIBILITY_HASH or identity_hash(identity) != FEASIBILITY_HASH:
        findings.append("feasibility identity changed")
    passes = value.get("passes", [])
    if value.get("status") != "pass_before_protocol_freeze" or len(passes) != 3 or value.get("actual_logical_ohlc_member_bars_per_pass", 0) < 1_000_000:
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
    if protocol.get("design_content_hash") != DESIGN_HASH or protocol.get("candidate_id") != "U23-CROSS-SECTIONAL-RANGE-EXPANSION-CLOSE-STRENGTH-CONTINUATION":
        findings.append("design binding changed")
    bindings = protocol.get("authority_bindings", {})
    if bindings.get("u23_design_authorization_hash") != "70c60434bb7c78344eb733eb8a8d4393538f60bbc97bff60e840c68f10998d5a" or bindings.get("u22_run_content_hash") != "12a756e2fa8a0fa2e2b87f69c8dc00559f3021a27368a0ac4efc8f5e8001531c" or bindings.get("synthetic_core_feasibility_hash") != FEASIBILITY_HASH or bindings.get("exact_core_sha256") != CORE_HASH:
        findings.append("authority binding changed")
    history = protocol.get("history_contract", {})
    ranges = protocol.get("range_contract", {})
    close = protocol.get("close_strength_contract", {})
    if history.get("prior_completed_4h_bars") != 42 or history.get("all_43_completed_4h_ohlc_bars_for_every_decision_time_active_member_required") is not True:
        findings.append("history changed")
    if ranges.get("minimum_current_log_range") != "0.03922071315328133" or ranges.get("minimum_current_over_baseline_ratio") != "2.00" or ranges.get("minimum_current_range_robust_z") != "3.00":
        findings.append("range Gate changed")
    if close.get("minimum_close_location") != "0.90" or close.get("minimum_positive_body_share") != "0.60" or close.get("minimum_peer_relative_log_return") != "0.02469261259037141":
        findings.append("close-strength Gate changed")
    if protocol.get("episode_clustering", {}).get("connected_window_hours") != 24:
        findings.append("clustering changed")
    observation = protocol.get("observation_contract", {})
    if protocol.get("scope", {}).get("oos_opened") is not False or observation.get("horizon_hours") != [1, 2, 4, 8, 12, 24] or observation.get("formal_strategy_return") is not False:
        findings.append("scope or observation changed")
    gates = protocol.get("paper_gates", {})
    if len(gates) != 12 or gates.get("complete_is_independent_episodes_minimum") != 90 or gates.get("combined_median_24h_relative_close_strength_continuation_minimum") != "0.0180" or gates.get("fraction_complete_episodes_with_positive_24h_relative_close_strength_continuation_minimum") != "0.60":
        findings.append("paper Gates changed")
    expected = {"paper_protocol_frozen": True, "exact_head_independent_review": True, "data_qualification_and_preflight": False, "ohlc_range_return_scan": False, "event_scan": False, "path_observation": False, "signals": False, "formal_returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if protocol.get("authorizations") != expected:
        findings.append("authorization changed")
    return findings


def validate_all() -> list[str]:
    return validate_design() + validate_feasibility(json.loads(FEASIBILITY.read_text())) + validate_protocol(json.loads(PROTOCOL.read_text()))


def main() -> int:
    findings = validate_all()
    if findings:
        print("u23_cross_sectional_paper_protocol_check FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"u23_cross_sectional_paper_protocol_check PASS hash={CONTENT_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
