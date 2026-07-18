#!/usr/bin/env python3
"""Validate the outcome-blind U-07 market-stress relative-strength design."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "config/u07_cross_sectional_design_scope_v1.json"
LEDGER_PATH = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
AUTH_PATH = ROOT / "config/u07_design_authorization_v1.json"
PRIOR_PATHS = [
    ROOT / "reports/m1/evidence/u06_cross_sectional_paper_observation/run_manifest.json",
    ROOT / "reports/m1/evidence/u05_cross_sectional_paper_observation/run_manifest.json",
    ROOT / "reports/m1/evidence/u04_cross_sectional_paper_observation/run_manifest.json",
]
AUDIT_PATH = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
EXPECTED_CANDIDATE = "U07-CROSS-SECTIONAL-MARKET-STRESS-RELATIVE-STRENGTH-CONTINUATION"
EXPECTED_HYPOTHESIS = "U07-CROSS-SECTIONAL-MARKET-STRESS-RELATIVE-STRENGTH-CONTINUATION: Binance spot USDT long/cash only; using only completed observations from the exact point-in-time active member set, broad contemporaneous market selling pressure combined with an asset retaining unusually strong relative price may indicate inelastic asset-specific demand that can continue to lead after the stress flow subsides and no earlier than the next eligible open; no U-04/U-05/U-06 outcome inversion, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption."
EXPECTED_HYPOTHESIS_HASH = "3130450cd7bd7cddab4bce0c89b274ae93e50bed278379011cc4d09e15fb3de3"
EXPECTED_CONTENT_HASH = "272eabd4ab1737566698309b98cc13b952a8d39b86c457674d58ff56de021795"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_scope(scope: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    required = {"schema_version", "status", "candidate_id", "hypothesis_sha256", "bindings", "research_scope", "economic_hypothesis", "causal_and_membership_invariants", "non_duplication", "unresolved_until_separate_protocol", "authorizations", "content_hash", "generated_utc"}
    if set(scope) != required:
        failures.append("design schema changed or gained a premature rule")
    identity = {key: value for key, value in scope.items() if key not in {"content_hash", "generated_utc"}}
    if scope.get("content_hash") != EXPECTED_CONTENT_HASH or canonical_hash(identity) != EXPECTED_CONTENT_HASH:
        failures.append("design content identity changed")
    if scope.get("candidate_id") != EXPECTED_CANDIDATE or scope.get("hypothesis_sha256") != EXPECTED_HYPOTHESIS_HASH:
        failures.append("candidate identity changed")
    bindings = scope.get("bindings", {})
    expected_bindings = {
        "u07_design_authorization_hash": "58f8301035e593b0621add93cfa876a11a5af52df0a3afae38d7b41f095e37d5",
        "u06_closed_run_hash": "2f715394411ca260f9889304ddc84da926d37ec1dfc9d4316493f23f6881382a",
        "u05_closed_run_hash": "874cdac32b63535f4b5636420dc55719e8dc795a66e5eca2be96f88ca3737e4a",
        "u04_closed_run_hash": "9182c9e3fb2aad6959d98ccbe18c77e411a3d5ce5adc6fdf352da76cd53eebc2",
    }
    if any(bindings.get(key) != value for key, value in expected_bindings.items()):
        failures.append("authorization or prior closure binding changed")
    economics = scope.get("economic_hypothesis", {})
    if economics.get("family") != "cross_sectional_market_stress_relative_strength_continuation" or len(economics.get("failure_regimes", [])) != 9:
        failures.append("economic mechanism or failure regime coverage changed")
    for section in ("causal_and_membership_invariants", "non_duplication"):
        if not scope.get(section) or any(value is not True for value in scope[section].values()):
            failures.append(f"{section} changed")
    unresolved = scope.get("unresolved_until_separate_protocol", [])
    if len(unresolved) != 15 or not all(any(token in str(item) for item in unresolved) for token in ("timeframe", "threshold", "horizon", "exit", "stop", "position")):
        failures.append("protocol or fixed-rule fields were resolved prematurely")
    expected_auth = {"u07_paper_protocol_design": True, "event_scan": False, "signals": False, "returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if scope.get("authorizations") != expected_auth:
        failures.append("only U-07 Paper protocol design may be authorized")
    return failures


def validate_ledger() -> list[str]:
    ledger = yaml.safe_load(LEDGER_PATH.read_text(encoding="utf-8"))
    matches = [item for item in ledger.get("candidates", []) if str(item.get("id", "")).startswith("U07-")]
    if len(matches) != 1:
        return ["exactly one U-07 candidate must be registered"]
    candidate = matches[0]
    if candidate.get("hypothesis") != EXPECTED_HYPOTHESIS or candidate.get("sha256") != EXPECTED_HYPOTHESIS_HASH or hashlib.sha256(candidate.get("hypothesis", "").encode()).hexdigest() != EXPECTED_HYPOTHESIS_HASH or candidate.get("status") != "declared_unopened" or candidate.get("oos_opened") is not False:
        return ["U-07 ledger identity or sealed status changed"]
    return []


def validate_bound_evidence() -> list[str]:
    auth, audit = load_json(AUTH_PATH), load_json(AUDIT_PATH)
    failures: list[str] = []
    if auth.get("content_hash") != "58f8301035e593b0621add93cfa876a11a5af52df0a3afae38d7b41f095e37d5":
        failures.append("U-07 authorization drifted")
    expected_prior = ["2f715394411ca260f9889304ddc84da926d37ec1dfc9d4316493f23f6881382a", "874cdac32b63535f4b5636420dc55719e8dc795a66e5eca2be96f88ca3737e4a", "9182c9e3fb2aad6959d98ccbe18c77e411a3d5ce5adc6fdf352da76cd53eebc2"]
    for path, expected in zip(PRIOR_PATHS, expected_prior):
        prior = load_json(path)
        if prior.get("run_content_hash") != expected or prior.get("status") != "failed_feasibility" or prior.get("oos_opened") is not False or prior.get("second_run_executed") is not False:
            failures.append(f"prior closed result drifted: {path.name}")
    if audit.get("audit_summary_hash") != "e26c9a084767e0f3f29a479552d14d24ac27d0a0fff426f953c811bac3d606c4" or audit.get("verdict") != "pass":
        failures.append("ADR-0015 audit drifted")
    return failures


def main() -> int:
    failures = validate_scope(load_json(SCOPE_PATH)) + validate_ledger() + validate_bound_evidence()
    if failures:
        print("u07_cross_sectional_design_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print(f"u07_cross_sectional_design_check PASS candidate={EXPECTED_CANDIDATE} content_hash={EXPECTED_CONTENT_HASH}")
    print("authorized_next=paper_protocol_design events=no returns=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
