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

SCOPE = ROOT / "config/u23_cross_sectional_design_scope_v1.json"
LEDGER = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
AUTHORIZATION = ROOT / "config/u23_design_authorization_v1.json"
FAILURE = ROOT / "reports/m1/evidence/u22_cross_sectional_paper_observation/run_manifest.json"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE = "U23-CROSS-SECTIONAL-RANGE-EXPANSION-CLOSE-STRENGTH-CONTINUATION"
HYPOTHESIS = "U23-CROSS-SECTIONAL-RANGE-EXPANSION-CLOSE-STRENGTH-CONTINUATION: Binance spot USDT long/cash only; using only completed prior OHLC observations from the exact point-in-time active member set, an asset whose completed trading range expands unusually relative to its own completed history while its close remains near the completed range high and positive relative to active peers may reveal aggressive demand and incomplete price discovery, so relative strength may continue after the next eligible open; no U-04 through U-22 outcome, defect or failure reuse, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption."
HYPOTHESIS_HASH = "6c099769b5fb89d7faf032d68c114540a6b93f8546bbedee26c2e9397e98627f"
CONTENT_HASH = "351ddd25e3c8708e55a21e81921d104f4c360b65966945b846fa40ba1e96e6e0"


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
    if economics.get("family") != "cross_sectional_range_expansion_close_strength_continuation" or len(economics.get("mechanism", [])) != 5 or len(economics.get("failure_regimes", [])) != 9:
        findings.append("mechanism coverage changed")
    for section in ("causal_and_membership_invariants", "non_duplication"):
        if not scope.get(section) or any(value is not True for value in scope[section].values()):
            findings.append(f"{section} changed")
    if len(scope.get("unresolved_until_separate_protocol", [])) != 20:
        findings.append("rules resolved prematurely")
    expected = {"u23_paper_protocol_design": True, "synthetic_only_exact_core_feasibility": True, "public_data_read": False, "event_scan": False, "signals": False, "returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if scope.get("authorizations") != expected:
        findings.append("authorization matrix changed")
    return findings


def validate_all() -> list[str]:
    findings = validate_scope(load(SCOPE))
    ledger = yaml.safe_load(LEDGER.read_text())
    matches = [item for item in ledger["candidates"] if item.get("id") == CANDIDATE]
    if len(matches) != 1 or matches[0].get("hypothesis") != HYPOTHESIS or matches[0].get("sha256") != HYPOTHESIS_HASH or hashlib.sha256(matches[0].get("hypothesis", "").encode()).hexdigest() != HYPOTHESIS_HASH or matches[0].get("status") != "declared_unopened" or matches[0].get("oos_opened") is not False:
        findings.append("ledger identity changed")
    if load(AUTHORIZATION).get("content_hash") != "70c60434bb7c78344eb733eb8a8d4393538f60bbc97bff60e840c68f10998d5a":
        findings.append("authorization drift")
    failure = load(FAILURE)
    if failure.get("run_content_hash") != "12a756e2fa8a0fa2e2b87f69c8dc00559f3021a27368a0ac4efc8f5e8001531c" or failure.get("status") != "failed_feasibility" or failure.get("oos_opened") is not False or failure.get("second_run_executed") is not False:
        findings.append("U-22 failure drift")
    if load(AUDIT).get("verdict") != "pass":
        findings.append("audit drift")
    return findings


def main() -> int:
    findings = validate_all()
    if findings:
        print("u23_cross_sectional_design_check FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"u23_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
