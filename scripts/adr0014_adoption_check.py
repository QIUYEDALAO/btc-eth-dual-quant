#!/usr/bin/env python3
"""Verify conditional ADR-0014 adoption without widening its reviewed semantics."""
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
ADOPTED_ADR_PATH = ROOT / "docs/decisions/ADR-0014-official-lifecycle-boundary-placeholder-policy.md"
MANIFEST_PATH = ROOT / "reports/expert/evidence/adr0014_adoption_manifest.json"
REVIEWED_HEAD = "31c967c785128671769eb713baed265da8ae0f2a"
REVIEWED_BASE = "ab45ba4f12badab8a00faa0181b48c948643e223"
EXPECTED_SEMANTIC_BODY_HASH = "5c2113edbb7a69b52c1e78e3a6c3f223dac36d21769a9e1c5b815894945f8e99"

EXPECTED_REVIEW_BINDINGS = {
    "reviewed_pr_number": 81,
    "reviewed_pr_head": REVIEWED_HEAD,
    "reviewed_pr_base": REVIEWED_BASE,
    "reviewed_adr_sha256": "a8c57bec6ee31342d0a9dd8e14deb4fd0ed28202aa838705d699522fa58d6790",
    "reviewed_semantic_body_hash": EXPECTED_SEMANTIC_BODY_HASH,
    "policy_model_hash": "bce56a1070ef0690b13cba492bf9619a456af2618be94eb2ecbe03ea7e709d97",
    "fault_matrix_hash": "90beb680e568ab5bc045556ef728e34cd2827d5bf6005ebb524b6e38ed6a199f",
    "mc_conformance_hash": "303e4d28ea27575ed7fa46e9d9da459e5c237a0390f36f9c9de9cfcd7c9821d2",
    "prior_review_content_hash": "3d7e089e3322970a8602dda8a4c4c82d01f5604276688567754d77319c932a15",
    "conformance_review_pr": 84,
    "conformance_review_merge_sha": "5c839cdf8b825e18546a5bdbfe3fd9ca1f2f1328",
    "conformance_review_content_hash": "d2b0dfa7fdd9c8cc5bef2c716600f6e79ec6272651fa067dc23a3d0915271bc7",
    "klay_adjudication_evidence_hash": "6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a",
}

EXPECTED_AUTHORIZATIONS = {
    "lifecycle_policy_adopted": True,
    "v4_contract_implementation": True,
    "v4_lifecycle_policy_implementation": True,
    "v4_lifecycle_event_registry_implementation": True,
    "fixture_validation": True,
    "fault_injection": True,
    "fixed_range_v4_public_requalification": True,
    "u03f_execution": False,
    "u04": False,
    "hypothesis_preregistration": False,
    "strategy_code": False,
    "event_scan": False,
    "signals": False,
    "returns": False,
    "backtesting": False,
    "oos": False,
    "api_or_trading": False,
    "execution_live": False,
    "m2": False,
}

MODEL_BINDINGS = {
    "docs/decisions/proposals/adr0014_lifecycle_policy_model.json": {
        "raw_sha256": "6686fa5e666145b6fb3c9487f4f3749cb7d6cd6c95ff6448497d264fa64c2549",
        "canonical_hash": EXPECTED_REVIEW_BINDINGS["policy_model_hash"],
    },
    "docs/decisions/proposals/adr0014_lifecycle_fault_matrix.json": {
        "raw_sha256": "c30bd234dc44257f302a641c15b10bcc94a4ef7641db41d588dfa4b884c7dfd3",
        "canonical_hash": EXPECTED_REVIEW_BINDINGS["fault_matrix_hash"],
    },
    "docs/decisions/proposals/adr0014_mc_conformance.json": {
        "raw_sha256": "8e93d333a0f0c32a14df6d151a7506bd1071d6d285997f4e3b7012b49f2edbdd",
        "canonical_hash": EXPECTED_REVIEW_BINDINGS["mc_conformance_hash"],
    },
}

DEPENDENCY_ORDER = [
    "A_conditional_adoption",
    "B_v4_implementation",
    "C_independent_implementation_review",
    "D_fixed_range_public_requalification",
    "E_governance_closeout",
]


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def extract_semantic_body(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    start = normalized.index("## MC-01:")
    authorization_headers = ("## Draft Authorization Matrix", "## Adoption Authorization Matrix")
    ends = [normalized.find(header, start) for header in authorization_headers]
    valid_ends = [end for end in ends if end >= 0]
    if not valid_ends:
        raise ValueError("ADR-0014 authorization matrix heading missing")
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
        "manifest_type": "adr0014_conditional_adoption",
        "review_bindings": dict(EXPECTED_REVIEW_BINDINGS),
        "content": {
            "adoption_status": "accepted_for_v4_implementation_and_fixed_range_public_requalification_only",
            "adopted_semantic_body_hash": EXPECTED_SEMANTIC_BODY_HASH,
            "model_bindings": copy.deepcopy(MODEL_BINDINGS),
            "authorization_matrix": dict(EXPECTED_AUTHORIZATIONS),
            "dependency_order": list(DEPENDENCY_ORDER),
            "stop_condition": "No U-03F, U-04, research, strategy, returns, OOS, API/trading, execution/live or M2 authority is created.",
        },
    }
    document["content_hash"] = canonical_hash(content_identity(document))
    document["generated_utc"] = generated_utc or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return document


