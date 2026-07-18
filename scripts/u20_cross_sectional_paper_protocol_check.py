#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.u20_cross_sectional_design_check import CONTENT_HASH as DESIGN_HASH, validate_all as validate_design

PROTOCOL = ROOT / "config/u20_cross_sectional_paper_protocol_v1.json"
CONTENT_HASH = "d909cd57bbed8c1eaa859905909ce0503d8e653d671b499af0868b1713e2dec9"


def identity_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_protocol(protocol: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    identity = {key: value for key, value in protocol.items() if key not in {"content_hash", "generated_utc"}}
    if protocol.get("content_hash") != CONTENT_HASH or identity_hash(identity) != CONTENT_HASH:
        findings.append("protocol identity changed")
    if protocol.get("design_content_hash") != DESIGN_HASH or protocol.get("candidate_id") != "U20-CROSS-SECTIONAL-NEGATIVE-COSKEWNESS-RISK-PREMIUM":
        findings.append("design binding changed")
    bindings = protocol.get("authority_bindings", {})
    if bindings.get("u20_design_authorization_hash") != "b4e9d5c94957d69142e328a05dfb00474840efe3347dd5347c55997115b64455" or bindings.get("u19_run_content_hash") != "38daffb0834c28a769108c74f256b601f08667c7076d107bc97f48925b63f3d4":
        findings.append("authority binding changed")
    history = protocol.get("history_contract", {})
    coskew = protocol.get("negative_coskewness_contract", {})
    if history.get("history_hours") != 336 or history.get("half_window_hours") != 168 or history.get("all_336_completed_hourly_returns_for_every_decision_time_active_member_required") is not True:
        findings.append("history changed")
    if coskew.get("maximum_coskewness_per_half") != "-0.20" or coskew.get("required_rank_per_half") != "lowest_ceiling_active_member_count_divided_by_four" or coskew.get("both_halves_must_pass_absolute_and_rank_gates") is not True:
        findings.append("coskewness contract changed")
    if coskew.get("common_or_candidate_mean_return_direction_gate_used") is not False or coskew.get("volatility_tail_drawdown_or_terminal_bar_gate_used") is not False:
        findings.append("outcome proxy gate added")
    if protocol.get("episode_clustering", {}).get("connected_window_hours") != 24:
        findings.append("clustering changed")
    observation = protocol.get("observation_contract", {})
    if protocol.get("scope", {}).get("oos_opened") is not False or observation.get("horizon_hours") != [1, 2, 4, 8, 12, 24] or observation.get("formal_strategy_return") is not False:
        findings.append("scope or observation changed")
    gates = protocol.get("paper_gates", {})
    if len(gates) != 12 or gates.get("complete_is_independent_episodes_minimum") != 90 or gates.get("combined_median_24h_relative_negative_coskewness_risk_premium_minimum") != "0.0180" or gates.get("fraction_complete_episodes_with_positive_24h_relative_negative_coskewness_risk_premium_minimum") != "0.60":
        findings.append("paper Gates changed")
    expected = {"paper_protocol_frozen": True, "exact_head_independent_review": True, "data_qualification_complexity_and_preflight": False, "return_common_adjustment_coskewness_scan": False, "event_scan": False, "path_observation": False, "signals": False, "formal_returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if protocol.get("authorizations") != expected:
        findings.append("authorization changed")
    return findings


def validate_all() -> list[str]:
    return validate_design() + validate_protocol(json.loads(PROTOCOL.read_text()))


def main() -> int:
    findings = validate_all()
    if findings:
        print("u20_cross_sectional_paper_protocol_check FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"u20_cross_sectional_paper_protocol_check PASS hash={CONTENT_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
