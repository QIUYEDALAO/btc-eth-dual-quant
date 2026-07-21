#!/usr/bin/env python3
"""Run the reviewed ADR-0015 independent audit from frozen local sources."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from btc_eth_dual_quant.audit.liquid_universe_v4_adr0015_audit_run import (
    execute_adr0015_audit,
    write_adr0015_audit_result,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe")
    parser.add_argument("--protocol", type=Path, default=ROOT / "config/liquid_universe_v4_adr0015_independent_audit_protocol.json")
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/m0/ADR_0015_INVALID_INTERVAL_INDEPENDENT_AUDIT_REPORT.md")
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    review = json.loads(args.review.read_text(encoding="utf-8"))
    result = execute_adr0015_audit(
        repository=ROOT, raw_root=args.raw_root, protocol=protocol, review=review,
    )
    write_adr0015_audit_result(result=result, evidence_dir=args.evidence_dir, report_path=args.report)
    print(json.dumps(result["summary"], sort_keys=True, separators=(",", ":")))
    return 0 if result["summary"]["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
