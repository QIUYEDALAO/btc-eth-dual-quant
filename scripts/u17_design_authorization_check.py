#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "config/u17_design_authorization_v1.json"
RUN = ROOT / "reports/m1/evidence/u16_cross_sectional_paper_observation/run_manifest.json"
PRIOR = ROOT / "config/u16_design_authorization_v1.json"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
EXPECTED = "eb93310f631709ff4fb3514a0ffccac24a16f5ef401156e3f158beaca397420b"


def identity_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate(
    decision: Mapping[str, Any],
    run: Mapping[str, Any],
    prior: Mapping[str, Any],
    audit: Mapping[str, Any],
) -> list[str]:
    findings: list[str] = []
    identity = {
        key: value
        for key, value in decision.items()
        if key not in {"content_hash", "generated_utc"}
    }
    bindings = decision.get("bindings", {})
    if decision.get("content_hash") != EXPECTED or identity_hash(identity) != EXPECTED:
        findings.append("identity")
    if (
        bindings.get("u16_run_content_hash") != run.get("run_content_hash")
        or run.get("status") != "failed_feasibility"
        or bindings.get("u16_status") != run.get("status")
    ):
        findings.append("U-16 result binding")
    if (
        run.get("oos_opened") is not False
        or run.get("oos_rows_decoded") != 0
        or run.get("formal_returns_computed") is not False
        or run.get("second_run_executed") is not False
        or bindings.get("u16_oos_opened") is not False
        or bindings.get("u16_formal_returns_computed") is not False
        or bindings.get("u16_second_run_executed") is not False
    ):
        findings.append("U-16 isolation")
    if (
        bindings.get("u16_protocol_content_hash") != run.get("protocol_content_hash")
        or bindings.get("u16_qualification_content_hash") != run.get("qualification_content_hash")
        or bindings.get("u16_design_authorization_hash") != prior.get("content_hash")
        or bindings.get("adr0015_audit_summary_hash") != audit.get("audit_summary_hash")
        or bindings.get("v4_artifact_set_hash") != audit.get("independent_artifact_set_hash")
        or bindings.get("source_freeze_hash") != audit.get("diagnostics", {}).get("source_freeze_content_hash")
    ):
        findings.append("authority")
    required = (
        "u17_design_authorized",
        "independent_economic_rationale_required",
        "u04_through_u16_outcome_direction_threshold_rule_censor_or_failure_reuse_prohibited",
        "u16_failed_gate_repair_relaxation_inversion_or_repackaging_prohibited",
        "prior_failed_candidate_repair_retry_inversion_or_relabeling_prohibited",
        "outcome_blind_preregistration_required",
        "separate_protocol_before_any_data_or_event_scan",
        "pre_result_data_authority_sample_ceiling_and_complexity_preflight_required",
    )
    rules = decision.get("decision", {})
    if rules.get("maximum_hypotheses") != 1 or any(rules.get(key) is not True for key in required):
        findings.append("decision")
    if [key for key, value in decision.get("authorizations", {}).items() if value] != ["u17_hypothesis_design"]:
        findings.append("authorization")
    return findings


def main() -> int:
    load = lambda path: json.loads(path.read_text())
    findings = validate(load(DECISION), load(RUN), load(PRIOR), load(AUDIT))
    print("u17_design_authorization_check " + ("PASS" if not findings else "FAIL") + f" hash={EXPECTED}")
    return bool(findings)


if __name__ == "__main__":
    raise SystemExit(main())
