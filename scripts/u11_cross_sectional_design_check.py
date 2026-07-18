#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "config/u11_cross_sectional_design_scope_v1.json"
LEDGER = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
AUTHORIZATION = ROOT / "config/u11_design_authorization_v1.json"
U10_RESULT = ROOT / "reports/m1/evidence/u10_cross_sectional_paper_observation/run_manifest.json"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE = "U11-CROSS-SECTIONAL-ASYMMETRIC-MARKET-CAPTURE-QUALITY-PERSISTENCE"
HYPOTHESIS = "U11-CROSS-SECTIONAL-ASYMMETRIC-MARKET-CAPTURE-QUALITY-PERSISTENCE: Binance spot USDT long/cash only; using only completed observations from the exact point-in-time active member set, an asset that persistently participates in positive common-market moves while preserving capital during negative common-market moves may reflect a stable demand base, lower forced-selling sensitivity and asymmetric quality that can persist after the next eligible open; no U-04 through U-10 outcome or defect reuse, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption."
HYPOTHESIS_HASH = "1c9ef854245c3f46000712894392b5b97a865013355c4553e372c6d168f63e74"
CONTENT_HASH = "0572daf7511c673a89dff6e737ad12528dde6c40845b672d62bbd3b1aeca9e4c"


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
    if hypothesis.get("family") != "cross_sectional_asymmetric_market_capture_quality_persistence" or len(hypothesis.get("failure_regimes", [])) != 9 or len(hypothesis.get("mechanism", [])) != 5:
        failures.append("mechanism coverage changed")
    for section in ("causal_and_membership_invariants", "non_duplication"):
        if not document.get(section) or any(value is not True for value in document[section].values()):
            failures.append(f"{section} changed")
    if len(document.get("unresolved_until_separate_protocol", [])) != 17:
        failures.append("rules resolved prematurely")
    expected = {"u11_paper_protocol_design": True, "event_scan": False, "signals": False, "returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if document.get("authorizations") != expected:
        failures.append("authorization matrix changed")
    return failures


def validate_all() -> list[str]:
    failures = validate_scope(load(SCOPE))
    ledger = yaml.safe_load(LEDGER.read_text())
    matches = [item for item in ledger["candidates"] if str(item.get("id", "")).startswith("U11-")]
    if len(matches) != 1 or matches[0].get("hypothesis") != HYPOTHESIS or matches[0].get("sha256") != HYPOTHESIS_HASH or hashlib.sha256(matches[0].get("hypothesis", "").encode()).hexdigest() != HYPOTHESIS_HASH or matches[0].get("status") != "declared_unopened" or matches[0].get("oos_opened") is not False:
        failures.append("ledger identity changed")
    if load(AUTHORIZATION).get("content_hash") != "c5db3dc0c01bc4e1ffe381150c132742446ce4b05b3fb8c381dc03612cff274a":
        failures.append("authorization drift")
    result = load(U10_RESULT)
    if result.get("status") != "failed_feasibility" or result.get("oos_opened") is not False or result.get("second_run_executed") is not False:
        failures.append("U-10 result drift")
    if load(AUDIT).get("verdict") != "pass":
        failures.append("audit drift")
    return failures


def main() -> int:
    failures = validate_all()
    if failures:
        print("u11_cross_sectional_design_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u11_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
