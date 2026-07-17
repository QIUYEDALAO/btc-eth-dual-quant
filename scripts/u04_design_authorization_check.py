#!/usr/bin/env python3
"""Validate the narrow post-audit U-04 design authorization decision."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "config/u04_design_authorization_v1.json"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
EXPECTED_HASH = "84d9b499329169719a880af80b1e2e7f0d5d5cbbc6c62a6aa762cd738aa04e89"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(document: Mapping[str, Any], audit: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}}
    if document.get("content_hash") != EXPECTED_HASH or canonical_hash(identity) != EXPECTED_HASH:
        failures.append("U-04 decision identity changed")
    bindings = document.get("bindings", {})
    if bindings.get("adr0015_audit_summary_hash") != audit.get("audit_summary_hash"):
        failures.append("audit summary binding changed")
    if bindings.get("v4_artifact_set_hash") != audit.get("independent_artifact_set_hash"):
        failures.append("artifact-set binding changed")
    if audit.get("verdict") != "pass" or audit.get("manifests_exact") != 19 or audit.get("manifests_total") != 19:
        failures.append("passing 19/19 audit dependency is absent")
    if audit.get("critical_findings") or audit.get("high_findings"):
        failures.append("audit critical/high Gate is not zero")
    decision = document.get("decision", {})
    if decision.get("u04_design_authorized") is not True or decision.get("maximum_hypotheses") != 1:
        failures.append("one-hypothesis design authority changed")
    if decision.get("outcome_blind_preregistration_required") is not True or decision.get("separate_protocol_before_any_event_scan") is not True:
        failures.append("outcome-blind protocol Gate changed")
    expected_authorizations = {
        "u04_hypothesis_design": True, "event_scan": False, "signals": False,
        "returns": False, "strategy_rule_selection": False, "freqtrade_strategy_code": False,
        "backtesting": False, "oos": False, "api_trading": False,
        "execution_live": False, "m2": False,
    }
    if document.get("authorizations") != expected_authorizations:
        failures.append("U-04 authorization matrix changed")
    return failures


def main() -> int:
    document = json.loads(DECISION.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    failures = validate(document, audit)
    if failures:
        print("u04_design_authorization_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("u04_design_authorization_check PASS")
    print(f"decision_content_hash={EXPECTED_HASH}")
    print("design=yes event_scan=no strategy=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
