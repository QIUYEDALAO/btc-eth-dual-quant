#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
import yaml

SCOPE = ROOT / "config/u19_cross_sectional_design_scope_v1.json"
LEDGER = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
AUTHORIZATION = ROOT / "config/u19_design_authorization_v1.json"
FAILURE = ROOT / "reports/m1/evidence/u18_cross_sectional_paper_observation/run_manifest.json"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE = "U19-CROSS-SECTIONAL-IDIOSYNCRATIC-VOLATILITY-OF-VOLATILITY-RISK-PREMIUM"
HYPOTHESIS = "U19-CROSS-SECTIONAL-IDIOSYNCRATIC-VOLATILITY-OF-VOLATILITY-RISK-PREMIUM: Binance spot USDT long/cash only; using only completed prior observations from the exact point-in-time active member set, an asset whose common-component-adjusted volatility itself varies persistently and unpredictably may impose unstable risk-budget, hedging and liquidity-capital demands, and investors may require a positive cross-sectional premium that can accrue after the next eligible open; no U-04 through U-18 outcome, defect or failure reuse, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption."
HYPOTHESIS_HASH = "6b3cd19be7fedab64bfc43ad6c667cdbe774d58994073446a340cf7f55217c52"
CONTENT_HASH = "89cd46e632d5d890b5c2b13c71a63642ab1ed5a2167904df0f722a5d4279fe80"


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def identity_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_scope(scope: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    identity = {key: value for key, value in scope.items() if key not in {"content_hash", "generated_utc"}}
    if scope.get("content_hash") != CONTENT_HASH or identity_hash(identity) != CONTENT_HASH:
        findings.append("design identity changed")
    if scope.get("candidate_id") != CANDIDATE or scope.get("hypothesis_sha256") != HYPOTHESIS_HASH:
        findings.append("candidate identity changed")
    economics = scope.get("economic_hypothesis", {})
    if economics.get("family") != "cross_sectional_idiosyncratic_volatility_of_volatility_risk_premium" or len(economics.get("mechanism", [])) != 5 or len(economics.get("failure_regimes", [])) != 10:
        findings.append("mechanism coverage changed")
    for section in ("causal_and_membership_invariants", "non_duplication"):
        if not scope.get(section) or any(value is not True for value in scope[section].values()):
            findings.append(f"{section} changed")
    if len(scope.get("unresolved_until_separate_protocol", [])) != 20:
        findings.append("rules resolved prematurely")
    expected = {"u19_paper_protocol_design": True, "public_data_read": False, "event_scan": False, "signals": False, "returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if scope.get("authorizations") != expected:
        findings.append("authorization matrix changed")
    return findings


def validate_all() -> list[str]:
    findings = validate_scope(load(SCOPE))
    ledger = yaml.safe_load(LEDGER.read_text())
    matches = [item for item in ledger["candidates"] if item.get("id") == CANDIDATE]
    if len(matches) != 1 or matches[0].get("hypothesis") != HYPOTHESIS or matches[0].get("sha256") != HYPOTHESIS_HASH or hashlib.sha256(matches[0].get("hypothesis", "").encode()).hexdigest() != HYPOTHESIS_HASH or matches[0].get("status") != "declared_unopened" or matches[0].get("oos_opened") is not False:
        findings.append("ledger identity changed")
    if load(AUTHORIZATION).get("content_hash") != "0996522977d3a54fe35f29220bcd0ca9dd4f2aebd1533d610c6aececf250c3a9":
        findings.append("authorization drift")
    failure = load(FAILURE)
    if failure.get("run_content_hash") != "213c303dc81f23f0f8bb0d37c1f114636ca0cbd76c0bae1f3c432a5b2cf9c3cd" or failure.get("status") != "failed_feasibility" or failure.get("oos_opened") is not False:
        findings.append("U-18 failure drift")
    if load(AUDIT).get("verdict") != "pass":
        findings.append("audit drift")
    return findings


def main() -> int:
    findings = validate_all()
    if findings:
        print("u19_cross_sectional_design_check FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"u19_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
