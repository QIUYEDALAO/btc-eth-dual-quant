#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "config/u22_design_authorization_v1.json"
FAILURE = ROOT / "reports/m1/evidence/u21_cross_sectional_data_qualification_v1.json"
PRIOR = ROOT / "config/u21_design_authorization_v1.json"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
EXPECTED = "82aef7f378a1aaa46ded62cfc21dedb67e6d86a8d0c27c24f66280d8c124e29d"


def identity_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(decision: Mapping[str, Any], failure: Mapping[str, Any], prior: Mapping[str, Any], audit: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    identity = {key: value for key, value in decision.items() if key not in {"content_hash", "generated_utc"}}
    bindings = decision.get("bindings", {})
    if decision.get("content_hash") != EXPECTED or identity_hash(identity) != EXPECTED:
        findings.append("identity")
    if bindings.get("u21_qualification_content_hash") != failure.get("qualification_content_hash") or failure.get("status") != "failed_pre_result_complexity":
        findings.append("U-21 failure binding")
    isolation = failure.get("isolation", {})
    if failure.get("candidate_closed") is not True or failure.get("failure", {}).get("retry_executed") is not False or isolation.get("frozen_source_archives_opened") != 0 or isolation.get("oos_opened") is not False:
        findings.append("U-21 isolation")
    if bindings.get("u21_protocol_content_hash") != failure.get("protocol_content_hash") or bindings.get("u21_design_authorization_hash") != prior.get("content_hash") or bindings.get("adr0015_audit_summary_hash") != audit.get("audit_summary_hash") or bindings.get("v4_artifact_set_hash") != audit.get("independent_artifact_set_hash") or bindings.get("source_freeze_hash") != audit.get("diagnostics", {}).get("source_freeze_content_hash"):
        findings.append("authority")
    required = (
        "u22_design_authorized",
        "independent_economic_rationale_required",
        "u04_through_u21_outcome_direction_threshold_rule_censor_or_failure_reuse_prohibited",
        "u21_complexity_failure_optimization_retry_repair_relabeling_or_repackaging_prohibited",
        "prior_failed_candidate_repair_retry_inversion_or_relabeling_prohibited",
        "outcome_blind_preregistration_required",
        "synthetic_only_exact_core_complexity_feasibility_required_before_protocol_freeze",
        "separate_protocol_before_any_public_data_or_event_scan",
        "pre_result_data_authority_sample_ceiling_and_complexity_preflight_required",
    )
    rules = decision.get("decision", {})
    if rules.get("maximum_hypotheses") != 1 or any(rules.get(key) is not True for key in required):
        findings.append("decision")
    if [key for key, value in decision.get("authorizations", {}).items() if value] != ["u22_hypothesis_design"]:
        findings.append("authorization")
    return findings


def main() -> int:
    load = lambda path: json.loads(path.read_text())
    findings = validate(load(DECISION), load(FAILURE), load(PRIOR), load(AUDIT))
    print("u22_design_authorization_check " + ("PASS" if not findings else "FAIL") + f" hash={EXPECTED}")
    return bool(findings)


if __name__ == "__main__":
    raise SystemExit(main())
