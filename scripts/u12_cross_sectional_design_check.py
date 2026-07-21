#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "config/u12_cross_sectional_design_scope_v1.json"
LEDGER = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
AUTHORIZATION = ROOT / "config/u12_design_authorization_v1.json"
U11_ATTEMPT = ROOT / "reports/m1/evidence/u11_cross_sectional_paper_observation/run_manifest.json"
U11_ADJUDICATION = ROOT / "reports/m1/U11_PAPER_OBSERVATION_ADJUDICATION.md"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE = "U12-CROSS-SECTIONAL-RECURRING-CALENDAR-FLOW-SEASONALITY"
HYPOTHESIS = "U12-CROSS-SECTIONAL-RECURRING-CALENDAR-FLOW-SEASONALITY: Binance spot USDT long/cash only; using only completed prior occurrences and the exact point-in-time active member set, an asset-specific relative return pattern that recurs in the same predeclared UTC calendar state across disjoint historical subperiods may reflect recurring regional participation, settlement, treasury or mandate flows and may persist after the next eligible open; no U-04 through U-10 outcome reuse, U-11 invalid-result or defect reuse, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption."
HYPOTHESIS_HASH = "5942e15d4c4dde246979ef980f0fc3c2a3f545e9e6717159355ee4312c87f54d"
CONTENT_HASH = "e53003e7c9255fc11d976a646f8700532cc98ad6fd1c410b00647957daa6d5dc"


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
    if hypothesis.get("family") != "cross_sectional_recurring_calendar_flow_seasonality" or len(hypothesis.get("failure_regimes", [])) != 10 or len(hypothesis.get("mechanism", [])) != 5:
        failures.append("mechanism coverage changed")
    for section in ("causal_and_membership_invariants", "non_duplication"):
        if not document.get(section) or any(value is not True for value in document[section].values()):
            failures.append(f"{section} changed")
    if len(document.get("unresolved_until_separate_protocol", [])) != 19:
        failures.append("rules resolved prematurely")
    expected = {"u12_paper_protocol_design": True, "public_data_read": False, "event_scan": False, "signals": False, "returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if document.get("authorizations") != expected:
        failures.append("authorization matrix changed")
    return failures


def validate_all() -> list[str]:
    failures = validate_scope(load(SCOPE))
    ledger = yaml.safe_load(LEDGER.read_text())
    matches = [item for item in ledger["candidates"] if str(item.get("id", "")).startswith("U12-")]
    if len(matches) != 1 or matches[0].get("hypothesis") != HYPOTHESIS or matches[0].get("sha256") != HYPOTHESIS_HASH or hashlib.sha256(matches[0].get("hypothesis", "").encode()).hexdigest() != HYPOTHESIS_HASH or matches[0].get("status") != "declared_unopened" or matches[0].get("oos_opened") is not False:
        failures.append("ledger identity changed")
    if load(AUTHORIZATION).get("content_hash") != "ecb8fd7801eda5a42652091a27bad46368d4193240d58423827cdc8c8c8602e7":
        failures.append("authorization drift")
    attempt = load(U11_ATTEMPT)
    if attempt.get("run_content_hash") != "0a55b61c83daea4c2f7c61e35db06b50c563a108c23cb74d35b1cb55888a9521" or attempt.get("oos_opened") is not False or attempt.get("second_run_executed") is not False:
        failures.append("U-11 attempt drift")
    adjudication = U11_ADJUDICATION.read_text()
    if "failed_execution_invalid_observation" not in adjudication or "Retry authorized: `false`" not in adjudication:
        failures.append("U-11 adjudication drift")
    if load(AUDIT).get("verdict") != "pass":
        failures.append("audit drift")
    return failures


def main() -> int:
    failures = validate_all()
    if failures:
        print("u12_cross_sectional_design_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u12_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
