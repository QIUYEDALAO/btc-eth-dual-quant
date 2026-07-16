#!/usr/bin/env python3
"""Execute the frozen U-03F V4 audit offline and write sanitized evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from btc_eth_dual_quant.audit.liquid_universe_v4_audit_run import (
    execute_audit,
    write_audit_result,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument(
        "--protocol",
        type=Path,
        default=ROOT / "config/liquid_universe_v4_independent_audit_protocol.json",
    )
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=ROOT / "reports/expert/evidence/liquid_universe_v4_independent_audit",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "reports/expert/U03F_V4_INDEPENDENT_AUDIT_REPORT.md",
    )
    args = parser.parse_args()
    result = execute_audit(repository=ROOT, raw_root=args.raw_root, protocol_path=args.protocol)
    if "summary" not in result:
        print(f"verdict={result['verdict']} failures={len(result.get('failures', []))}")
        return 2
    write_audit_result(result=result, evidence_dir=args.evidence_dir, report_path=args.report)
    summary = result["summary"]
    print(
        f"verdict={summary['verdict']} "
        f"critical={len(summary['critical_findings'])} "
        f"high={len(summary['high_findings'])} "
        f"artifact_set={summary['independent_artifact_set_hash']}"
    )
    # A truthful failed audit is a successfully executed audit. Gate scripts
    # inspect the verdict separately; the runner reports execution errors only.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
