#!/usr/bin/env python3
"""Build and verify the frozen independent review of proposed ADR-0014."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "reports/expert/evidence/adr0014_independent_review.json"
REPORT_PATH = ROOT / "reports/expert/ADR_0014_INDEPENDENT_REVIEW.md"

EXPECTED_CHANGED_FILES = [
    ".github/workflows/adr0014-draft-policy-validate.yml",
    "AGENTS.md",
    "NEXT_ACTION.md",
    "PROJECT_EXECUTION_CHECKLIST.md",
    "PROJECT_LEDGER.md",
    "PROJECT_STATE.yaml",
    "docs/decisions/ADR-0014-official-lifecycle-boundary-placeholder-policy.md",
    "reports/INDEX.md",
    "scripts/adr0014_draft_policy_check.py",
    "scripts/adr0014_draft_policy_validate.sh",
    "scripts/project_state_transition_check.py",
    "tests/test_adr0014_draft_policy.py",
    "tests/test_liquid_universe_v3_klay_conflict.py",
]
EXPECTED_ARTIFACTS = {
    "reviewed_pr_number": 81,
    "reviewed_pr_state": "OPEN_DRAFT_MERGEABLE",
    "reviewed_pr_head": "cd4a1d8fb53870cdf8a3a683a4942a2c81b58f44",
    "reviewed_base_branch": "main",
    "reviewed_base_sha": "d2d876af192a23ff1879d6a09cb2737c3f12133f",
    "adr_path": "docs/decisions/ADR-0014-official-lifecycle-boundary-placeholder-policy.md",
    "adr_blob_sha": "35c492acfb3cbd1af5291ffdd68384429f1d8ce9",
    "adr_content_sha256": "7350d691e2b7158a9cd985b3e53cf0c504a1147c39791c844d2ad4b4b5ede8a9",
    "changed_file_list_sha256": "5de2d40f14ab74b905f8a924a3f89acd0e2f10d1350c87665097cbc3bce99315",
    "changed_file_list_hash_algorithm": "sha256(canonical_json(sorted_utf8_paths)))",
    "changed_files": EXPECTED_CHANGED_FILES,
    "klay_adjudication_evidence_hash": "6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a",
}
EXPECTED_REVIEW_QUESTION_IDS = {f"Q{index:02d}" for index in range(1, 13)}
EXPECTED_MANDATORY_CHANGE_IDS = {f"MC-{index:02d}" for index in range(1, 12)}
EXPECTED_AUTHORIZATIONS = {
    "adr0014_adopted": False,
    "pr81_ready": False,
    "pr81_merge": False,
    "contract_mutation": False,
    "registry_mutation": False,
    "v4_implementation": False,
    "v3_or_v4_requalification": False,
    "cold_warm_or_worker_build": False,
    "u03f": False,
    "u04": False,
    "strategy_design_or_code": False,
    "event_scan": False,
    "returns_or_backtesting": False,
    "oos_access": False,
    "api_or_trading": False,
    "execution_live": False,
    "m2": False,
}
FAULT_INJECTION_TESTS = [
    "cessation exactly at a UTC day boundary",
    "cessation exactly at a 5m boundary",
    "cessation exactly at a 1h boundary",
    "cessation not aligned to any bar boundary",
    "cessation-day partial daily row",
    "post-cessation normal-duration zero-volume placeholder",
    "post-cessation close-before-open placeholder",
    "multiple post-cessation placeholders",
    "monthly/daily/REST disagreement",
    "intraday archive absence without lifecycle announcement",
    "lifecycle announcement while intraday trading continues",
    "temporary suspension",
    "permanent delisting",
    "migration",
    "announced successor",
    "same ticker relisted as a new epoch",
    "evidence publication later than effective time",
    "official checksum update",
    "registry content-hash change",
    "unregistered lifecycle event",
    "overlapping availability epochs",
    "member and non-member lifecycle events",
    "no replacement member",
    "active member count decline",
    "90/365 complete-day windows exclude partial lifecycle day",
    "post-cessation absence does not create a gap",
    "pre-cessation gap remains blocking",
    "no stale-price forward-fill or cross-boundary return",
    "no symbol/date special case",
]


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def content_identity(document: dict[str, Any]) -> dict[str, Any]:
    """Return the review identity, explicitly excluding review wall-clock time."""
    return {
        "schema_version": document["schema_version"],
        "manifest_type": document["manifest_type"],
        "reviewed_artifacts": document["reviewed_artifacts"],
        "content": document["content"],
    }


def _question(
    review_id: str,
    question: str,
    evidence: list[str],
    finding: str,
    severity: str,
    mandatory_change: list[str],
    passed: bool,
    rationale: str,
) -> dict[str, Any]:
    return {
        "review_id": review_id,
        "question": question,
        "evidence": evidence,
        "finding": finding,
        "severity": severity,
        "mandatory_change": mandatory_change,
        "pass": passed,
        "rationale": rationale,
    }


def _mandatory(
    change_id: str,
    title: str,
    text_requirement: str,
    acceptance: list[str],
    tests: list[str],
) -> dict[str, Any]:
    return {
        "id": change_id,
        "title": title,
        "text_requirement": text_requirement,
        "acceptance": acceptance,
        "tests": tests,
        "blocks_adoption": True,
    }


def _mandatory_changes() -> list[dict[str, Any]]:
    return [
        _mandatory(
            "MC-01",
            "Promote row category to a lifecycle availability event",
            "Replace the close_time<open_time row-only category with a versioned lifecycle event that freezes the affected interval and complete affected-row set. It must distinguish cessation-day partial rows, post-cessation normal-duration placeholders, malformed placeholders and legitimate zero-volume rows. Every newly observed post-cessation row must fail closed until its evidence is bound.",
            [
                "The KLAY event binds the 2024-10-28 partial day and both 2024-10-29/30 post-cessation rows by raw hash.",
                "No post-cessation row can contribute to complete-history, 90-day ranking or 365-day eligibility counts.",
                "A new post-cessation row or changed affected-row hash blocks qualification.",
            ],
            [
                "normal-duration zero-volume placeholder is excluded",
                "close-before-open placeholder is excluded",
                "multiple/new post-cessation placeholders fail closed",
            ],
        ),
        _mandatory(
            "MC-02",
            "Freeze exact availability and expected-grid semantics",
            "Define symbol_availability_epochs with availability_start_inclusive and availability_end_exclusive. Apply epochs before expected-grid generation. Define legal partial, crossing and post-boundary behavior for 5m, 1h and 1d; incomplete child sets cannot form complete parents. Separate raw-row quarantine, lifecycle-event quarantine and research-panel availability masks.",
            [
                "open>=end_exclusive is not expected and never reported as a gap",
                "a bar crossing end_exclusive is blocked or partial by explicit timeframe rule",
                "a lifecycle partial UTC day is excluded from complete-day windows while preserved as raw evidence",
                "pre-boundary gaps continue to block",
            ],
            [
                "UTC-day, 5m, 1h and off-grid boundary fixtures",
                "12 complete 5m children required for a complete 1h bar",
                "partial lifecycle day excluded from 90/365 windows",
                "post-boundary absence does not become a gap",
            ],
        ),
        _mandatory(
            "MC-03",
            "Add point-in-time lifecycle knowledge semantics",
            "Bind known_at/publication_time separately from effective_at, archive publication/revision time and resolution approval time. Month-start membership remains immutable; mid-month events alter only active availability. Retrospective evidence unavailable at the historical time must be disclosed and cannot be used as if known earlier.",
            [
                "machine event contains known_at and effective_at",
                "no event influences state before known_at",
                "month membership and rank are unchanged by later evidence",
                "retrospective reconstruction status is explicit",
            ],
            [
                "publication after effective time",
                "late archive revision",
                "replacement performance cannot rewrite old membership",
            ],
        ),
        _mandatory(
            "MC-04",
            "Separate membership from active universe",
            "Preserve monthly point-in-time membership and derive timestamped active availability separately. Expose distinct membership_count and active_count plus active_complete, active_partial, lifecycle_terminated, data_quarantined and unresolved_blocked states. A terminated member is not missing data, zero return, cash or a stale-price position.",
            [
                "membership does not change mid-month",
                "active count decreases after cessation without adding rank 16",
                "status and count fields are separate and machine checked",
            ],
            [
                "member and non-member event fixtures",
                "active count decline without replacement",
                "terminated state cannot be coerced to missing/zero/cash/stale",
            ],
        ),
        _mandatory(
            "MC-05",
            "Keep execution and returns outside the data policy",
            "State that availability does not define exit, liquidation, settlement, conversion, stale fill, cross-cessation return, -100%, zero return or cash treatment. U-04 may design a hypothesis, but fixed-rule or backtest work is blocked by a separately reviewed delisting/execution policy whenever a lifecycle event can intersect a position.",
            [
                "ADR contains an explicit non-target section",
                "authorization matrix keeps returns and execution false",
                "downstream Gate is machine represented",
            ],
            [
                "no stale-price forward-fill",
                "no cross-boundary return",
                "no implicit -100%, zero or cash settlement",
            ],
        ),
        _mandatory(
            "MC-06",
            "Make successor metadata non-authoritative",
            "Rename replacement symbol to announced_successor_symbol and define it as provenance only. It grants no continuity, conversion, equivalence, listing age, volume, rank or complete-history inheritance. Any KLAY/KAIA splice requires a separate ADR; the successor must independently satisfy 365/90-day point-in-time rules.",
            [
                "field name and schema state provenance_only",
                "successor cannot fill the old symbol gap or inherit metrics",
                "economic continuity is separately unauthorized",
            ],
            [
                "announced successor without automatic replacement",
                "successor receives independent age/rank/volume history",
            ],
        ),
        _mandatory(
            "MC-07",
            "Split lifecycle policy from event registry",
            "Create separate hash-bound lifecycle policy and lifecycle event resolution registries. Event entries must bind exchange, market, symbol/pair, epoch, cessation/effective/known times, last valid time, expected-grid end, official evidence and archive/raw/intraday/scope hashes, policy version, adjudication hash, announced successor metadata and authorization status.",
            [
                "new/changed events, hashes, cessation times or post-event rows fail closed",
                "overlapping/conflicting entries fail closed",
                "implementation contains no symbol/date branch",
            ],
            [
                "unregistered event",
                "checksum/evidence/registry hash changes",
                "cessation-time change",
                "new post-cessation row",
                "no symbol/date special case",
            ],
        ),
        _mandatory(
            "MC-08",
            "Support multiple availability epochs and ticker identity",
            "Represent relisting, reactivation, migration and ticker reuse as distinct symbol_availability_epochs with identity/version and evidence. A new epoch cannot inherit the prior epoch's 365-day history, volume, rank or price continuity.",
            [
                "multiple non-overlapping epochs are representable",
                "same ticker/different asset identity remains separate",
                "epoch overlap blocks qualification",
            ],
            [
                "same ticker relisting",
                "ticker reused for a different economic asset",
                "overlapping epochs",
            ],
        ),
        _mandatory(
            "MC-09",
            "Raise lifecycle evidence sufficiency above archive absence",
            "Limit this policy to proven permanent cessation/migration events. Archive absence alone is not lifecycle proof. Require validated official lifecycle evidence plus integrity-checked interval evidence, and distinguish temporary suspension, maintenance, delisting and migration. Freeze the similar-scope scan definition and hash.",
            [
                "permanent and temporary states have different outcomes",
                "missing intraday data without announcement remains a data blocker",
                "continued intraday trading contradicts cessation and blocks",
                "scope and scan hash are machine bound",
            ],
            [
                "temporary suspension",
                "maintenance",
                "archive absence without announcement",
                "announcement while trading continues",
                "scope hash change",
            ],
        ),
        _mandatory(
            "MC-10",
            "Define V4 machine authority and disclosures",
            "Require lifecycle_policy_manifest, lifecycle_resolution_registry, symbol_availability_manifest, active_universe_manifest, complete_day_mask, expected_grid_manifest, raw_row_quarantine_manifest, qualification_summary and V3/V4 diff. Use canonical serialization and hash bindings; Markdown is never input. V4 becomes active only after cold/warm/worker equality, truthful requalification PASS and later U-03F independent recomputation.",
            [
                "summary discloses lifecycle events, terminated symbol-months, partial days, quarantined post-cessation rows, membership/active counts and unresolved lifecycle rows",
                "synthetic fills and replacement members are zero",
                "V3 remains authority until a V4 pass",
            ],
            [
                "cold/warm/worker machine hash equality",
                "Markdown mutation cannot affect qualification",
                "V4 blocked evidence cannot become active authority",
            ],
        ),
        _mandatory(
            "MC-11",
            "Freeze lifecycle fault-injection coverage",
            "Adoption must include the complete fault-injection matrix listed in this independent review. Tests must exercise boundary alignment, partial and placeholder rows, source disagreement, evidence timing, event types, epochs, membership/active counts, complete-day masking and non-execution semantics.",
            [
                "every named fault-injection case maps to an automated test ID",
                "unknown and contradictory cases fail closed",
                "tests do not run qualification or mutate production evidence during policy adoption review",
            ],
            FAULT_INJECTION_TESTS,
        ),
    ]


def _questions() -> list[dict[str, Any]]:
    return [
        _question(
            "Q01",
            "Does the Draft cover the lifecycle event rather than only one malformed row?",
            [
                "ADR B1 requires close_time < open_time and therefore selects only the 2024-10-30 malformed row.",
                "KLAY monthly archive previous_raw_fields/hash fde7b404... records 2024-10-29 as flat, zero volume/trades and normal daily duration after cessation.",
                "The 2024-10-28 row ends at 2024-10-28T02:59:59.999Z and is a genuine partial lifecycle day.",
            ],
            "The row category is over-fitted. A normal-duration post-cessation placeholder can enter complete-history, 90-day ranking and 365-day eligibility calculations even if the 2024-10-30 row is quarantined.",
            "high",
            ["MC-01"],
            False,
            "The policy must bind the availability event and all affected rows, not one blocker signature.",
        ),
        _question(
            "Q02",
            "Are availability intervals, timeframe boundaries and expected-grid order uniquely defined?",
            ["ADR B2 says stop expecting bars after cessation but defines no inclusive/exclusive epoch, partial-day mask, cross-boundary rule or grid construction order."],
            "The Draft permits multiple incompatible 5m/1h/1d implementations and can misclassify post-cessation absence as gaps or partial days as complete days.",
            "high",
            ["MC-02"],
            False,
            "Exact availability_start_inclusive/end_exclusive and pre-grid application are required for deterministic qualification.",
        ),
        _question(
            "Q03",
            "Does point-in-time reconstruction separate when evidence was known from when cessation became effective?",
            ["KLAY evidence records publication 2024-10-16 and effective cessation 2024-10-28, but B2 has no known_at/effective_at or retrospective reconstruction semantics."],
            "The Draft does not prevent future information from altering historical availability before it was public or rewriting month-start membership.",
            "high",
            ["MC-03"],
            False,
            "Knowledge time and market-effective time are distinct facts and must be independently bound.",
        ),
        _question(
            "Q04",
            "Are monthly membership and timestamped active universe separate machine concepts?",
            ["ADR B2 preserves membership and marks termination but defines neither separate counts nor a complete status vocabulary."],
            "Downstream research could treat lifecycle termination as missing data, zero return, cash or stale-price continuity.",
            "high",
            ["MC-04"],
            False,
            "Point-in-time membership is fixed monthly while active availability can change intramonth; both must be explicit.",
        ),
        _question(
            "Q05",
            "Does the data policy explicitly avoid defining prices, returns or position settlement?",
            ["ADR B2 describes availability only, but it does not explicitly prohibit exit price, token conversion, stale fill or cross-cessation return semantics."],
            "A future backtest could silently infer a favorable or arbitrary settlement from a data-qualification boundary.",
            "high",
            ["MC-05"],
            False,
            "Lifecycle data admissibility and held-position execution are separate policies and review Gates.",
        ),
        _question(
            "Q06",
            "Is optional replacement symbol metadata unambiguously non-authoritative?",
            ["B2 calls the field optional replacement symbol while separately denying automatic KLAY/KAIA splice."],
            "The current name can be misread as replacement authority even though the prose denies continuity.",
            "medium",
            ["MC-06"],
            False,
            "Rename it announced_successor_symbol and prohibit inheritance or conversion semantics in schema and tests.",
        ),
        _question(
            "Q07",
            "Are lifecycle policy and event resolution records separate and fail closed?",
            ["B3 requests a versioned lifecycle resolution registry but does not define separate policy/event schemas, required fields or change detection."],
            "Unknown events, checksum changes, new rows and conflicting registry entries are not uniquely governed.",
            "high",
            ["MC-07"],
            False,
            "Generic policy and evidence-bound event instances require separate identities and failure modes.",
        ),
        _question(
            "Q08",
            "Can the model represent relisting, reactivation and ticker reuse without history splice?",
            ["B2 emits one symbol_availability_boundary and has no epoch identity or later start boundary."],
            "A single terminal boundary can permanently kill a ticker or incorrectly join a new economic asset to old history.",
            "high",
            ["MC-08"],
            False,
            "Availability must be a versioned set of non-overlapping epochs, each with independent identity and eligibility history.",
        ),
        _question(
            "Q09",
            "Is lifecycle evidence sufficient and generalized beyond the KLAY signature?",
            [
                "B1 combines KLAY-specific flat/zero/close-boundary features with announcement evidence.",
                "The scope scan found partial-duration ORN/SCR rows, proving non-full duration alone is not a universal cessation class.",
                "Missing intraday archives can also be a public-archive gap.",
            ],
            "The Draft does not distinguish permanent cessation, temporary suspension, maintenance, migration and archive absence, nor freeze scope semantics.",
            "high",
            ["MC-09"],
            False,
            "Archive absence is not lifecycle proof; validated lifecycle evidence and interval integrity must agree.",
        ),
        _question(
            "Q10",
            "Are future V4 machine artifacts, authority activation and counters complete?",
            ["B3 mentions contract/registry binding and three rebuilds but omits availability, active-universe, complete-day and expected-grid manifests and required disclosures."],
            "A V4 run could pass without proving active counts, partial-day exclusion, post-cessation quarantine or zero synthetic/replacement artifacts.",
            "high",
            ["MC-10"],
            False,
            "Machine evidence, not Markdown, must close every policy consequence before V4 authority can activate.",
        ),
        _question(
            "Q11",
            "Does the Draft freeze adequate boundary and fault-injection tests before adoption?",
            ["PR #81 CI has 88 passing static/guard tests, but the Draft tests verify markers and zero authority rather than the full lifecycle state machine."],
            "The policy is not adoption-ready without deterministic tests for boundaries, placeholders, source contradictions, event types, epochs and non-execution behavior.",
            "high",
            ["MC-11"],
            False,
            "Passing Draft CI proves scope safety, not complete lifecycle semantics.",
        ),
        _question(
            "Q12",
            "Does the current Draft safely avoid adoption, implementation and downstream authorization?",
            ["ADR B6 keeps every authorization false; PR #81 changes only Draft governance/checker/tests/CI files; all 88 checks passed."],
            "The Draft is safely proposed-only and does not mutate runtime authority.",
            "informational",
            [],
            True,
            "The review can be merged independently while PR #81 remains Draft and unchanged.",
        ),
    ]


def build_review_document(*, generated_utc: str | None = None) -> dict[str, Any]:
    generated_utc = generated_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    questions = _questions()
    severity_counts = {level: 0 for level in ("critical", "high", "medium", "low", "informational")}
    for item in questions:
        severity_counts[item["severity"]] += 1
    document = {
        "schema_version": 1,
        "manifest_type": "adr0014_independent_policy_review",
        "generated_utc": generated_utc,
        "reviewed_artifacts": dict(EXPECTED_ARTIFACTS),
        "content": {
            "verdict": "approve_with_required_changes",
            "questions": questions,
            "findings": [
                {
                    "review_id": item["review_id"],
                    "severity": item["severity"],
                    "finding": item["finding"],
                    "resolved": item["pass"],
                }
                for item in questions
            ],
            "severity_counts": severity_counts,
            "mandatory_changes": _mandatory_changes(),
            "fault_injection_tests": FAULT_INJECTION_TESTS,
            "authorization_matrix": dict(EXPECTED_AUTHORIZATIONS),
            "stop_condition": "PR #81 remains Proposed draft and unchanged. No adoption, implementation, registry mutation, requalification or downstream research is authorized by this review.",
        },
    }
    document["content_hash"] = sha256(content_identity(document))
    return document


def verify_review_document(document: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if document.get("schema_version") != 1 or document.get("manifest_type") != "adr0014_independent_policy_review":
        failures.append("review identity mismatch")
    if document.get("content_hash") != sha256(content_identity(document)):
        failures.append("content hash mismatch")
    reviewed = document.get("reviewed_artifacts", {})
    for key, expected in EXPECTED_ARTIFACTS.items():
        if reviewed.get(key) != expected:
            failures.append(f"reviewed artifact binding changed: {key}")
    content = document.get("content", {})
    questions = content.get("questions", [])
    if len(questions) != 12 or {item.get("review_id") for item in questions} != EXPECTED_REVIEW_QUESTION_IDS:
        failures.append("review question set mismatch")
    required_fields = {"review_id", "question", "evidence", "finding", "severity", "mandatory_change", "pass", "rationale"}
    if any(set(item) != required_fields for item in questions):
        failures.append("review question schema mismatch")
    mandatory = content.get("mandatory_changes", [])
    if len(mandatory) != 11 or {item.get("id") for item in mandatory} != EXPECTED_MANDATORY_CHANGE_IDS:
        failures.append("mandatory change set mismatch")
    mandatory_fields = {"id", "title", "text_requirement", "acceptance", "tests", "blocks_adoption"}
    if any(set(item) != mandatory_fields or not item.get("acceptance") or not item.get("tests") for item in mandatory):
        failures.append("mandatory change schema mismatch")
    if any(item.get("blocks_adoption") is not True for item in mandatory):
        failures.append("mandatory change no longer blocks adoption")
    if content.get("authorization_matrix") != EXPECTED_AUTHORIZATIONS:
        failures.append("authorization matrix changed")
    if content.get("fault_injection_tests") != FAULT_INJECTION_TESTS:
        failures.append("fault injection matrix changed")
    derived_counts = {level: 0 for level in ("critical", "high", "medium", "low", "informational")}
    for item in questions:
        if item.get("severity") in derived_counts:
            derived_counts[item["severity"]] += 1
        else:
            failures.append("unknown finding severity")
    if content.get("severity_counts") != derived_counts:
        failures.append("severity counts mismatch")
    verdict = content.get("verdict")
    if verdict not in {"reject", "approve_with_required_changes", "approve"}:
        failures.append("invalid verdict")
    if verdict == "approve" and (derived_counts["critical"] or derived_counts["high"]):
        failures.append("verdict is incompatible with unresolved high findings")
    if verdict == "approve_with_required_changes" and not mandatory:
        failures.append("conditional approval has no mandatory changes")
    return failures


def verify_git_target(ref: str) -> list[str]:
    """Verify that the locally fetched review target is the exact frozen PR head."""
    failures: list[str] = []

    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=ROOT)

    try:
        head = git("rev-parse", ref).decode().strip()
    except subprocess.CalledProcessError:
        return [f"review target ref is unavailable: {ref}"]
    if head != EXPECTED_ARTIFACTS["reviewed_pr_head"]:
        failures.append(f"review target head changed: {head}")
        return failures
    base = EXPECTED_ARTIFACTS["reviewed_base_sha"]
    adr_path = EXPECTED_ARTIFACTS["adr_path"]
    blob = git("rev-parse", f"{ref}:{adr_path}").decode().strip()
    if blob != EXPECTED_ARTIFACTS["adr_blob_sha"]:
        failures.append("review target ADR blob changed")
    adr_bytes = git("show", f"{ref}:{adr_path}")
    if hashlib.sha256(adr_bytes).hexdigest() != EXPECTED_ARTIFACTS["adr_content_sha256"]:
        failures.append("review target ADR content hash changed")
    changed_files = sorted(
        item for item in git("diff", "--name-only", f"{base}...{ref}").decode().splitlines() if item
    )
    if changed_files != EXPECTED_CHANGED_FILES:
        failures.append("review target changed-file list changed")
    if sha256(changed_files) != EXPECTED_ARTIFACTS["changed_file_list_sha256"]:
        failures.append("review target changed-file-list hash changed")
    return failures


def render_report(document: dict[str, Any]) -> str:
    content = document["content"]
    artifacts = document["reviewed_artifacts"]
    lines = [
        "# ADR-0014 Independent Policy Review",
        "",
        f"- Verdict: `{content['verdict']}`",
        f"- Reviewed PR: `#{artifacts['reviewed_pr_number']}`",
        f"- Reviewed PR head: `{artifacts['reviewed_pr_head']}`",
        f"- Reviewed base: `{artifacts['reviewed_base_branch']}@{artifacts['reviewed_base_sha']}`",
        f"- ADR blob / content SHA256: `{artifacts['adr_blob_sha']}` / `{artifacts['adr_content_sha256']}`",
        f"- PR changed-file-list SHA256: `{artifacts['changed_file_list_sha256']}`",
        f"- KLAY evidence hash: `{artifacts['klay_adjudication_evidence_hash']}`",
        f"- Generated UTC: `{document['generated_utc']}` (excluded from content identity)",
        f"- Review content hash: `{document['content_hash']}`",
        "",
        "## Executive Decision",
        "",
        "The proposed Draft is safe as a review-only artifact, but it is not adoption-ready. Its row category is tied to the malformed 2024-10-30 record while the same official monthly archive contains a normal-duration, flat, zero-volume 2024-10-29 placeholder after the 2024-10-28T03:00:00Z cessation. The real policy object must therefore be a versioned availability lifecycle event, not a single invalid row.",
        "",
        "There are no critical findings, but ten unresolved high findings prevent `approve`. The verdict is `approve_with_required_changes`; all eleven machine-verifiable changes below block adoption. PR #81 must remain Draft and unchanged.",
        "",
        "## Frozen Source Observation",
        "",
        "- Last real intraday market close: `2024-10-28T02:59:59.999Z`.",
        "- `2024-10-28`: real cessation-day partial row; it is not a complete UTC day.",
        "- `2024-10-29`: flat zero-volume/trade row with normal daily duration, but entirely after cessation.",
        "- `2024-10-30`: flat zero-volume/trade row whose close precedes open and equals cessation minus 1 ms.",
        "- Quarantining only 2024-10-30 would leave a false complete day in ranking and history evidence.",
        "",
        "## Severity Summary",
        "",
        "| Severity | Count |",
        "| --- | ---: |",
    ]
    for severity in ("critical", "high", "medium", "low", "informational"):
        lines.append(f"| {severity} | {content['severity_counts'][severity]} |")
    lines.extend([
        "",
        "## Review Questions",
        "",
        "| ID | Pass | Severity | Question | Finding | Mandatory change |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for item in content["questions"]:
        changes = ", ".join(item["mandatory_change"]) or "none"
        lines.append(
            f"| {item['review_id']} | {'yes' if item['pass'] else 'no'} | `{item['severity']}` | "
            f"{item['question']} | {item['finding']} | {changes} |"
        )
        lines.append("")
        lines.append(f"Evidence for {item['review_id']}:")
        for evidence in item["evidence"]:
            lines.append(f"- {evidence}")
        lines.append(f"- Rationale: {item['rationale']}")
        lines.append("")
    lines.extend(["## Mandatory Changes Before Adoption", ""])
    for item in content["mandatory_changes"]:
        lines.extend([
            f"### {item['id']} {item['title']}",
            "",
            item["text_requirement"],
            "",
            "Acceptance:",
        ])
        lines.extend(f"- {entry}" for entry in item["acceptance"])
        lines.append("")
        lines.append("Required tests:")
        lines.extend(f"- {entry}" for entry in item["tests"])
        lines.extend(["", "Blocks adoption: `yes`", ""])
    lines.extend([
        "## Required Boundary Semantics",
        "",
        "- Every availability epoch must expose `availability_start_inclusive` and `availability_end_exclusive`.",
        "- The availability mask is applied before expected-grid construction.",
        "- A lifecycle partial day can retain raw OHLCV evidence but cannot count toward 90/365 complete-day windows.",
        "- Monthly membership remains fixed; timestamped active membership and counts change at the lifecycle boundary.",
        "- Archive absence is not lifecycle proof. Validated official lifecycle evidence and integrity-checked interval evidence must agree.",
        "- `announced_successor_symbol` is provenance only and grants no price, age, volume, rank, conversion or economic-continuity authority.",
        "",
        "## Non-Targets And Downstream Gate",
        "",
        "This data policy must not define exit price, liquidation, settlement, conversion, stale fill, cross-cessation return, -100%, zero-return or cash treatment. U-04 may later design a hypothesis, but fixed-rule or backtest work must remain blocked until a separate delisting/execution policy review covers positions intersecting lifecycle events.",
        "",
        "## Fault-Injection Matrix",
        "",
    ])
    lines.extend(f"- {item}" for item in content["fault_injection_tests"])
    auth_labels = {
        "adr0014_adopted": "ADR-0014 adopted",
        "pr81_ready": "PR #81 Ready",
        "pr81_merge": "PR #81 merge",
        "contract_mutation": "Contract mutation",
        "registry_mutation": "Registry mutation",
        "v4_implementation": "V4 implementation",
        "v3_or_v4_requalification": "V3/V4 requalification",
        "cold_warm_or_worker_build": "Cold/warm/worker build",
        "u03f": "U-03F",
        "u04": "U-04",
        "strategy_design_or_code": "Strategy design/code",
        "event_scan": "Event scan",
        "returns_or_backtesting": "Returns/backtesting",
        "oos_access": "OOS access",
        "api_or_trading": "API/trading",
        "execution_live": "execution/live",
        "m2": "M2",
    }
    lines.extend(["", "## Authorization Matrix", ""])
    for key in EXPECTED_AUTHORIZATIONS:
        value = content["authorization_matrix"][key]
        lines.append(f"- {auth_labels[key]} authorized: {'yes' if value else 'no'}")
    lines.extend(["", f"Stop condition: {content['stop_condition']}", ""])
    return "\n".join(lines)


def canonical_pretty(document: dict[str, Any]) -> str:
    return json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify-target-ref")
    args = parser.parse_args()
    if args.write:
        document = build_review_document()
        EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE_PATH.write_text(canonical_pretty(document), encoding="utf-8")
        REPORT_PATH.write_text(render_report(document), encoding="utf-8")
        print(f"ADR0014_INDEPENDENT_REVIEW_WRITE {document['content_hash']}")
        return 0
    document = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    failures = verify_review_document(document)
    if args.verify_target_ref:
        failures.extend(verify_git_target(args.verify_target_ref))
    if EVIDENCE_PATH.read_text(encoding="utf-8") != canonical_pretty(document):
        failures.append("machine review is not canonical pretty JSON")
    if REPORT_PATH.read_text(encoding="utf-8") != render_report(document):
        failures.append("Markdown report is not the exact JSON render")
    if failures:
        print("ADR0014_INDEPENDENT_REVIEW_CHECK FAIL")
        for failure in sorted(set(failures)):
            print(f"- {failure}")
        return 1
    print(f"ADR0014_INDEPENDENT_REVIEW_CHECK PASS {document['content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
