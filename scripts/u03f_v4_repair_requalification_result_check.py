#!/usr/bin/env python3
"""Validate the frozen U-03F repair-requalification blocked result."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from btc_eth_dual_quant.data.lifecycle_artifacts import V4_MANIFEST_TYPES
from scripts.liquid_universe_v4_requalification_check import check as base_check


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v4_repair_requalification"
REPORT = ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V4_REPAIR_REQUALIFICATION_REPORT.md"
DIFF_REPORT = ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V4_REPAIR_V3_V4_DIFF_REPORT.md"

RUN_CONTENT_HASH = "0792ec7b52dbabb6057f0c238d963ed774c1e9e838b42cb21a03bc7e334f68cf"
COLD_ARTIFACT_SET_HASH = "b7cac049c6ab339f52fc29c7f31d275db09b3a4c47e2f62b38175cea219b2f83"
SOURCE_FREEZE_HASH = "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c"
REPORT_SHA256 = "0085e32766bc7b0b261c158aecef5d022154f396533712a957a4b97b1a3c1eb2"
DIFF_REPORT_SHA256 = "4411c02e390b4948a4b706a17c25f5f77f3d55746f6a6e8491e8ad11c2d0a86c"
SOURCE_FREEZE_FILE_SHA256 = "71ef8d900ceca6618d0557ce62db0b63814793502789bc8346ba02abc3bb96fb"
BLOCKER_COUNT = 119

IMMUTABLE_HISTORICAL_EVIDENCE = {
    "reports/m0/LIQUID_SPOT_UNIVERSE_V4_QUALIFICATION_REPORT.md":
        "ad414f760655645e20c6bc20c49c0f25bf3aea1d5f47b373fc254364aab91e2a",
    "reports/m0/evidence/liquid_universe_v4/requalification_run_manifest.json":
        "77df052ce642231af1357a8c61848408f516421a83bd467bca39d5c9deb317ad",
    "reports/expert/U03F_V4_INDEPENDENT_AUDIT_REPORT.md":
        "dab79b1224e1c1f8be4c6f6e018b9ce6f40e751af58d380fd4d872d3f442045c",
    "reports/expert/evidence/liquid_universe_v4_independent_audit/audit_summary.json":
        "d11af8c2fdc54cac699909b0b418dd90a5f1c87e6a5e91e892770924c2184003",
}

CONTEXT_MARKERS = {
    "PROJECT_STATE.yaml": "processing_errors: 119",
    "PROJECT_LEDGER.md": "warm and worker are `not_run_due_fail_closed_cold_block`",
    "NEXT_ACTION.md": "119 physical",
    "reports/INDEX.md": "119 strict 5m interval-boundary errors",
    "AGENTS.md": "Cold is truthfully `blocked` on 119 strict 5m interval-boundary errors",
    "PROJECT_EXECUTION_CHECKLIST.md": "119 processing errors",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate() -> list[str]:
    failures: list[str] = []
    try:
        base = base_check()
    except Exception as exc:  # pragma: no cover - exact error is reported to CI
        return [f"base requalification check failed: {exc}"]
    if base != {"status": "blocked", "content_hash": RUN_CONTENT_HASH}:
        failures.append("base result identity mismatch")

    run = load(EVIDENCE / "requalification_run_manifest.json")
    summary = load(EVIDENCE / "qualification_summary.json")["content"]
    freeze = load(EVIDENCE / "source_freeze_manifest.json")
    content = run.get("content", {})
    builds = content.get("builds", {})
    cold = builds.get("cold", {})

    if run.get("content_hash") != RUN_CONTENT_HASH:
        failures.append("run content hash mismatch")
    if content.get("status") != "blocked":
        failures.append("result is not blocked")
    if content.get("range") != {"start": "2020-01", "end": "2026-06"}:
        failures.append("fixed range mismatch")
    if content.get("source_mode") != "frozen_local_only":
        failures.append("source mode is not frozen_local_only")
    if content.get("source_freeze_hash") != SOURCE_FREEZE_HASH:
        failures.append("run source freeze mismatch")
    if content.get("builds_completed") != ["cold"] or set(builds) != {"cold"}:
        failures.append("blocked run did not stop after cold")
    if content.get("determinism_status") != "not_run_due_fail_closed_cold_block":
        failures.append("blocked determinism marker mismatch")
    if content.get("deterministic_mismatches") is not None:
        failures.append("blocked run fabricated determinism count")
    if cold.get("artifact_set_hash") != COLD_ARTIFACT_SET_HASH:
        failures.append("cold artifact-set hash mismatch")

    blockers = summary.get("blockers", [])
    if len(blockers) != BLOCKER_COUNT or content.get("stop_reasons") != blockers:
        failures.append("exact 119-stop-reason binding mismatch")
    if any(not reason.endswith(":5m interval boundary is invalid") for reason in blockers):
        failures.append("unexpected blocker class")
    for field in (
        "processing_errors", "unresolved_row_conflicts", "unresolved_lifecycle_rows",
        "epoch_overlaps", "unresolved_gaps", "synthetic_fills", "replacement_members",
    ):
        if content.get(field) != summary.get(field):
            failures.append(f"run/summary counter mismatch: {field}")
    if summary.get("processing_errors") != BLOCKER_COUNT:
        failures.append("processing error count mismatch")

    expected_manifest_hashes = cold.get("manifest_hashes", {})
    if set(expected_manifest_hashes) != set(V4_MANIFEST_TYPES):
        failures.append("cold manifest identity set mismatch")
    else:
        for name in sorted(V4_MANIFEST_TYPES):
            document = load(EVIDENCE / f"{name}.json")
            if document.get("content_hash") != expected_manifest_hashes[name]:
                failures.append(f"cold manifest binding mismatch: {name}")

    if freeze.get("content_hash") != SOURCE_FREEZE_HASH:
        failures.append("source freeze content hash mismatch")
    if freeze.get("content", {}).get("archive_count") != 27_736:
        failures.append("source freeze archive count mismatch")
    if sha256(EVIDENCE / "source_freeze_manifest.json") != SOURCE_FREEZE_FILE_SHA256:
        failures.append("source freeze file hash mismatch")
    if sha256(REPORT) != REPORT_SHA256 or cold.get("qualification_report_sha256") != REPORT_SHA256:
        failures.append("final report binding mismatch")
    if sha256(DIFF_REPORT) != DIFF_REPORT_SHA256 or cold.get("v3_v4_diff_sha256") != DIFF_REPORT_SHA256:
        failures.append("V3/V4 diff binding mismatch")

    if any(summary.get("authorizations", {}).values()) or any(content.get("authorizations", {}).values()):
        failures.append("downstream authorization expanded")
    for path, expected in IMMUTABLE_HISTORICAL_EVIDENCE.items():
        if sha256(ROOT / path) != expected:
            failures.append(f"historical evidence drift: {path}")
    for path, marker in CONTEXT_MARKERS.items():
        if marker not in (ROOT / path).read_text(encoding="utf-8"):
            failures.append(f"context marker missing: {path}")
    return sorted(set(failures))


def main() -> int:
    failures = validate()
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print("u03f_v4_repair_requalification_result_check PASS")
    print(f"status=blocked blockers={BLOCKER_COUNT} run_hash={RUN_CONTENT_HASH}")
    print("builds=cold warm=not_run worker=not_run audit=no u04=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
