#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.u18_cross_sectional_design_check import CONTENT_HASH as DESIGN_HASH, validate_all as validate_design

PROTOCOL = ROOT / "config/u18_cross_sectional_paper_protocol_v1.json"
CONTENT_HASH = "7571d2cb2408e30ac03d626544243f1e00595dc9ed85e6a7107b7d9a2062c671"


def identity_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_protocol(protocol: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    identity = {key: value for key, value in protocol.items() if key not in {"content_hash", "generated_utc"}}
    if protocol.get("content_hash") != CONTENT_HASH or identity_hash(identity) != CONTENT_HASH:
        findings.append("protocol identity changed")
    if protocol.get("design_content_hash") != DESIGN_HASH or protocol.get("candidate_id") != "U18-CROSS-SECTIONAL-IDIOSYNCRATIC-DOWNSIDE-TAIL-RISK-PREMIUM":
        findings.append("design binding changed")
    history = protocol.get("history_contract", {})
    tail = protocol.get("downside_tail_contract", {})
    if history.get("history_hours") != 168 or history.get("half_window_hours") != 84 or history.get("all_168_completed_hourly_returns_for_every_decision_time_active_member_required") is not True:
        findings.append("history changed")
    if tail.get("minimum_downside_tail_observations_per_half") != 2 or tail.get("minimum_downside_tail_energy_share_per_half") != "0.25" or tail.get("maximum_single_tail_observation_share_of_half_tail_energy") != "0.65" or tail.get("both_halves_must_pass") is not True or tail.get("return_direction_mean_or_terminal_bar_gate_used") is not False:
        findings.append("tail contract changed")
    if protocol.get("episode_clustering", {}).get("connected_window_hours") != 24:
        findings.append("clustering changed")
    observation = protocol.get("observation_contract", {})
    if protocol.get("scope", {}).get("oos_opened") is not False or observation.get("horizon_hours") != [1, 2, 4, 8, 12, 24] or observation.get("formal_strategy_return") is not False:
        findings.append("scope or observation changed")
    gates = protocol.get("paper_gates", {})
    if len(gates) != 12 or gates.get("complete_is_independent_episodes_minimum") != 90 or gates.get("combined_median_24h_relative_downside_tail_risk_premium_minimum") != "0.0180" or gates.get("fraction_complete_episodes_with_positive_24h_relative_downside_tail_risk_premium_minimum") != "0.60":
        findings.append("paper Gates changed")
    expected = {"paper_protocol_frozen": True, "exact_head_independent_review": True, "data_qualification_complexity_and_preflight": False, "return_residual_tail_scan": False, "event_scan": False, "path_observation": False, "signals": False, "formal_returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if protocol.get("authorizations") != expected:
        findings.append("authorization changed")
    return findings


def validate_all() -> list[str]:
    return validate_design() + validate_protocol(json.loads(PROTOCOL.read_text()))


def main() -> int:
    findings = validate_all()
    if findings:
        print("u18_cross_sectional_paper_protocol_check FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"u18_cross_sectional_paper_protocol_check PASS hash={CONTENT_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
