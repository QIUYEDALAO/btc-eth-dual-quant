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

SCOPE = ROOT / "config/u17_cross_sectional_design_scope_v1.json"
LEDGER = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
AUTHORIZATION = ROOT / "config/u17_design_authorization_v1.json"
RUN = ROOT / "reports/m1/evidence/u16_cross_sectional_paper_observation/run_manifest.json"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE = "U17-CROSS-SECTIONAL-LIQUIDITY-RISK-PREMIUM"
HYPOTHESIS = "U17-CROSS-SECTIONAL-LIQUIDITY-RISK-PREMIUM: Binance spot USDT long/cash only; using only completed prior observations from the exact point-in-time active member set, an asset that remains investable inside the frozen liquid universe yet persistently ranks below its active peers in trading liquidity may require compensation for marginal immediacy, crowding-exit and capital-capacity risk, and that cross-sectional liquidity risk premium may accrue after the next eligible open; no U-04 through U-16 outcome, defect or failure reuse, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption."
HYPOTHESIS_HASH = "19b0e7eaa4d9f8432b733d3660a76226c9e3351674d21a819adf266515261fea"
CONTENT_HASH = "ad3b6a4cabc61bd41890684ccf30b8ee4ae3a2811fcc4dd08abcf45a4bf420fe"


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
    if economics.get("family") != "cross_sectional_liquidity_risk_premium" or len(economics.get("mechanism", [])) != 5 or len(economics.get("failure_regimes", [])) != 10:
        findings.append("mechanism coverage changed")
    for section in ("causal_and_membership_invariants", "non_duplication"):
        if not scope.get(section) or any(value is not True for value in scope[section].values()):
            findings.append(f"{section} changed")
    if len(scope.get("unresolved_until_separate_protocol", [])) != 20:
        findings.append("rules resolved prematurely")
    expected = {
        "u17_paper_protocol_design": True,
        "public_data_read": False,
        "event_scan": False,
        "signals": False,
        "returns": False,
        "fixed_rule_contract": False,
        "freqtrade_strategy_code": False,
        "backtesting": False,
        "oos": False,
        "api_trading": False,
        "execution_live": False,
        "m2": False,
    }
    if scope.get("authorizations") != expected:
        findings.append("authorization matrix changed")
    return findings


def validate_all() -> list[str]:
    findings = validate_scope(load(SCOPE))
    ledger = yaml.safe_load(LEDGER.read_text())
    matches = [item for item in ledger["candidates"] if item.get("id") == CANDIDATE]
    if (
        len(matches) != 1
        or matches[0].get("hypothesis") != HYPOTHESIS
        or matches[0].get("sha256") != HYPOTHESIS_HASH
        or hashlib.sha256(matches[0].get("hypothesis", "").encode()).hexdigest() != HYPOTHESIS_HASH
        or matches[0].get("status") != "declared_unopened"
        or matches[0].get("oos_opened") is not False
    ):
        findings.append("ledger identity changed")
    if load(AUTHORIZATION).get("content_hash") != "eb93310f631709ff4fb3514a0ffccac24a16f5ef401156e3f158beaca397420b":
        findings.append("authorization drift")
    run = load(RUN)
    if run.get("run_content_hash") != "322fda776158c5c035a30821460ac3acd7477a99b747aa6d08bfa68a55984d14" or run.get("status") != "failed_feasibility" or run.get("oos_opened") is not False:
        findings.append("U-16 result drift")
    if load(AUDIT).get("verdict") != "pass":
        findings.append("audit drift")
    return findings


def main() -> int:
    findings = validate_all()
    if findings:
        print("u17_cross_sectional_design_check FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"u17_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
