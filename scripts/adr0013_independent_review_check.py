#!/usr/bin/env python3
"""Build and verify the frozen independent review of ADR-0013."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.data.liquid_universe import canonical_hash  # noqa: E402


EVIDENCE_PATH = ROOT / "reports/expert/evidence/adr0013_independent_review.json"
REPORT_PATH = ROOT / "reports/expert/ADR_0013_INDEPENDENT_REVIEW.md"

EXPECTED_REVIEW_QUESTION_IDS = {f"Q{index:02d}" for index in range(1, 16)}
EXPECTED_MANDATORY_CHANGE_IDS = {f"A{index}" for index in range(1, 11)}
ZERO_AUTHORIZATIONS = {
    "v3_implementation": False,
    "u03e_v3_rerun": False,
    "u03f": False,
    "u04": False,
    "hypothesis_preregistration": False,
    "strategy_code": False,
    "event_scan": False,
    "returns_or_backtesting": False,
    "oos": False,
    "api_or_trading": False,
    "m2": False,
}
EXPECTED_ARTIFACTS = {
    "base_main_sha": "7477c34a403cdbdcf0a7dcc36c4646d32e6d5b83",
    "adr_pr": 74,
    "adr_draft_head_sha": "8dc9ee034fdd172147485f7718117f8a76713cdf",
    "adr_draft_evidence_commit": "4a95a28142d13aa2f03f271baf660ae95ba67e78",
    "adr_draft_content_sha256": "c285a6cfea04c127ca17a537d9c97d4a8931400c3aefe0c2c7c19654e2bcecfc",
    "adjudication_evidence_hash": "8214079900d311c232ecde4b348712f2a5a6d958c8cd98270b9501a71f77330b",
    "v2_contract_hash": "051894e89b713f541caa601efab51be22f83461a4e624e1d51d7f576ed8cda51",
    "v2_source_manifest_hash": "928c3520028ddf5bfc1c03fe3185d5af4b9ad8fea0f327469d60f388a3f638cf",
    "v2_qualification_summary_hash": "80cd0a88b6253f06aeb40bfe4123aa55f874ce31a40d2e94a46859b2aba8380c",
}


def _question(question_id: str, topic: str, finding: str, required_change: str | None) -> dict[str, Any]:
    return {
        "id": question_id,
        "topic": topic,
        "finding": finding,
        "assessment": "pass" if required_change is None else "approve_with_required_changes",
        "required_change": required_change,
    }


def _mandatory(change_id: str, title: str, requirement: str) -> dict[str, Any]:
    return {
        "id": change_id,
        "title": title,
        "required": True,
        "draft_status": "missing_or_incomplete",
        "requirement": requirement,
    }


def build_review_document() -> dict[str, Any]:
    questions = [
        _question("Q01", "Exact duplicate collapse is information-lossless", "Canonical collapse can be lossless only when every raw row, line number, multiplicity and hash remains immutable provenance.", "Freeze the raw-preservation and canonical-collapse manifest contract in A4/A7."),
        _question("Q02", "Raw multiplicity is permanently retained", "The draft states retention but does not define a machine schema that proves all raw members remain present.", "Bind multiplicity, all raw-row hashes and retained canonical hash in A4."),
        _question("Q03", "Invalid monthly to daily replacement has sufficient official evidence", "The five BTT rows have checksum-verified daily ZIP evidence and two agreeing public REST comparators, but runtime use must not depend on mutable REST.", "Freeze comparator payloads and row evidence in the A1 registry and enforce A5 candidate qualification."),
        _question("Q04", "REST remains corroboration", "The draft correctly rejects REST as primary history.", "Make frozen REST evidence registry-only and prohibit live REST adoption during qualification under A1/A6."),
        _question("Q05", "Offline deterministic replay", "The draft is not replay-complete because it has no versioned resolution registry or hash binding.", "Add A1, A6 and A9 before adoption."),
        _question("Q06", "Live REST drift", "The evidence probe is networked and current REST can change; using it during qualification would make results time-dependent.", "Qualification must consume only frozen comparator evidence and fail on binding mismatch."),
        _question("Q07", "Conflicting duplicate cannot be misclassified", "The classifier distinguishes exact, semantic and conflicting groups, but the policy must classify the complete key group rather than a selected pair.", "Freeze the complete-group rule, including two-identical-plus-one-conflicting, in A2/A4."),
        _question("Q08", "Collapse cannot hide a later conflict", "Collapsing before complete-key grouping can hide a third differing row.", "Group all raw rows before any collapse and block any heterogeneous group under A2."),
        _question("Q09", "No source-order or thread-order dependency", "The proposed result is deterministic in principle, but the exact processing order and order-independent hashes are not specified.", "Freeze A2 and require cold/warm/worker equality in the first V3 rerun."),
        _question("Q10", "No asset or date special cases", "The proposal is asset- and time-neutral and rejects special cases.", "V3 must enforce registry-driven generic resolution and static fault tests under A6."),
        _question("Q11", "Membership rules remain unchanged", "Top-15, prior-90-day median, 365-day history, UTC activation and tie-break are explicitly unchanged.", None),
        _question("Q12", "No outcome dependence", "The policy uses source validity and frozen provenance, not membership or strategy outcomes.", None),
        _question("Q13", "Fail-closed behavior", "The draft intends fail-closed behavior but an unknown conflict could still match a broad rule without a registry.", "Require exact conflict/source/evidence bindings and blocked_pending_adjudication in A6."),
        _question("Q14", "New schemas are required", "V2 cannot represent approved canonical source resolutions without changing authority semantics.", "Create V3 contract, resolution registry, canonicalization and manifest schemas bound by A9."),
        _question("Q15", "Future U-03F auditability", "Independent audit is feasible if raw and canonical quarantines, resolution IDs, source hashes and deterministic manifests are separately exposed.", "Implement A7/A9; U-03F remains unauthorized until a truthful V3 qualification pass."),
    ]
    mandatory = [
        _mandatory("A1", "Frozen comparator evidence", "Create a versioned hash-bound resolution registry; qualification must not query live REST to adopt a row."),
        _mandatory("A2", "Fixed processing order", "Freeze ZIP/schema verification, raw retention, full-key grouping, duplicate classification, candidate validation, registry resolution, provenance, merge, eligibility and panel order."),
        _mandatory("A3", "Canonical key and 12-field semantics", "Freeze symbol/interval/open_time UTC key, exact field names/types, Decimal equality and the equality role of ignore."),
        _mandatory("A4", "Complete duplicate-group rules", "Collapse only complete groups whose every raw 12-field string is identical; preserve all members; block semantic, conflicting and parser-created groups."),
        _mandatory("A5", "Daily correction candidate qualification", "Require checksum/schema/uniqueness/validity, complete duplicate processing, two frozen REST matches, monthly equality except invalid fields and no unresolved conflict."),
        _mandatory("A6", "Fail-closed resolution registry", "Resolve only exact registered conflict/source/evidence hashes under an adopted V3 contract; every unknown conflict becomes blocked_pending_adjudication."),
        _mandatory("A7", "Two quarantine layers", "Separate raw_row_quarantine from research_panel_quarantine and report duplicate collapses, monthly quarantine, admitted corrections, unresolved conflicts, blocked months and zero synthetic fills."),
        _mandatory("A8", "Fixed first V3 range", "Freeze the first V3 public comparison to 2020-01-01 through 2026-06; later accrual is a separate task."),
        _mandatory("A9", "Contract hash bindings", "Bind eligibility registry, conflict policy, resolution registry, adjudication evidence/schema, source/canonical schemas and authorization matrix into the V3 contract hash."),
        _mandatory("A10", "Governance SHA semantics", "Store current PR head_sha separately from the first frozen evidence_commit and validate that neither field impersonates the other."),
    ]
    unsigned = {
        "schema_version": 1,
        "manifest_type": "adr0013_independent_review",
        "reviewed_artifacts": dict(EXPECTED_ARTIFACTS),
        "content": {
            "verdict": "approve_with_required_changes",
            "policy_adopted": False,
            "review_questions": questions,
            "mandatory_changes": mandatory,
            "authorizations": dict(ZERO_AUTHORIZATIONS),
            "stop_condition": "ADR-0013 remains proposed and V2 remains blocked until every mandatory change is implemented and independently checked.",
        },
    }
    return {**unsigned, "content_hash": canonical_hash(unsigned)}


def verify_review_document(document: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if document.get("schema_version") != 1 or document.get("manifest_type") != "adr0013_independent_review":
        failures.append("review identity mismatch")
    unsigned = {key: value for key, value in document.items() if key != "content_hash"}
    if document.get("content_hash") != canonical_hash(unsigned):
        failures.append("content hash mismatch")
    artifacts = document.get("reviewed_artifacts", {})
    for key, value in EXPECTED_ARTIFACTS.items():
        if artifacts.get(key) != value:
            failures.append(f"reviewed artifact binding changed: {key}")
    content = document.get("content", {})
    if content.get("verdict") != "approve_with_required_changes" or content.get("policy_adopted") is not False:
        failures.append("verdict or adoption state changed")
    questions = content.get("review_questions", [])
    if {item.get("id") for item in questions} != EXPECTED_REVIEW_QUESTION_IDS or len(questions) != 15:
        failures.append("review question set mismatch")
    mandatory = content.get("mandatory_changes", [])
    if {item.get("id") for item in mandatory} != EXPECTED_MANDATORY_CHANGE_IDS or len(mandatory) != 10:
        failures.append("mandatory change set mismatch")
    if any(item.get("required") is not True or item.get("draft_status") != "missing_or_incomplete" for item in mandatory):
        failures.append("mandatory change no longer blocks adoption")
    if content.get("authorizations") != ZERO_AUTHORIZATIONS:
        failures.append("authorization matrix changed")
    return failures


def render_report(document: dict[str, Any]) -> str:
    content = document["content"]
    lines = [
        "# ADR-0013 Independent Review",
        "",
        f"- Verdict: `{content['verdict']}`",
        "- Policy adopted: no",
        f"- Reviewed main: `{document['reviewed_artifacts']['base_main_sha']}`",
        f"- Reviewed PR #74 head: `{document['reviewed_artifacts']['adr_draft_head_sha']}`",
        f"- ADR evidence commit: `{document['reviewed_artifacts']['adr_draft_evidence_commit']}`",
        f"- ADR draft SHA256: `{document['reviewed_artifacts']['adr_draft_content_sha256']}`",
        f"- PR #73 adjudication evidence: `{document['reviewed_artifacts']['adjudication_evidence_hash']}`",
        "",
        "## Executive Decision",
        "",
        "The general policy direction is defensible: exact raw duplicates may be collapsed only in a derived canonical layer, and an invalid monthly row may use a checksum-verified daily correction only when independent frozen official evidence agrees. The current Draft is not adoption-ready because it does not yet freeze the resolution registry, complete-key processing order, field semantics, quarantine accounting, first comparison range, hash bindings, or governance SHA meanings.",
        "",
        "ADR-0013 therefore remains proposed. V2 remains truthfully blocked. No V3 implementation or rerun is authorized by this review.",
        "",
        "## Review Questions",
        "",
        "| ID | Topic | Assessment | Finding | Required change |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in content["review_questions"]:
        required = item["required_change"] or "None"
        lines.append(f"| {item['id']} | {item['topic']} | `{item['assessment']}` | {item['finding']} | {required} |")
    lines.extend(["", "## Mandatory Changes Before Adoption", ""])
    for item in content["mandatory_changes"]:
        lines.append(f"- **{item['id']} {item['title']}**: {item['requirement']}")
    lines.extend([
        "",
        "## Evidence Conclusions",
        "",
        "- BTTUSDT: five negative monthly `base_volume` rows are checksum-bound official monthly/daily conflicts. Daily ZIP rows and two public REST comparators agree; the unsigned-overflow signature is explanatory only and may never generate a value.",
        "- AXSUSDT: the monthly and daily archives each contain two byte-identical rows for one canonical key; REST returns one matching row. Any canonical collapse must retain raw multiplicity and both raw row hashes.",
        "- Existing V2 helpers distinguish byte-identical, semantic-identical, conflicting and parser-created duplicates, but V3 must classify the entire key group before collapse.",
        "- REST can corroborate frozen evidence but cannot become historical authority or a live qualification dependency.",
        "- Top-15, 90-day median quote volume, 365-day history, UTC activation, exclusions and symbol tie-break remain unchanged.",
        "",
        "## Authorization",
        "",
        "- V3 implementation authorized: no",
        "- U-03E V3 rerun authorized: no",
        "- U-03F authorized: no",
        "- U-04 authorized: no",
        "- Strategy, events, returns, backtesting, OOS, API/trading and M2 authorized: no",
        "",
        f"Machine evidence hash: `{document['content_hash']}`",
        "",
    ])
    return "\n".join(lines)


def canonical_json(document: dict[str, Any]) -> str:
    return json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    expected = build_review_document()
    if args.write:
        EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE_PATH.write_text(canonical_json(expected), encoding="utf-8")
        REPORT_PATH.write_text(render_report(expected), encoding="utf-8")
        print(f"ADR0013_INDEPENDENT_REVIEW_WRITE {expected['content_hash']}")
        return 0
    failures = verify_review_document(json.loads(EVIDENCE_PATH.read_text(encoding="utf-8")))
    if EVIDENCE_PATH.read_text(encoding="utf-8") != canonical_json(expected):
        failures.append("committed machine review differs from deterministic render")
    if REPORT_PATH.read_text(encoding="utf-8") != render_report(expected):
        failures.append("committed report differs from deterministic render")
    if failures:
        for failure in sorted(set(failures)):
            print(f"FAIL {failure}")
        return 1
    print(f"ADR0013_INDEPENDENT_REVIEW_CHECK PASS {expected['content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
