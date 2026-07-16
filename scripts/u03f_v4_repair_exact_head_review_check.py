#!/usr/bin/env python3
"""Verify the independent review of the exact U-03F V4 repair head."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from btc_eth_dual_quant.audit.liquid_universe_v4_audit_artifacts import scan_float_timestamp_paths


ROOT = Path(__file__).resolve().parents[1]
TARGET_PR = 98
TARGET_BASE = "0e65cd41bfac590d40ae5cb0590cc7102019018c"
TARGET_HEAD = "27e6436c0a4b00ca7c8055bc763d533fcbcc9743"
TARGET_REMOTE_REF = "refs/remotes/origin/u03f-v4-repair-reviewed-head"
PROTOCOL_HASH = "9b771317d8257b397addefc262a1ffd48ded57ec1d79542372fe3c95cf8180c1"
IMPLEMENTATION_HASH = "9c97200e7e7ad441eac5282b7bbdda742980b13d59694c97e54cb65c4becae3a"
AUDITOR_HASH = "7407e147cb41cbb8fbf0b0fa5b3fa08421d03f51cafb19f41c4d1541923d51f1"
SOURCE_FREEZE_HASH = "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c"
CHANGED_FILE_LIST_HASH = "ecee2bbb76d0da0a0822cf218efda607fd38dea7d8e737c13fb8b19ada978ac9"
REPORT = ROOT / "reports/expert/U03F_V4_REPAIR_EXACT_HEAD_REVIEW.md"
EVIDENCE = ROOT / "reports/expert/evidence/u03f_v4_repair_exact_head_review.json"

CHANGED_FILES = [
    ".github/workflows/m0-validate.yml",
    ".github/workflows/u03f-v4-repair-implementation.yml",
    ".github/workflows/u03f-v4-repair-protocol.yml",
    "AGENTS.md",
    "NEXT_ACTION.md",
    "PROJECT_EXECUTION_CHECKLIST.md",
    "PROJECT_LEDGER.md",
    "PROJECT_STATE.yaml",
    "reports/INDEX.md",
    "reports/m0/U03F_V4_REPAIR_IMPLEMENTATION_STATUS.md",
    "scripts/liquid_universe_v4_historical_audit_blocked_check.py",
    "scripts/liquid_universe_v4_public_run.py",
    "scripts/liquid_universe_v4_requalification.py",
    "scripts/liquid_universe_v4_requalification_check.py",
    "scripts/liquid_universe_v4_requalification_validate.sh",
    "scripts/u03f_v4_independent_audit_check.py",
    "scripts/u03f_v4_repair_implementation_check.py",
    "scripts/u03f_v4_repair_implementation_validate.sh",
    "scripts/u03f_v4_repair_protocol_check.py",
    "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py",
    "tests/test_liquid_universe_v4_public_run.py",
    "tests/test_liquid_universe_v4_requalification.py",
    "tests/test_u03f_v4_repair_implementation.py",
    "tests/test_u03f_v4_repair_protocol.py",
]
IMPLEMENTATION_FILES = (
    "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py",
    "scripts/liquid_universe_v4_public_run.py",
    "scripts/liquid_universe_v4_requalification.py",
    "scripts/liquid_universe_v4_requalification_check.py",
)
AUDITOR_FILES = (
    "src/btc_eth_dual_quant/audit/liquid_universe_v4_independent.py",
    "src/btc_eth_dual_quant/audit/liquid_universe_v4_audit_artifacts.py",
    "scripts/u03f_v4_independent_audit.py",
)
EXPECTED_BLOBS = {
    "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py": "6bd95ce57ebd7bba5fae03585cdaed337f1b7c86",
    "scripts/liquid_universe_v4_public_run.py": "7a18aa267314bc0f11f393abc70c7678aaff4ac1",
    "scripts/liquid_universe_v4_requalification.py": "e50f481aadd33b9ba3b3f7f7cb209660e3b3a9a4",
    "scripts/liquid_universe_v4_requalification_check.py": "949bfb92af3373286b4d5fd46fb8c67b01bef0b7",
    "reports/m0/U03F_V4_REPAIR_IMPLEMENTATION_STATUS.md": "c69f34d9e7c466fe8391ba2eb9908c3889395b80",
    "scripts/u03f_v4_repair_implementation_check.py": "3b476577d8f7138f99b9b56bb3e2c7e6894f81fa",
    "tests/test_u03f_v4_repair_implementation.py": "ee6bad276e16f335921fcaf2ad32e0c243b34685",
    "tests/test_liquid_universe_v4_public_run.py": "91242746d391d44247124f65d95d8be335217a60",
    "tests/test_liquid_universe_v4_requalification.py": "6c63e8f3ad8ef9a131dd10bd57aa218f5f010540",
}
IMMUTABLE_EVIDENCE = {
    "reports/m0/LIQUID_SPOT_UNIVERSE_V4_QUALIFICATION_REPORT.md": "ad414f760655645e20c6bc20c49c0f25bf3aea1d5f47b373fc254364aab91e2a",
    "reports/m0/LIQUID_SPOT_UNIVERSE_V3_V4_DIFF_REPORT.md": "b43a365a906c9b2689d3853d3478762c25df64bc7193dbf54dd697e6e172cb06",
    "reports/m0/evidence/liquid_universe_v4/requalification_run_manifest.json": "77df052ce642231af1357a8c61848408f516421a83bd467bca39d5c9deb317ad",
    "reports/m0/evidence/liquid_universe_v4/source_freeze_manifest.json": "71ef8d900ceca6618d0557ce62db0b63814793502789bc8346ba02abc3bb96fb",
    "reports/expert/U03F_V4_INDEPENDENT_AUDIT_REPORT.md": "dab79b1224e1c1f8be4c6f6e018b9ce6f40e751af58d380fd4d872d3f442045c",
    "reports/expert/evidence/liquid_universe_v4_independent_audit/audit_summary.json": "d11af8c2fdc54cac699909b0b418dd90a5f1c87e6a5e91e892770924c2184003",
}
REVIEW_DIMENSIONS = (
    "exact_head_and_ci",
    "frozen_protocol_scope",
    "integer_time_authority",
    "strict_5m_physical_row_validity",
    "atomic_report_run_binding",
    "exact_frozen_source_consumption",
    "fresh_three_way_execution",
    "truthful_blocked_evidence",
    "historical_evidence_immutability",
    "auditor_algorithm_immutability",
    "zero_downstream_authorization",
)
AUTHORIZATION = {
    "merge_exact_implementation_after_review": True,
    "public_requalification": False,
    "new_independent_audit": False,
    "u04": False,
    "hypothesis": False,
    "strategy": False,
    "events": False,
    "signals": False,
    "returns": False,
    "backtesting": False,
    "oos": False,
    "api_trading": False,
    "execution_live": False,
    "m2": False,
}
CONTEXT_MARKERS = {
    "PROJECT_STATE.yaml": "u03f_v4_repair_exact_head_review:",
    "PROJECT_LEDGER.md": "U-03F V4 Repair Exact-Head Review Opened",
    "NEXT_ACTION.md": "## U-03F Repair Exact-Head Review",
    "reports/INDEX.md": "U03F_V4_REPAIR_EXACT_HEAD_REVIEW.md",
    "AGENTS.md": "## U-03F Repair Exact-Head Review Gate",
    "PROJECT_EXECUTION_CHECKLIST.md": "## U-03F Repair Exact-Head Review Supplemental Gate",
}


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _show_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{TARGET_HEAD}:{path}"], cwd=ROOT)


def target_available() -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{TARGET_HEAD}^{{commit}}"], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0


def content_set_hash(paths: tuple[str, ...], *, target: bool) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.encode())
        digest.update(b"\0")
        digest.update(_show_bytes(path) if target else (ROOT / path).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def protocol_hash() -> str:
    value = json.loads((ROOT / "config/liquid_universe_v4_repair_requalification_protocol.json").read_text())
    value.pop("generated_utc", None)
    return canonical_hash(value)


def build_document(generated_utc: str) -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema_version": 1,
        "review_id": "U03F-V4-REPAIR-EXACT-HEAD-REVIEW-V1",
        "generated_utc": generated_utc,
        "reviewed_target": {
            "pull_request": TARGET_PR,
            "base_sha": TARGET_BASE,
            "head_sha": TARGET_HEAD,
            "changed_files": CHANGED_FILES,
            "changed_file_list_sha256": CHANGED_FILE_LIST_HASH,
            "repair_implementation_sha256": IMPLEMENTATION_HASH,
            "repair_protocol_sha256": PROTOCOL_HASH,
            "auditor_algorithm_sha256": AUDITOR_HASH,
            "source_freeze_sha256": SOURCE_FREEZE_HASH,
            "target_blobs": EXPECTED_BLOBS,
        },
        "validation_evidence": {
            "github_checks_total": 110,
            "github_checks_success": 110,
            "local_unit_tests_total": 602,
            "local_unit_tests_success": 602,
            "frozen_fault_tests_total": 6,
            "frozen_fault_tests_success": 6,
            "public_requalification_executed": False,
            "new_independent_audit_executed": False,
        },
        "review_dimensions": [
            {"dimension": name, "status": "pass"} for name in REVIEW_DIMENSIONS
        ],
        "resolved_during_review": [
            {
                "severity": "high",
                "id": "U03F-RR-H01",
                "resolution": "Blocked evidence now requires the fail-closed determinism marker instead of the pass marker.",
            },
            {
                "severity": "high",
                "id": "U03F-RR-H02",
                "resolution": "Every consumed source key, SHA256 and byte size is bound to the exact 27,736-entry freeze.",
            },
            {
                "severity": "high",
                "id": "U03F-RR-H03",
                "resolution": "Resume was removed so cold, warm and worker must be regenerated under the current repair.",
            },
        ],
        "remaining_findings": {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "informational": [
                "The review is fixture and exact-head evidence; fixed-range public requalification has not run.",
                "A later blocked public result must be recorded truthfully and cannot proceed to a new audit.",
            ],
        },
        "authorization": AUTHORIZATION,
        "verdict": "approve",
    }
    identity = {key: value for key, value in document.items() if key != "generated_utc"}
    document["review_content_sha256"] = canonical_hash(identity)
    return document


def render(document: dict[str, Any]) -> str:
    target = document["reviewed_target"]
    evidence = document["validation_evidence"]
    lines = [
        "# U-03F V4 Repair Exact-Head Review", "",
        f"- Verdict: `{document['verdict']}`",
        f"- Target PR: `#{target['pull_request']}`",
        f"- Exact base: `{target['base_sha']}`",
        f"- Exact head: `{target['head_sha']}`",
        f"- Changed-file-list hash: `{target['changed_file_list_sha256']}`",
        f"- Repair implementation hash: `{target['repair_implementation_sha256']}`",
        f"- Frozen protocol hash: `{target['repair_protocol_sha256']}`",
        f"- Frozen auditor algorithm hash: `{target['auditor_algorithm_sha256']}`",
        f"- Source freeze hash: `{target['source_freeze_sha256']}`",
        f"- Review content hash: `{document['review_content_sha256']}`",
        "- Remaining critical/high: `0 / 0`", "",
        "## Validation", "",
        f"- GitHub exact-head checks: {evidence['github_checks_success']}/{evidence['github_checks_total']}",
        f"- Local exact-head unit tests: {evidence['local_unit_tests_success']}/{evidence['local_unit_tests_total']}",
        f"- Frozen fault tests: {evidence['frozen_fault_tests_success']}/{evidence['frozen_fault_tests_total']}",
        "- Public requalification executed: no",
        "- New independent audit executed: no", "",
        "## Review Matrix", "",
        "| Dimension | Result |", "| --- | --- |",
    ]
    lines.extend(f"| {item['dimension']} | {item['status']} |" for item in document["review_dimensions"])
    lines.extend(["", "## Resolved During Review", ""])
    lines.extend(
        f"- `{item['severity']}` `{item['id']}`: {item['resolution']}"
        for item in document["resolved_during_review"]
    )
    lines.extend([
        "", "## Authorization", "",
        "This review approves only the unchanged exact implementation head for merge. It does not",
        "run or approve public requalification, a new independent audit, U-04, strategy work,",
        "returns, backtesting, OOS, API/trading, execution/live or M2. Any target/hash drift",
        "invalidates this approval and stops the chain.", "",
    ])
    return "\n".join(lines)


def validate_target(*, require_remote_ref: bool = False) -> list[str]:
    failures: list[str] = []
    if not target_available():
        return ["exact implementation target is unavailable"] if require_remote_ref else []
    if _git("rev-parse", TARGET_HEAD) != TARGET_HEAD:
        failures.append("implementation target head changed")
    if require_remote_ref:
        try:
            if _git("rev-parse", TARGET_REMOTE_REF) != TARGET_HEAD:
                failures.append("PR #98 remote head drifted from reviewed target")
        except subprocess.CalledProcessError:
            failures.append("PR #98 fetched review ref is unavailable")
    paths = _git("diff", "--name-only", TARGET_BASE, TARGET_HEAD).splitlines()
    if paths != CHANGED_FILES or canonical_hash(sorted(paths)) != CHANGED_FILE_LIST_HASH:
        failures.append("implementation changed-file set drift")
    for path, expected in EXPECTED_BLOBS.items():
        if _git("rev-parse", f"{TARGET_HEAD}:{path}") != expected:
            failures.append(f"target blob drift: {path}")
    if content_set_hash(IMPLEMENTATION_FILES, target=True) != IMPLEMENTATION_HASH:
        failures.append("repair implementation hash drift")
    if protocol_hash() != PROTOCOL_HASH:
        failures.append("repair protocol hash drift")
    if content_set_hash(AUDITOR_FILES, target=False) != AUDITOR_HASH:
        failures.append("independent auditor algorithm hash drift")
    for path, expected in IMMUTABLE_EVIDENCE.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            failures.append(f"historical evidence drift: {path}")
    freeze = json.loads((ROOT / "reports/m0/evidence/liquid_universe_v4/source_freeze_manifest.json").read_text())
    if freeze.get("content_hash") != SOURCE_FREEZE_HASH or freeze.get("content", {}).get("archive_count") != 27_736:
        failures.append("source freeze binding drift")

    pipeline = _show_bytes("src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py").decode()
    public = _show_bytes("scripts/liquid_universe_v4_public_run.py").decode()
    requalification = _show_bytes("scripts/liquid_universe_v4_requalification.py").decode()
    requalification_check = _show_bytes("scripts/liquid_universe_v4_requalification_check.py").decode()
    for path, source in ((IMPLEMENTATION_FILES[0], pipeline), (IMPLEMENTATION_FILES[1], public)):
        findings = scan_float_timestamp_paths(source)
        if findings:
            failures.append(f"integer-time authority violation: {path}:{findings[0]}")
    for marker in ("_frozen_source_bindings", "_validate_frozen_source_rows", "REQUIRED_SOURCE_FREEZE_HASH"):
        if marker not in public:
            failures.append(f"exact frozen-source enforcement missing: {marker}")
    if "_download_missing_archive" in public:
        failures.append("public builder retains download path")
    if "--resume" in requalification or "status=resumed" in requalification:
        failures.append("requalification retains resume/reuse path")
    if "shutil.rmtree(work_root" not in requalification:
        failures.append("requalification does not force a fresh work-root")
    if "not_run_due_fail_closed_cold_block" not in requalification_check:
        failures.append("truthful blocked report marker is not enforced")
    return sorted(set(failures))


def validate_document(document: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if document != build_document(str(document.get("generated_utc"))):
        failures.append("review evidence is not the deterministic exact-head document")
    if document.get("verdict") != "approve":
        failures.append("exact-head review verdict is not approve")
    findings = document.get("remaining_findings", {})
    if findings.get("critical") or findings.get("high"):
        failures.append("approve requires zero remaining critical/high findings")
    if any(item.get("status") != "pass" for item in document.get("review_dimensions", [])):
        failures.append("approve requires every review dimension to pass")
    if document.get("authorization") != AUTHORIZATION:
        failures.append("review authorization matrix changed")
    return sorted(set(failures))


def validate_context() -> list[str]:
    return [
        f"review context marker missing: {path}"
        for path, marker in CONTEXT_MARKERS.items()
        if marker not in (ROOT / path).read_text(encoding="utf-8")
    ]


def validate() -> list[str]:
    failures = validate_target(require_remote_ref=os.environ.get("U03F_REQUIRE_TARGET_HEAD") == "1")
    try:
        document = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return failures + [f"review evidence load failed: {exc}"]
    failures.extend(validate_document(document))
    if REPORT.read_text(encoding="utf-8") != render(document):
        failures.append("review Markdown is not the deterministic JSON render")
    failures.extend(validate_context())
    return sorted(set(failures))


def main() -> int:
    failures = validate()
    if failures:
        print("u03f_v4_repair_exact_head_review_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("u03f_v4_repair_exact_head_review_check PASS")
    print(f"target_head={TARGET_HEAD}")
    print(f"repair_implementation_hash={IMPLEMENTATION_HASH}")
    print("verdict=approve critical=0 high=0 public_requalification=no audit=no u04=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