def verify_adoption_document(document: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if document.get("schema_version") != 1 or document.get("manifest_type") != "adr0014_conditional_adoption":
        failures.append("adoption schema or manifest type changed")
    bindings = document.get("review_bindings", {})
    for key, value in EXPECTED_REVIEW_BINDINGS.items():
        if bindings.get(key) != value:
            failures.append(f"review binding changed: {key}")
    content = document.get("content", {})
    if content.get("adoption_status") != "accepted_for_v4_implementation_and_fixed_range_public_requalification_only":
        failures.append("adoption status changed")
    if content.get("adopted_semantic_body_hash") != EXPECTED_SEMANTIC_BODY_HASH:
        failures.append("adopted semantic body hash changed")
    if content.get("model_bindings") != MODEL_BINDINGS:
        failures.append("docs-only model bindings changed")
    if content.get("authorization_matrix") != EXPECTED_AUTHORIZATIONS:
        failures.append("authorization matrix changed")
    if content.get("dependency_order") != DEPENDENCY_ORDER:
        failures.append("dependency order changed")
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


def _verify_reviewed_source() -> list[str]:
    failures: list[str] = []
    try:
        raw = _git("show", f"{REVIEWED_HEAD}:docs/decisions/ADR-0014-official-lifecycle-boundary-placeholder-policy.md")
    except subprocess.CalledProcessError:
        return ["reviewed ADR source is unavailable"]
    if hashlib.sha256(raw).hexdigest() != EXPECTED_REVIEW_BINDINGS["reviewed_adr_sha256"]:
        failures.append("reviewed ADR source hash changed")
    try:
        semantic_hash = canonical_hash(extract_semantic_body(raw.decode("utf-8")))
    except (UnicodeDecodeError, ValueError) as exc:
        failures.append(f"reviewed ADR semantic body invalid: {exc}")
    else:
        if semantic_hash != EXPECTED_SEMANTIC_BODY_HASH:
            failures.append("reviewed ADR semantic body hash changed")
    return failures


def verify_repository(*, check_stage_scope: bool = True) -> list[str]:
    failures: list[str] = []
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"adoption manifest load failed: {exc}"]
    failures.extend(verify_adoption_document(manifest))
    # The adoption stage binds the exact review-branch object before merge. Later
    # stages validate the merged, hash-bound adoption evidence because a closed
    # PR head is not guaranteed to be reachable in a clean GitHub checkout.
    if check_stage_scope:
        failures.extend(_verify_reviewed_source())

    try:
        adr = ADOPTED_ADR_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        failures.append(f"adopted ADR load failed: {exc}")
    else:
        required_markers = (
            "- Status: Accepted for V4 implementation and fixed-range public requalification only",
            "- Adoption evidence: PR #84",
            "## Adoption Scope",
            "## Adoption Authorization Matrix",
            "## Adoption Dependency Order",
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

    for relative_path, expected in MODEL_BINDINGS.items():
        path = ROOT / relative_path
        try:
            raw = path.read_bytes()
            parsed = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"docs-only model load failed: {relative_path}: {exc}")
            continue
        if hashlib.sha256(raw).hexdigest() != expected["raw_sha256"]:
            failures.append(f"docs-only model bytes changed: {relative_path}")
        if canonical_hash(parsed) != expected["canonical_hash"]:
            failures.append(f"docs-only model semantics changed: {relative_path}")

    if check_stage_scope:
        try:
            changed = _git("diff", "--name-only", "origin/main...").decode().splitlines()
        except subprocess.CalledProcessError:
            changed = _git("diff", "--name-only").decode().splitlines()
        forbidden = [
            path for path in changed
            if path.startswith(("src/", "config/", "reports/m0/evidence/liquid_universe_v4/"))
            or "requalification" in path.lower()
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
        MANIFEST_PATH.write_text(
            json.dumps(build_adoption_document(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    failures = verify_repository(check_stage_scope=not args.evidence_only)
    if failures:
        print("ADR0014_ADOPTION_CHECK FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    print("ADR0014_ADOPTION_CHECK PASS")
    print(f"reviewed_head={REVIEWED_HEAD}")
    print(f"semantic_body_hash={EXPECTED_SEMANTIC_BODY_HASH}")
    print(f"content_hash={manifest['content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
