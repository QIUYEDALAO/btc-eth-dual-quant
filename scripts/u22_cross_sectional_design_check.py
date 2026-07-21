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

SCOPE = ROOT / "config/u22_cross_sectional_design_scope_v1.json"
LEDGER = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
AUTHORIZATION = ROOT / "config/u22_design_authorization_v1.json"
FAILURE = ROOT / "reports/m1/evidence/u21_cross_sectional_data_qualification_v1.json"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE = "U22-CROSS-SECTIONAL-DISPERSION-EXPANSION-LEADER-CONTINUATION"
HYPOTHESIS = "U22-CROSS-SECTIONAL-DISPERSION-EXPANSION-LEADER-CONTINUATION: Binance spot USDT long/cash only; using only completed prior observations from the exact point-in-time active member set, a broadening cross-sectional return-dispersion regime in which one asset develops multi-observation positive peer-relative leadership without single-observation dominance may reflect segmented attention, capital rotation and gradual price discovery, so relative leadership may continue after the next eligible open; no U-04 through U-21 outcome, defect or failure reuse, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption."
HYPOTHESIS_HASH = "4ec9eba4d04169fe90caf50f4eaa914f1784339802b148a1cff43f5a07cb77d3"
CONTENT_HASH = "652677b1e0c070d27d854166c9c7d692e93d7f58236eced06c94f01abb153abe"


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
    if economics.get("family") != "cross_sectional_dispersion_expansion_leader_continuation" or len(economics.get("mechanism", [])) != 5 or len(economics.get("failure_regimes", [])) != 9:
        findings.append("mechanism coverage changed")
    for section in ("causal_and_membership_invariants", "non_duplication"):
        if not scope.get(section) or any(value is not True for value in scope[section].values()):
            findings.append(f"{section} changed")
    if len(scope.get("unresolved_until_separate_protocol", [])) != 20:
        findings.append("rules resolved prematurely")
    expected = {"u22_paper_protocol_design": True, "synthetic_only_exact_core_feasibility": True, "public_data_read": False, "event_scan": False, "signals": False, "returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if scope.get("authorizations") != expected:
        findings.append("authorization matrix changed")
    return findings


def validate_all() -> list[str]:
    findings = validate_scope(load(SCOPE))
    ledger = yaml.safe_load(LEDGER.read_text())
    matches = [item for item in ledger["candidates"] if item.get("id") == CANDIDATE]
    if len(matches) != 1 or matches[0].get("hypothesis") != HYPOTHESIS or matches[0].get("sha256") != HYPOTHESIS_HASH or hashlib.sha256(matches[0].get("hypothesis", "").encode()).hexdigest() != HYPOTHESIS_HASH or matches[0].get("status") != "declared_unopened" or matches[0].get("oos_opened") is not False:
        findings.append("ledger identity changed")
    if load(AUTHORIZATION).get("content_hash") != "82aef7f378a1aaa46ded62cfc21dedb67e6d86a8d0c27c24f66280d8c124e29d":
        findings.append("authorization drift")
    failure = load(FAILURE)
    if failure.get("qualification_content_hash") != "33e53b7fd32c6610349f99bb01cf71143ab9837289198266fd1b25f6e7147a1b" or failure.get("status") != "failed_pre_result_complexity" or failure.get("candidate_closed") is not True or failure.get("isolation", {}).get("oos_opened") is not False:
        findings.append("U-21 failure drift")
    if load(AUDIT).get("verdict") != "pass":
        findings.append("audit drift")
    return findings


def main() -> int:
    findings = validate_all()
    if findings:
        print("u22_cross_sectional_design_check FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"u22_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
