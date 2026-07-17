#!/usr/bin/env python3
"""Verify conditional ADR-0015 adoption without widening reviewed semantics."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ADOPTED_ADR_PATH = ROOT / "docs/decisions/ADR-0015-synchronized-official-invalid-interval-quarantine-policy.md"
MODEL_PATH = ROOT / "docs/decisions/proposals/adr0015_invalid_interval_policy_model.json"
MANIFEST_PATH = ROOT / "reports/expert/evidence/adr0015_adoption_manifest.json"

REVIEWED_DRAFT_HEAD = "03d2b8736abab277e60db1153ba73f0899d7696f"
REVIEWED_DRAFT_BASE = "6df4aa3aa355f986e5533a51e223d69e3bf16e84"
DRAFT_MERGE_SHA = "e1783090dfb0a4560475b97a021ef1e77aebc399"
REVIEW_HEAD = "f3cf2131798f8bf3bd319b21480dca196517f3fe"
REVIEW_MERGE_SHA = "1573abf2bef7d02df6c3b0624ee25cd3557ff2c6"
EXPECTED_SEMANTIC_BODY_HASH = "c3d5f605ec26161f1bedc6961ac6f326d00582f9c3dcaa9de68c226961a34149"
MODEL_CONTENT_HASH = "7acb69f72136742eb2b5f4c66e4fa09611846e74625846a690d932b9835fe78c"

EXPECTED_REVIEW_BINDINGS = {
    "reviewed_draft_pr": 105,
    "reviewed_draft_base_sha": REVIEWED_DRAFT_BASE,
    "reviewed_draft_head_sha": REVIEWED_DRAFT_HEAD,
    "draft_merge_sha": DRAFT_MERGE_SHA,
    "reviewed_adr_file_sha256": "9ce9eade1f622824562a74ce5750da400f4c298145fb92c2a89023ff527ce19a",
    "reviewed_semantic_body_hash": EXPECTED_SEMANTIC_BODY_HASH,
    "policy_model_file_sha256": "f945d5c61553a4571e9cbda7c77bff0c974a460cd25b7ad92d6382c8d4e92a7e",
    "policy_model_content_hash": MODEL_CONTENT_HASH,
    "review_pr": 107,
    "review_head_sha": REVIEW_HEAD,
    "review_merge_sha": REVIEW_MERGE_SHA,
    "review_evidence_file_sha256": "01322bff7ed0d35829e85c2e2eb6c8783a916a9107ba5d3d0a27a586fa9fe24f",
    "review_report_file_sha256": "caeca0eae20afb761ed516162c9d5128c7403c55ca5b3cb4da9a105c54422cd9",
    "review_content_hash": "893d056ec07ebc0697521a96a1533cb43265ebc2fa9484862fcdf39d8c5285a3",
    "review_verdict": "approve",
    "review_critical_findings": 0,
    "review_high_findings": 0,
    "protocol_content_hash": "9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190",
    "diagnostic_content_hash": "ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677",
    "diagnostic_run_content_hash": "df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33",
    "source_freeze_content_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
    "v2_gap_policy_contract_hash": "051894e89b713f541caa601efab51be22f83461a4e624e1d51d7f576ed8cda51",
}

EXPECTED_AUTHORIZATIONS = {
    "adr0015_adopted": True,
    "generic_policy_implementation": True,
    "fixture_validation": True,
    "fault_injection": True,
    "exact_head_implementation_review": True,
    "fixed_range_public_requalification": False,
    "new_independent_audit_protocol": False,
    "new_independent_audit": False,
    "u04": False,
    "hypothesis_or_strategy": False,
    "event_scan_signals_or_returns": False,
    "backtesting_or_oos": False,
    "api_or_trading": False,
    "execution_live": False,
    "m2": False,
}

DEPENDENCY_ORDER = [
    "A_conditional_adoption",
    "B_generic_policy_implementation",
    "C_exact_head_implementation_review",
    "D_fixed_range_public_requalification",
    "E_new_independent_audit_protocol",
    "F_new_independent_audit",
    "G_governance_closeout",
    "H_separate_u04_authorization_consideration",
]


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def model_content_hash(model: dict[str, Any]) -> str:
    value = copy.deepcopy(model)
    value.pop("generated_utc", None)
    value.pop("content_hash", None)
    return canonical_hash(value)


def extract_semantic_body(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    headings = ("## Proposed Decision", "## Decision")
    starts = [normalized.find(heading) for heading in headings]
    valid_starts = [start for start in starts if start >= 0]
    if not valid_starts:
        raise ValueError("ADR-0015 decision heading missing")
    heading_start = min(valid_starts)
    start = normalized.index("\n", heading_start) + 1
    end_markers = ("## Independent Policy Review Gate", "## Independent Policy Review Result")
    ends = [normalized.find(marker, start) for marker in end_markers]
    valid_ends = [end for end in ends if end >= 0]
    if not valid_ends:
        raise ValueError("ADR-0015 independent-review heading missing")
    body = normalized[start:min(valid_ends)]
    return "\n".join(line.rstrip() for line in body.split("\n")).rstrip() + "\n"


def content_identity(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": document["schema_version"],
        "manifest_type": document["manifest_type"],
        "review_bindings": document["review_bindings"],
        "content": document["content"],
    }


def build_adoption_document(generated_utc: str | None = None) -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema_version": 1,
        "manifest_type": "adr0015_conditional_adoption",
        "review_bindings": dict(EXPECTED_REVIEW_BINDINGS),
        "content": {
            "adoption_status": "accepted_for_generic_policy_implementation_and_exact_head_implementation_review_only",
            "adopted_semantic_body_hash": EXPECTED_SEMANTIC_BODY_HASH,
            "authorization_matrix": dict(EXPECTED_AUTHORIZATIONS),
            "dependency_order": list(DEPENDENCY_ORDER),
            "current_stage_effects": {
                "production_pipeline_modified": False,
                "public_data_run_executed": False,
                "requalification_executed": False,
                "independent_audit_executed": False,
            },
            "stop_condition": "Any target, evidence, semantic, authorization or dependency drift fails closed; no requalification, audit, U-04, research, OOS, trading or M2 authority is created.",
        },
    }
    document["content_hash"] = canonical_hash(content_identity(document))
    document["generated_utc"] = generated_utc or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return document


def verify_adoption_document(document: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if document.get("schema_version") != 1 or document.get("manifest_type") != "adr0015_conditional_adoption":
        failures.append("adoption schema or manifest type changed")
    bindings = document.get("review_bindings", {})
    for key, value in EXPECTED_REVIEW_BINDINGS.items():
        if bindings.get(key) != value:
            failures.append(f"review binding changed: {key}")
    content = document.get("content", {})
    if content.get("adoption_status") != "accepted_for_generic_policy_implementation_and_exact_head_implementation_review_only":
        failures.append("adoption status changed")
    if content.get("adopted_semantic_body_hash") != EXPECTED_SEMANTIC_BODY_HASH:
        failures.append("adopted semantic body hash changed")
    if content.get("authorization_matrix") != EXPECTED_AUTHORIZATIONS:
        failures.append("authorization matrix changed")
    if content.get("dependency_order") != DEPENDENCY_ORDER:
        failures.append("dependency order changed")
    if content.get("current_stage_effects") != {
        "production_pipeline_modified": False,
        "public_data_run_executed": False,
        "requalification_executed": False,
        "independent_audit_executed": False,
    }:
        failures.append("adoption stage effects changed")
    try:
        expected_hash = canonical_hash(content_identity(document))
    except KeyError:
        failures.append("adoption content identity is incomplete")
    else:
        if document.get("content_hash") != expected_hash:
            failures.append("adoption content hash mismatch")
    return sorted(set(failures))


def _git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def _show(commit: str, path: str) -> bytes:
    return _git("show", f"{commit}:{path}")


def _verify_frozen_sources() -> list[str]:
    failures: list[str] = []
    try:
        draft_adr = _show(REVIEWED_DRAFT_HEAD, "docs/decisions/ADR-0015-synchronized-official-invalid-interval-quarantine-policy.md")
        draft_model = _show(REVIEWED_DRAFT_HEAD, "docs/decisions/proposals/adr0015_invalid_interval_policy_model.json")
        review_json = _show(REVIEW_HEAD, "reports/expert/evidence/adr0015_independent_review.json")
        review_report = _show(REVIEW_HEAD, "reports/expert/ADR_0015_INDEPENDENT_REVIEW.md")
    except subprocess.CalledProcessError:
        return ["reviewed ADR-0015 source or review evidence is unavailable"]
    hashes = {
        "reviewed_adr_file_sha256": hashlib.sha256(draft_adr).hexdigest(),
        "policy_model_file_sha256": hashlib.sha256(draft_model).hexdigest(),
        "review_evidence_file_sha256": hashlib.sha256(review_json).hexdigest(),
        "review_report_file_sha256": hashlib.sha256(review_report).hexdigest(),
    }
    for key, actual in hashes.items():
        if actual != EXPECTED_REVIEW_BINDINGS[key]:
            failures.append(f"frozen source hash changed: {key}")
    try:
        semantic_hash = canonical_hash(extract_semantic_body(draft_adr.decode("utf-8")))
        model = json.loads(draft_model)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"reviewed source is invalid: {exc}")
    else:
        if semantic_hash != EXPECTED_SEMANTIC_BODY_HASH:
            failures.append("reviewed ADR semantic body changed")
        if model_content_hash(model) != MODEL_CONTENT_HASH or model.get("content_hash") != MODEL_CONTENT_HASH:
            failures.append("reviewed policy model content changed")
    try:
        review_document = json.loads(review_json)
    except json.JSONDecodeError as exc:
        failures.append(f"review evidence JSON invalid: {exc}")
    else:
        if review_document.get("review_content_sha256") != EXPECTED_REVIEW_BINDINGS["review_content_hash"]:
            failures.append("review content hash changed")
        if review_document.get("verdict") != "approve":
            failures.append("review verdict changed")
        findings = review_document.get("remaining_findings", {})
        if findings.get("critical") or findings.get("high"):
            failures.append("review no longer has zero critical/high findings")
    try:
        if _git("rev-parse", f"{REVIEW_HEAD}^{{tree}}").strip() != _git("rev-parse", f"{REVIEW_MERGE_SHA}^{{tree}}").strip():
            failures.append("review merge tree differs from exact review head")
    except subprocess.CalledProcessError:
        failures.append("review head or merge commit is unavailable")
    return failures


def verify_repository(*, check_stage_scope: bool = True) -> list[str]:
    failures: list[str] = []
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"adoption manifest load failed: {exc}"]
    failures.extend(verify_adoption_document(manifest))
    failures.extend(_verify_frozen_sources())

    try:
        adr = ADOPTED_ADR_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        failures.append(f"adopted ADR load failed: {exc}")
    else:
        required_markers = (
            "- Status: Accepted for generic policy implementation and exact-head implementation review only",
            "- Adoption basis: PR #107 exact-head independent review",
            "## Adoption Scope",
            "## Adoption Authorization Matrix",
            "## Adoption Dependency Chain",
        )
        for marker in required_markers:
            if marker not in adr:
                failures.append(f"adopted ADR marker missing: {marker}")
        try:
            semantic_hash = canonical_hash(extract_semantic_body(adr))
        except ValueError as exc:
            failures.append(f"adopted ADR semantic body invalid: {exc}")
        else:
            if semantic_hash != EXPECTED_SEMANTIC_BODY_HASH:
                failures.append("adopted ADR semantic body differs from reviewed Draft")

    try:
        raw_model = MODEL_PATH.read_bytes()
        current_model = json.loads(raw_model)
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"policy model load failed: {exc}")
    else:
        if hashlib.sha256(raw_model).hexdigest() != EXPECTED_REVIEW_BINDINGS["policy_model_file_sha256"]:
            failures.append("docs-only policy model bytes changed")
        if model_content_hash(current_model) != MODEL_CONTENT_HASH or current_model.get("content_hash") != MODEL_CONTENT_HASH:
            failures.append("docs-only policy model semantics changed")
        if any(current_model.get("authorization_matrix", {}).values()):
            failures.append("frozen Draft model authorization matrix changed")

    if check_stage_scope:
        try:
            changed = _git("diff", "--name-only", "origin/main...").decode().splitlines()
        except subprocess.CalledProcessError:
            changed = _git("diff", "--name-only").decode().splitlines()
        forbidden = [
            path for path in changed
            if path.startswith(("src/", "config/", "reports/m0/evidence/", "storage/"))
            or "requalification_run_manifest" in path
        ]
        if forbidden:
            failures.append(f"adoption stage contains forbidden implementation/run artifacts: {forbidden}")
    return sorted(set(failures))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--evidence-only", action="store_true")
    args = parser.parse_args()
    if args.write:
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text(json.dumps(build_adoption_document(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    failures = verify_repository(check_stage_scope=not args.evidence_only)
    if failures:
        print("ADR0015_ADOPTION_CHECK FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    print("ADR0015_ADOPTION_CHECK PASS")
    print(f"reviewed_draft_head={REVIEWED_DRAFT_HEAD}")
    print(f"review_head={REVIEW_HEAD}")
    print(f"semantic_body_hash={EXPECTED_SEMANTIC_BODY_HASH}")
    print(f"content_hash={manifest['content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
