#!/usr/bin/env python3
"""Validate the narrow post-U-04 U-05 design authorization decision."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "config/u05_design_authorization_v1.json"
U04_RESULT = ROOT / "reports/m1/evidence/u04_cross_sectional_paper_observation/run_manifest.json"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
EXPECTED_HASH = "48482a1d72b34d4925e3b0ed8ab218df202d560af7d8057c4fa8be403c46dc2c"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(document: Mapping[str, Any], u04: Mapping[str, Any], audit: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}}
    if document.get("content_hash") != EXPECTED_HASH or canonical_hash(identity) != EXPECTED_HASH:
        failures.append("U-05 decision identity changed")
    bindings = document.get("bindings", {})
    if bindings.get("u04_run_content_hash") != u04.get("run_content_hash"):
        failures.append("U-04 result binding changed")
    if u04.get("status") != "failed_feasibility" or u04.get("oos_opened") is not False:
        failures.append("U-04 must remain failed and OOS-sealed")
    if bindings.get("adr0015_audit_summary_hash") != audit.get("audit_summary_hash"):
        failures.append("audit summary binding changed")
    if bindings.get("v4_artifact_set_hash") != audit.get("independent_artifact_set_hash"):
        failures.append("artifact-set binding changed")
    if audit.get("verdict") != "pass" or audit.get("manifests_exact") != 19 or audit.get("manifests_total") != 19:
        failures.append("passing 19/19 audit dependency is absent")
    decision = document.get("decision", {})
    if decision.get("u05_design_authorized") is not True or decision.get("maximum_hypotheses") != 1:
        failures.append("one-hypothesis U-05 design authority changed")
    for key in (
        "independent_economic_rationale_required",
        "u04_outcome_derived_direction_or_rule_prohibited",
        "outcome_blind_preregistration_required",
        "separate_protocol_before_any_event_scan",
    ):
        if decision.get(key) is not True:
            failures.append(f"required design invariant changed: {key}")
    expected_authorizations = {
        "u05_hypothesis_design": True, "event_scan": False, "signals": False,
        "returns": False, "strategy_rule_selection": False, "freqtrade_strategy_code": False,
        "backtesting": False, "oos": False, "api_trading": False,
        "execution_live": False, "m2": False,
    }
    if document.get("authorizations") != expected_authorizations:
        failures.append("U-05 authorization matrix changed")
    stops = document.get("stop_conditions", [])
    if not any("may not be inverted" in str(item) for item in stops):
        failures.append("U-04 outcome-inversion prohibition missing")
    return failures


def main() -> int:
    document = json.loads(DECISION.read_text(encoding="utf-8"))
    u04 = json.loads(U04_RESULT.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    failures = validate(document, u04, audit)
    if failures:
        print("u05_design_authorization_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("u05_design_authorization_check PASS")
    print(f"decision_content_hash={EXPECTED_HASH}")
    print("design=yes event_scan=no strategy=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
