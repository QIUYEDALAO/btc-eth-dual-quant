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

SCOPE = ROOT / "config/u20_cross_sectional_design_scope_v1.json"
LEDGER = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
AUTHORIZATION = ROOT / "config/u20_design_authorization_v1.json"
FAILURE = ROOT / "reports/m1/evidence/u19_cross_sectional_paper_observation/run_manifest.json"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE = "U20-CROSS-SECTIONAL-NEGATIVE-COSKEWNESS-RISK-PREMIUM"
HYPOTHESIS = "U20-CROSS-SECTIONAL-NEGATIVE-COSKEWNESS-RISK-PREMIUM: Binance spot USDT long/cash only; using only completed prior observations from the exact point-in-time active member set, an asset whose common-adjusted returns exhibit persistently negative coskewness with the active-universe common return may deliver disproportionately poor relative outcomes during large common moves, and investors may require a positive cross-sectional premium that can accrue after the next eligible open; no U-04 through U-19 outcome, defect or failure reuse, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption."
HYPOTHESIS_HASH = "9d17a514b9e13eff5dd885382ab7c9df5c14e9a71283a219d43c901648e46bdb"
CONTENT_HASH = "3995e92a9ae69fd64f8258b33b620c801d63e235e1ed90a254a3d99d70a1e5b5"


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
    if economics.get("family") != "cross_sectional_negative_coskewness_risk_premium" or len(economics.get("mechanism", [])) != 5 or len(economics.get("failure_regimes", [])) != 9:
        findings.append("mechanism coverage changed")
    for section in ("causal_and_membership_invariants", "non_duplication"):
        if not scope.get(section) or any(value is not True for value in scope[section].values()):
            findings.append(f"{section} changed")
    if len(scope.get("unresolved_until_separate_protocol", [])) != 19:
        findings.append("rules resolved prematurely")
    expected = {"u20_paper_protocol_design": True, "public_data_read": False, "event_scan": False, "signals": False, "returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if scope.get("authorizations") != expected:
        findings.append("authorization matrix changed")
    return findings


def validate_all() -> list[str]:
    findings = validate_scope(load(SCOPE))
    ledger = yaml.safe_load(LEDGER.read_text())
    matches = [item for item in ledger["candidates"] if item.get("id") == CANDIDATE]
    if len(matches) != 1 or matches[0].get("hypothesis") != HYPOTHESIS or matches[0].get("sha256") != HYPOTHESIS_HASH or hashlib.sha256(matches[0].get("hypothesis", "").encode()).hexdigest() != HYPOTHESIS_HASH or matches[0].get("status") != "declared_unopened" or matches[0].get("oos_opened") is not False:
        findings.append("ledger identity changed")
    if load(AUTHORIZATION).get("content_hash") != "b4e9d5c94957d69142e328a05dfb00474840efe3347dd5347c55997115b64455":
        findings.append("authorization drift")
    failure = load(FAILURE)
    if failure.get("run_content_hash") != "38daffb0834c28a769108c74f256b601f08667c7076d107bc97f48925b63f3d4" or failure.get("status") != "failed_feasibility" or failure.get("oos_opened") is not False:
        findings.append("U-19 failure drift")
    if load(AUDIT).get("verdict") != "pass":
        findings.append("audit drift")
    return findings


def main() -> int:
    findings = validate_all()
    if findings:
        print("u20_cross_sectional_design_check FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"u20_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
