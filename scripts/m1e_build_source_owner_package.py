#!/usr/bin/env python3
"""Render a sanitized Binance source-owner package from ignored evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.data.source_owner_package import build_package, render_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build M1E Binance source-owner package")
    parser.add_argument("--evidence", default="storage/logs/m1e_conflict_diagnostics.json")
    parser.add_argument("--json-out", default="reports/m1/M1E_BINANCE_SOURCE_OWNER_EVIDENCE.json")
    parser.add_argument("--report-out", default="reports/m1/M1E_BINANCE_SOURCE_OWNER_ESCALATION.md")
    parser.add_argument("--submission-url", default=None)
    parser.add_argument("--submitted-at-utc", default=None)
    args = parser.parse_args()
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    package = build_package(evidence, submission_url=args.submission_url, submitted_at_utc=args.submitted_at_utc)
    json_path = Path(args.json_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(package), encoding="utf-8")
    print(f"json={json_path}")
    print(f"report={report_path}")
    print(f"status={package['status']} supplemental_rows={package['supplemental_rows']} submitted={'yes' if package['external_submission_performed'] else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
