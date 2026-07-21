#!/usr/bin/env python3
"""Run ADR-0015 fixed-range requalification from frozen local sources only."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

from scripts.liquid_universe_public_run import DEFAULT_RAW, ROOT
from scripts.liquid_universe_v4_requalification import execute


EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification"
REPORT = ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V4_ADR0015_REQUALIFICATION_REPORT.md"
DIFF_REPORT = ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V4_ADR0015_V3_V4_DIFF_REPORT.md"
WORK_ROOT = ROOT / "storage/logs/liquid_universe_v4_adr0015_requalification"

REVIEWED_IMPLEMENTATION_HEAD = "67e7d29eaed63a3edb903dd618184bc9f02c5748"
IMPLEMENTATION_REVIEW_MERGE = "a02d4dfbe752bb7e26e8a7b41971a9f089ddc57f"
CONTROLLED_INTEGRATION_MERGE = "e2112a31908f1587eb657a4123f1f114cf2016fe"
RUNTIME_POLICY_HASH = "0ac074cf6849918065569fe6fb77eb8bd68f30d416325a70d4f55eef02262d04"
ALGORITHM_HASH = "8f8a36681f35c64a244a7fc0e7155fdcdeb8fb6e5ace2054d261ef8daadea4ff"
IMPLEMENTATION_CONTENT_HASH = "7cc4f9a3343de1f81ea7ac38e7c77efdd9fdb6bcbe3f8eeec099ddfca1dd020f"

EXACT_IMPLEMENTATION_FILES = (
    "config/liquid_spot_invalid_interval_policy_v1.json",
    "reports/m0/ADR_0015_INVALID_INTERVAL_POLICY_IMPLEMENTATION_STATUS.md",
    "scripts/adr0015_invalid_interval_implementation_check.py",
    "scripts/adr0015_invalid_interval_implementation_validate.sh",
    "scripts/liquid_universe_v4_public_run.py",
    "src/btc_eth_dual_quant/data/invalid_interval_quarantine.py",
    "tests/test_adr0015_invalid_interval_policy.py",
)

RUN_BINDINGS = {
    "reviewed_implementation_head": REVIEWED_IMPLEMENTATION_HEAD,
    "implementation_review_merge": IMPLEMENTATION_REVIEW_MERGE,
    "controlled_integration_merge": CONTROLLED_INTEGRATION_MERGE,
    "controlled_integration_selective_run": 29572828915,
    "controlled_integration_main_run": 29573400780,
    "runtime_policy_hash": RUNTIME_POLICY_HASH,
    "algorithm_hash": ALGORITHM_HASH,
    "implementation_content_hash": IMPLEMENTATION_CONTENT_HASH,
}


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args), cwd=ROOT, check=False, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def preflight_exact_implementation() -> None:
    for commit in (REVIEWED_IMPLEMENTATION_HEAD, IMPLEMENTATION_REVIEW_MERGE, CONTROLLED_INTEGRATION_MERGE):
        result = _git("merge-base", "--is-ancestor", commit, "HEAD")
        if result.returncode:
            raise ValueError(f"required implementation ancestry missing: {commit}")
    result = _git("diff", "--exit-code", REVIEWED_IMPLEMENTATION_HEAD, "HEAD", "--", *EXACT_IMPLEMENTATION_FILES)
    if result.returncode:
        raise ValueError("reviewed implementation blob drift before requalification")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--work-root", type=Path, default=WORK_ROOT)
    parser.add_argument("--evidence-dir", type=Path, default=EVIDENCE)
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--diff-report", type=Path, default=DIFF_REPORT)
    parser.add_argument("--workers-cold", type=int, default=16)
    parser.add_argument("--workers-warm", type=int, default=3)
    parser.add_argument("--workers-variant", type=int, default=7)
    args = parser.parse_args()
    preflight_exact_implementation()
    document = execute(
        raw_root=args.raw_root,
        work_root=args.work_root,
        evidence_dir=args.evidence_dir,
        report_path=args.report,
        diff_report_path=args.diff_report,
        workers_cold=args.workers_cold,
        workers_warm=args.workers_warm,
        workers_variant=args.workers_variant,
        run_bindings=RUN_BINDINGS,
    )
    print(f"status={document['content']['status']} content_hash={document['content_hash']}")
    return 0 if document["content"]["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
