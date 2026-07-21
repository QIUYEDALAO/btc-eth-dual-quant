#!/usr/bin/env python3
"""Fail-closed validation for the result-blind ADR-0018 contract."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/adr0018_scheduled_market_cessation_forced_exit_v1.json"
DECISION = ROOT / "docs/decisions/ADR-0018-scheduled-market-cessation-forced-exit.md"
SOURCE_PREFLIGHT = ROOT / "reports/m1/evidence/external_strategy_boundary_authority/source_preflight.json"
COMMAND_EVIDENCE = ROOT / "reports/m1/evidence/external_strategy_boundary_authority/source_preflight_command.json"
AUTHORIZATION = ROOT / "config/membership_exit_boundary_authorization_v1.json"
QUALIFICATION = ROOT / "reports/m1/evidence/external_strategy_runtime/is_boundary_qualification.json"
OOS_GUARD = ROOT / "config/external_strategy_oos_guard_v1.json"
TRIAL_STATE = ROOT / "config/external_strategy_candidate_freeze_v1.json"
PR116_REVIEW = ROOT / "reports/expert/evidence/pr116_exact_head_review_v1.json"

EXPECTED = "8761fabac1f32d518d6c75c08dcf0a37288262059fe3192b87fb44de836b46e9"
DECISION_BYTES = "0cf8f7ee99b2c9bda23dd036c2ccb5e38d95772213095a617b38c5f0137ea8d0"
PR116_HEAD = "edf753f28f26f6a168798fa40b49bcbd121a2adc"
PR116_REVIEW_HASH = "b873227e3777db6a867294c35986a021fdff12dee4353a7c40312e0a1bc4b10d"


def digest(value: Mapping[str, Any]) -> str:
    identity = {key: item for key, item in value.items() if key not in {"content_hash", "generated_utc"}}
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("timestamp is not explicit UTC")
    return parsed.astimezone(timezone.utc)


def derive_forced_exit_open(cessation_utc: str) -> str:
    cessation = parse_utc(cessation_utc)
    if cessation.second or cessation.microsecond or cessation.minute % 5:
        raise ValueError("cessation is not on the 5m grid")
    result = cessation - timedelta(minutes=5)
    return result.isoformat().replace("+00:00", "Z")


def _load(root: Path, relative: Path) -> dict[str, Any]:
    return json.loads((root / relative.relative_to(ROOT)).read_text(encoding="utf-8"))


def validate(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    try:
        contract = _load(root, CONTRACT)
        source = _load(root, SOURCE_PREFLIGHT)
        command = _load(root, COMMAND_EVIDENCE)
        authorization = _load(root, AUTHORIZATION)
        qualification = _load(root, QUALIFICATION)
        oos = _load(root, OOS_GUARD)
        trial = _load(root, TRIAL_STATE)
        review = _load(root, PR116_REVIEW)
        decision_bytes = (root / DECISION.relative_to(ROOT)).read_bytes()
    except (OSError, json.JSONDecodeError) as exc:
        return [f"bound artifact unreadable: {exc}"]

    if contract.get("content_hash") != EXPECTED or digest(contract) != EXPECTED:
        failures.append("ADR-0018 canonical identity mismatch")
    if hashlib.sha256(decision_bytes).hexdigest() != DECISION_BYTES:
        failures.append("ADR-0018 decision bytes drift")
    if review.get("content_hash") != PR116_REVIEW_HASH or digest(review) != PR116_REVIEW_HASH:
        failures.append("PR #116 review identity mismatch")
    if review.get("reviewed_head") != PR116_HEAD or review.get("critical_findings") != 0 or review.get("high_findings") != 0:
        failures.append("PR #116 exact review verdict drift")
    if review.get("verdict") != "approve_pending_exact_head_github_gate":
        failures.append("PR #116 review verdict changed")

    bindings = contract.get("bindings", {})
    exact_bindings = {
        "original_boundary_qualification_hash": qualification.get("content_hash"),
        "pr116_command_evidence_hash": command.get("content_hash"),
        "pr116_reviewed_head": PR116_HEAD,
        "pr116_source_preflight_hash": source.get("content_hash"),
        "prior_boundary_design_authorization_hash": authorization.get("reviewer_provided_canonical_content_hash"),
        "repository": "QIUYEDALAO/btc-eth-dual-quant",
    }
    if bindings != exact_bindings:
        failures.append("ADR-0018 evidence bindings drift")

    revision = contract.get("boundary_set_revision", {})
    expected_replacement = {
        "add": ["RNDRUSDT", "2024-07-22T02:55:00Z"],
        "remove": ["RNDRUSDT", "2024-08-01T00:00:00Z"],
    }
    if revision.get("one_for_one_replacement") != expected_replacement:
        failures.append("boundary replacement drift")
    if revision.get("total_identity_count") != 92 or revision.get("unchanged_original_monthly_boundaries") != 91:
        failures.append("boundary count drift")
    if revision.get("additions_beyond_replacement") != 0 or revision.get("deletions_beyond_replacement") != 0:
        failures.append("boundary scope expanded")
    if revision.get("must_receive_new_canonical_hash") is not True or revision.get("result_blind") is not True:
        failures.append("new result-blind boundary identity is not mandatory")

    event = contract.get("rndr_event", {})
    try:
        derived = derive_forced_exit_open(event.get("spot_trading_cessation_utc", ""))
        announcement_date = datetime.fromisoformat(event.get("official_announcement_publication_date", "")).date()
        cessation_date = parse_utc(event.get("spot_trading_cessation_utc", "")).date()
    except (TypeError, ValueError) as exc:
        failures.append(f"RNDR event timestamp invalid: {exc}")
    else:
        if derived != event.get("candidate_forced_exit_open_utc"):
            failures.append("RNDR forced-exit open is not derived from cessation")
        if announcement_date >= cessation_date:
            failures.append("official announcement is not prior to cessation")
    if event.get("candidate_forced_exit_close_time_utc") != "2024-07-22T02:59:59.999Z":
        failures.append("RNDR forced-exit close drift")
    if event.get("exact_archive_and_row_not_yet_validated") is not True:
        failures.append("unvalidated RNDR archive was presented as evidence")
    if event.get("predecessor_symbol") != "RNDRUSDT" or event.get("successor_symbol") != "RENDERUSDT":
        failures.append("RNDR/RENDER provenance identity drift")
    for key in ("use_render_history_for_rndr_or_future_membership", "use_render_price_for_rndr_exit"):
        if event.get(key) is not False:
            failures.append(f"successor substitution enabled: {key}")

    rule = contract.get("generic_rule", {})
    expected_precedence = [
        "close every already-open position in the predecessor symbol at the forced-exit open",
        "reject any new entry scheduled for the same open",
        "reject all later predecessor-symbol signals and fills",
    ]
    if rule.get("forced_exit_precedence") != expected_precedence:
        failures.append("forced-exit precedence drift")
    required_true = (
        "announcement_exact_timestamp_required_before_authority_freeze",
        "announcement_must_be_known_before_forced_exit",
        "official_venue_announcement_required",
        "reset_and_rewarm_required_after_any_later_readmission",
    )
    required_false = (
        "append_boundary_row_to_candidate_ohlcv",
        "append_boundary_row_to_indicator_history",
        "forward_search_allowed",
        "indicator_state_crosses_inactive_interval",
        "successor_inherits_history_or_rank",
        "successor_inherits_position",
    )
    for key in required_true:
        if rule.get(key) is not True:
            failures.append(f"required lifecycle rule disabled: {key}")
    for key in required_false:
        if rule.get(key) is not False:
            failures.append(f"forbidden lifecycle behavior enabled: {key}")
    if rule.get("boundary_row_use") != "forced_exit_lookup_only" or rule.get("successor_symbol_authority") != "provenance_only":
        failures.append("boundary or successor authority drift")

    permissions = contract.get("permissions", {})
    expected_true = {
        "adr0018_contract_design",
        "official_public_preflight_for_rndr_original_symbol",
        "pr116_blocked_evidence_merge_after_gate",
    }
    if {key for key, value in permissions.items() if value is True} != expected_true:
        failures.append("ADR-0018 permission matrix drift")
    for key in (
        "api_private_endpoints", "boundary_archive_acquisition_before_adr0018_merge",
        "boundary_authority_freeze_before_adr0018_merge", "dry_run", "execution_live", "m2",
        "modified_is", "oos", "order_placement", "original_is", "paper_live",
        "selection_trial_materialization",
    ):
        if permissions.get(key) is not False:
            failures.append(f"forbidden permission enabled: {key}")

    preflight = contract.get("required_preflight_before_freeze", {})
    if preflight.get("normal_reverse_shuffled_independent_constructions_required") is not True:
        failures.append("NB-01 independent construction requirement removed")
    if review.get("non_blocking_finding", {}).get("id") != "NB-01":
        failures.append("PR #116 NB-01 review finding missing")
    if preflight.get("market_rows_outside_fixed_boundary_rows") != 0 or preflight.get("oos_rows_decoded") != 0 or preflight.get("strategy_results_read") != 0:
        failures.append("preflight zero-access boundary drift")

    if trial.get("selection_trial_count") != 0:
        failures.append("selection trial materialized before authority freeze")
    if oos.get("oos_authorized") is not False or oos.get("oos_opened") is not False or oos.get("oos_runs") != 0 or oos.get("oos_rows_decoded") != 0:
        failures.append("OOS guard is not sealed")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(f"ADR-0018 scheduled cessation contract PASS: {EXPECTED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
