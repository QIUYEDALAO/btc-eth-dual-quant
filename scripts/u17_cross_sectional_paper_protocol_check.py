#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.u17_cross_sectional_design_check import CONTENT_HASH as DESIGN_HASH, validate_all as validate_design

PROTOCOL = ROOT / "config/u17_cross_sectional_paper_protocol_v1.json"
CONTENT_HASH = "815013384df29fe2e803ee3e9dde22d0561cf1b67a24504290344ddef1ee6089"


def identity_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_protocol(protocol: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    identity = {key: value for key, value in protocol.items() if key not in {"content_hash", "generated_utc"}}
    if protocol.get("content_hash") != CONTENT_HASH or identity_hash(identity) != CONTENT_HASH:
        findings.append("protocol identity changed")
    if protocol.get("design_content_hash") != DESIGN_HASH or protocol.get("candidate_id") != "U17-CROSS-SECTIONAL-LIQUIDITY-RISK-PREMIUM":
        findings.append("design binding changed")
    history = protocol.get("history_contract", {})
    characteristic = protocol.get("liquidity_characteristic_contract", {})
    if history.get("history_complete_utc_days") != 28 or history.get("daily_quote_volume") != "sum_quote_volume_of_exactly_288_qualified_5m_rows" or history.get("all_28_complete_days_for_every_decision_time_active_member_required") is not True:
        findings.append("history changed")
    if characteristic.get("candidate_persistence_gate") != "candidate_in_daily_low_liquidity_group_on_at_least_21_of_28_completed_days" or characteristic.get("single_day_volume_change_or_price_move_used") is not False or characteristic.get("membership_entry_or_exit_event_used") is not False:
        findings.append("characteristic changed")
    if protocol.get("episode_clustering", {}).get("connected_window_days") != 28:
        findings.append("clustering changed")
    observation = protocol.get("observation_contract", {})
    if protocol.get("scope", {}).get("oos_opened") is not False or observation.get("horizon_days") != [1, 3, 7, 14, 28] or observation.get("formal_strategy_return") is not False:
        findings.append("scope or observation changed")
    gates = protocol.get("paper_gates", {})
    if len(gates) != 12 or gates.get("complete_is_independent_episodes_minimum") != 40 or gates.get("combined_median_28d_relative_liquidity_premium_minimum") != "0.0180" or gates.get("fraction_complete_episodes_with_positive_28d_relative_liquidity_premium_minimum") != "0.60":
        findings.append("paper Gates changed")
    expected = {
        "paper_protocol_frozen": True,
        "exact_head_independent_review": True,
        "data_qualification_complexity_and_preflight": False,
        "liquidity_rank_scan": False,
        "event_scan": False,
        "path_observation": False,
        "signals": False,
        "formal_returns": False,
        "fixed_rule_contract": False,
        "freqtrade_strategy_code": False,
        "backtesting": False,
        "oos": False,
        "api_trading": False,
        "execution_live": False,
        "m2": False,
    }
    if protocol.get("authorizations") != expected:
        findings.append("authorization changed")
    return findings


def validate_all() -> list[str]:
    return validate_design() + validate_protocol(json.loads(PROTOCOL.read_text()))


def main() -> int:
    findings = validate_all()
    if findings:
        print("u17_cross_sectional_paper_protocol_check FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"u17_cross_sectional_paper_protocol_check PASS hash={CONTENT_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
