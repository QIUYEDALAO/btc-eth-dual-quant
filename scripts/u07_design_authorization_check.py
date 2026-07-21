#!/usr/bin/env python3
"""Validate the narrow post-U-06 U-07 design authorization decision."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "config/u07_design_authorization_v1.json"
U06_RESULT = ROOT / "reports/m1/evidence/u06_cross_sectional_paper_observation/run_manifest.json"
U05_RESULT = ROOT / "reports/m1/evidence/u05_cross_sectional_paper_observation/run_manifest.json"
U04_RESULT = ROOT / "reports/m1/evidence/u04_cross_sectional_paper_observation/run_manifest.json"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
EXPECTED_HASH = "58f8301035e593b0621add93cfa876a11a5af52df0a3afae38d7b41f095e37d5"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(document: Mapping[str, Any], u06: Mapping[str, Any], u05: Mapping[str, Any], u04: Mapping[str, Any], audit: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}}
    if document.get("content_hash") != EXPECTED_HASH or canonical_hash(identity) != EXPECTED_HASH:
        failures.append("U-07 decision identity changed")
    bindings = document.get("bindings", {})
    for label, prior, field in (("U-06", u06, "u06_run_content_hash"), ("U-05", u05, "u05_run_content_hash"), ("U-04", u04, "u04_run_content_hash")):
        if bindings.get(field) != prior.get("run_content_hash"):
            failures.append(f"{label} result binding changed")
        if prior.get("status") != "failed_feasibility" or prior.get("oos_opened") is not False or prior.get("second_run_executed") is not False:
            failures.append(f"{label} must remain failed, single-run and OOS-sealed")
    if bindings.get("adr0015_audit_summary_hash") != audit.get("audit_summary_hash"):
        failures.append("audit summary binding changed")
    if bindings.get("v4_artifact_set_hash") != audit.get("independent_artifact_set_hash"):
        failures.append("artifact-set binding changed")
    if audit.get("verdict") != "pass" or audit.get("manifests_exact") != 19 or audit.get("manifests_total") != 19:
        failures.append("passing 19/19 audit dependency is absent")
    decision = document.get("decision", {})
    if decision.get("u07_design_authorized") is not True or decision.get("maximum_hypotheses") != 1:
        failures.append("one-hypothesis U-07 design authority changed")
    for key in ("independent_economic_rationale_required", "u04_u05_u06_outcome_derived_direction_or_rule_prohibited", "outcome_blind_preregistration_required", "separate_protocol_before_any_event_scan"):
        if decision.get(key) is not True:
            failures.append(f"required design invariant changed: {key}")
    expected_authorizations = {
        "u07_hypothesis_design": True, "event_scan": False, "signals": False,
        "returns": False, "strategy_rule_selection": False, "freqtrade_strategy_code": False,
        "backtesting": False, "oos": False, "api_trading": False,
        "execution_live": False, "m2": False,
    }
    if document.get("authorizations") != expected_authorizations:
        failures.append("U-07 authorization matrix changed")
    stops = document.get("stop_conditions", [])
    if not any("may not be inverted" in str(item) for item in stops):
        failures.append("prior-outcome inversion prohibition missing")
    return failures


def main() -> int:
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))
    failures = validate(load(DECISION), load(U06_RESULT), load(U05_RESULT), load(U04_RESULT), load(AUDIT))
    if failures:
        print("u07_design_authorization_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("u07_design_authorization_check PASS")
    print(f"decision_content_hash={EXPECTED_HASH}")
    print("design=yes event_scan=no strategy=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
