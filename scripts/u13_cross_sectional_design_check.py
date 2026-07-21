#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "config/u13_cross_sectional_design_scope_v1.json"
LEDGER = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
AUTHORIZATION = ROOT / "config/u13_design_authorization_v1.json"
U12_RESULT = ROOT / "reports/m1/evidence/u12_cross_sectional_paper_observation/run_manifest.json"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE = "U13-CROSS-SECTIONAL-COMMON-SHOCK-LAGGED-DIFFUSION"
HYPOTHESIS = "U13-CROSS-SECTIONAL-COMMON-SHOCK-LAGGED-DIFFUSION: Binance spot USDT long/cash only; using only completed observations and exact point-in-time active members, a broad positive common-market information or capital-flow shock may be absorbed at different speeds across assets, and an asset with a preregistered prior-only tendency to respond with delay rather than permanent weakness may continue catching up after the next eligible open; no U-04 through U-12 outcome reuse, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption."
HYPOTHESIS_HASH = "39f1848fe195be8e6c406a5e21b734ce9c469a9df5c08eaa0a70de348988db5c"
CONTENT_HASH = "982cb95125a94dd10d5524dab0c241fbd7642639e1dd3461da760024d9fd3477"


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_scope(document: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}}
    if document.get("content_hash") != CONTENT_HASH or canonical_hash(identity) != CONTENT_HASH:
        failures.append("design identity changed")
    if document.get("candidate_id") != CANDIDATE or document.get("hypothesis_sha256") != HYPOTHESIS_HASH:
        failures.append("candidate identity changed")
    hypothesis = document.get("economic_hypothesis", {})
    if hypothesis.get("family") != "cross_sectional_common_shock_lagged_information_diffusion" or len(hypothesis.get("failure_regimes", [])) != 10 or len(hypothesis.get("mechanism", [])) != 5:
        failures.append("mechanism coverage changed")
    for section in ("causal_and_membership_invariants", "non_duplication"):
        if not document.get(section) or any(value is not True for value in document[section].values()):
            failures.append(f"{section} changed")
    if len(document.get("unresolved_until_separate_protocol", [])) != 19:
        failures.append("rules resolved prematurely")
    expected = {"u13_paper_protocol_design": True, "public_data_read": False, "event_scan": False, "signals": False, "returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if document.get("authorizations") != expected:
        failures.append("authorization matrix changed")
    return failures


def validate_all() -> list[str]:
    failures = validate_scope(load(SCOPE))
    ledger = yaml.safe_load(LEDGER.read_text())
    matches = [item for item in ledger["candidates"] if str(item.get("id", "")).startswith("U13-")]
    if len(matches) != 1 or matches[0].get("hypothesis") != HYPOTHESIS or matches[0].get("sha256") != HYPOTHESIS_HASH or hashlib.sha256(matches[0].get("hypothesis", "").encode()).hexdigest() != HYPOTHESIS_HASH or matches[0].get("status") != "declared_unopened" or matches[0].get("oos_opened") is not False:
        failures.append("ledger identity changed")
    if load(AUTHORIZATION).get("content_hash") != "8900ada4819a2d951fd26ab6a1d61e18e0e43de939207787c63e05f925866ce6":
        failures.append("authorization drift")
    result = load(U12_RESULT)
    if result.get("run_content_hash") != "b42a539c555e37b8b3871910bf5fc21397db3ea01044dee3bbfe3bf7902e7995" or result.get("oos_opened") is not False or result.get("second_run_executed") is not False:
        failures.append("U-12 result drift")
    if load(AUDIT).get("verdict") != "pass":
        failures.append("audit drift")
    return failures


def main() -> int:
    failures = validate_all()
    if failures:
        print("u13_cross_sectional_design_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u13_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
