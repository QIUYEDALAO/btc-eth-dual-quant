#!/usr/bin/env python3
"""Validate the outcome-blind U-06 volume-share absorption design."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "config/u06_cross_sectional_design_scope_v1.json"
LEDGER_PATH = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
AUTH_PATH = ROOT / "config/u06_design_authorization_v1.json"
U05_PATH = ROOT / "reports/m1/evidence/u05_cross_sectional_paper_observation/run_manifest.json"
AUDIT_PATH = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
EXPECTED_CANDIDATE = "U06-CROSS-SECTIONAL-VOLUME-SHARE-ABSORPTION-REPRICING"
EXPECTED_HYPOTHESIS = "U06-CROSS-SECTIONAL-VOLUME-SHARE-ABSORPTION-REPRICING: Binance spot USDT long/cash only; using completed prior observations from exact active members, a persistent increase in an asset's cross-sectional quote-volume share without a commensurate relative price advance may reflect liquidity absorption and latent demand that can reprice after the next eligible open; no U-04/U-05 outcome inversion, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption."
EXPECTED_HYPOTHESIS_HASH = "e6cb136b5bfaa4948b1681696b33496a43b7f9ab1f4fc25dcea63714700c259b"
EXPECTED_CONTENT_HASH = "694e5a4344481bf785b09ff9f69a7c170d6c3d7061407902306cee70176966a5"


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
    if bindings.get("u06_design_authorization_hash") != "596eacbcf2caec7dd1da27bb66ee8bb5859c5b6992c067f22d40e5305cb74662" or bindings.get("u05_closed_run_hash") != "874cdac32b63535f4b5636420dc55719e8dc795a66e5eca2be96f88ca3737e4a":
        failures.append("authorization or U-05 closure binding changed")
    if scope.get("economic_hypothesis", {}).get("family") != "cross_sectional_quote_volume_share_absorption_then_repricing" or len(scope.get("economic_hypothesis", {}).get("failure_regimes", [])) != 8:
        failures.append("economic mechanism or failure regime coverage changed")
    for section in ("causal_and_membership_invariants", "non_duplication"):
        if not scope.get(section) or any(value is not True for value in scope[section].values()):
            failures.append(f"{section} changed")
    unresolved = scope.get("unresolved_until_separate_protocol", [])
    if len(unresolved) != 15 or not all(any(token in str(item) for item in unresolved) for token in ("timeframe", "threshold", "horizon", "exit", "stop", "position")):
        failures.append("protocol or fixed-rule fields were resolved prematurely")
    expected_auth = {"u06_paper_protocol_design": True, "event_scan": False, "signals": False, "returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if scope.get("authorizations") != expected_auth:
        failures.append("only U-06 Paper protocol design may be authorized")
    return failures


def validate_ledger() -> list[str]:
    ledger = yaml.safe_load(LEDGER_PATH.read_text(encoding="utf-8"))
    matches = [item for item in ledger.get("candidates", []) if str(item.get("id", "")).startswith("U06-")]
    if len(matches) != 1:
        return ["exactly one U-06 candidate must be registered"]
    candidate = matches[0]
    if candidate.get("hypothesis") != EXPECTED_HYPOTHESIS or candidate.get("sha256") != EXPECTED_HYPOTHESIS_HASH or hashlib.sha256(candidate.get("hypothesis", "").encode()).hexdigest() != EXPECTED_HYPOTHESIS_HASH or candidate.get("status") != "declared_unopened" or candidate.get("oos_opened") is not False:
        return ["U-06 ledger identity or sealed status changed"]
    return []


def validate_bound_evidence() -> list[str]:
    auth, u05, audit = load_json(AUTH_PATH), load_json(U05_PATH), load_json(AUDIT_PATH)
    failures: list[str] = []
    if auth.get("content_hash") != "596eacbcf2caec7dd1da27bb66ee8bb5859c5b6992c067f22d40e5305cb74662": failures.append("U-06 authorization drifted")
    if u05.get("run_content_hash") != "874cdac32b63535f4b5636420dc55719e8dc795a66e5eca2be96f88ca3737e4a" or u05.get("status") != "failed_feasibility" or u05.get("oos_opened") is not False: failures.append("U-05 closed result drifted")
    if audit.get("audit_summary_hash") != "e26c9a084767e0f3f29a479552d14d24ac27d0a0fff426f953c811bac3d606c4" or audit.get("verdict") != "pass": failures.append("ADR-0015 audit drifted")
    return failures


def main() -> int:
    failures = validate_scope(load_json(SCOPE_PATH)) + validate_ledger() + validate_bound_evidence()
    if failures:
        print("u06_cross_sectional_design_check FAIL")
        for item in failures: print(f"- {item}")
        return 1
    print(f"u06_cross_sectional_design_check PASS candidate={EXPECTED_CANDIDATE} content_hash={EXPECTED_CONTENT_HASH}")
    print("authorized_next=paper_protocol_design events=no returns=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__": raise SystemExit(main())
