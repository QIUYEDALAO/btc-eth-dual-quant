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

SCOPE = ROOT / "config/u18_cross_sectional_design_scope_v1.json"
LEDGER = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
AUTHORIZATION = ROOT / "config/u18_design_authorization_v1.json"
FAILURE = ROOT / "reports/m1/evidence/u17_cross_sectional_data_qualification_v1.json"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE = "U18-CROSS-SECTIONAL-IDIOSYNCRATIC-DOWNSIDE-TAIL-RISK-PREMIUM"
HYPOTHESIS = "U18-CROSS-SECTIONAL-IDIOSYNCRATIC-DOWNSIDE-TAIL-RISK-PREMIUM: Binance spot USDT long/cash only; using only completed prior observations from the exact point-in-time active member set, an asset whose returns retain persistent left-tail asymmetry after removing the contemporaneous peer common component may expose holders to crash, liquidation and liquidity-withdrawal risk, and investors may require a positive cross-sectional premium that can accrue after the next eligible open; no U-04 through U-17 outcome, defect or failure reuse, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption."
HYPOTHESIS_HASH = "e6b84d1b6e9cb979dd973fed42c20821858704c362e24b4a342aef25359778c4"
CONTENT_HASH = "487d9b11883d2eb38f2171bf6fe57b1e2e5040b31032e03de73cea9bb5c62df8"


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
    if economics.get("family") != "cross_sectional_idiosyncratic_downside_tail_risk_premium" or len(economics.get("mechanism", [])) != 5 or len(economics.get("failure_regimes", [])) != 10:
        findings.append("mechanism coverage changed")
    for section in ("causal_and_membership_invariants", "non_duplication"):
        if not scope.get(section) or any(value is not True for value in scope[section].values()):
            findings.append(f"{section} changed")
    if len(scope.get("unresolved_until_separate_protocol", [])) != 20:
        findings.append("rules resolved prematurely")
    expected = {"u18_paper_protocol_design": True, "public_data_read": False, "event_scan": False, "signals": False, "returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if scope.get("authorizations") != expected:
        findings.append("authorization matrix changed")
    return findings


def validate_all() -> list[str]:
    findings = validate_scope(load(SCOPE))
    ledger = yaml.safe_load(LEDGER.read_text())
    matches = [item for item in ledger["candidates"] if item.get("id") == CANDIDATE]
    if len(matches) != 1 or matches[0].get("hypothesis") != HYPOTHESIS or matches[0].get("sha256") != HYPOTHESIS_HASH or hashlib.sha256(matches[0].get("hypothesis", "").encode()).hexdigest() != HYPOTHESIS_HASH or matches[0].get("status") != "declared_unopened" or matches[0].get("oos_opened") is not False:
        findings.append("ledger identity changed")
    if load(AUTHORIZATION).get("content_hash") != "eb78548edfb57859deea0433412ef772e92bad6c249caab8e3e3af3e91fcc0b1":
        findings.append("authorization drift")
    failure = load(FAILURE)
    if failure.get("qualification_content_hash") != "434d8a58a19306e9ff340da3b8df0c85fe15848c2686ed15491dee05ac64af91" or failure.get("decision", {}).get("candidate_closed") is not True:
        findings.append("U-17 failure drift")
    if load(AUDIT).get("verdict") != "pass":
        findings.append("audit drift")
    return findings


def main() -> int:
    findings = validate_all()
    if findings:
        print("u18_cross_sectional_design_check FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"u18_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
