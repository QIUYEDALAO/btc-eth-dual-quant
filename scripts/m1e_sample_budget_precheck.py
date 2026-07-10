#!/usr/bin/env python3
"""Generate the M1E metadata-only calendar admission report."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.audit.feasibility import validate_candidate_identity
from btc_eth_dual_quant.audit.sample_budget import evaluate_calendar_budget, extract_m1e_requalification_metadata
from m1e_contract_check import EXPECTED_HASH, EXPECTED_HYPOTHESIS

CANDIDATE_ID = "M1E-1H-TREND-BREAKOUT"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_report(result: object, *, manifest_sha256: str, candidate_sha256: str) -> str:
    passed = result.calendar_gate_passed
    status = "sample_budget_pass_design_only" if passed else "blocked_insufficient_oos_calendar"
    return "\n".join([
        "# M1E 1H Sample Budget Report", "",
        f"- Status: {status}",
        f"- Generated UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "- Scope: metadata-only calendar admission",
        "- Candidate evaluated: no", "- Events selected: no",
        "- OOS prices/returns accessed: no", "- Trial count incremented: no",
        "- Strategy rules selected: no", "- Strategy returns computed: no",
        "- API key used: no", "- Private data used: no", "",
        "## Input Authority", "",
        f"- M1E requalification manifest SHA256: `{manifest_sha256}`",
        f"- Candidate hypothesis SHA256: `{candidate_sha256}`",
        f"- Budget result SHA256: `{result.canonical_sha256}`",
        "- Only sanitized manifest admission metadata and sealed trial identity were read.",
        "- No OHLCV row, price, event, signal, trade, equity, or return field was read.", "",
        "## Fixed Policy", "",
        "- Calendar split: final 30% is sealed OOS.",
        "- Minimum full history: 1800 days.",
        "- Minimum sealed OOS calendar: 540 days.",
        "- Callers cannot override these values.", "",
        "## Calendar Result", "",
        "| Measure | Result | Gate |", "| --- | ---: | --- |",
        f"| Research start | {result.research_start.isoformat()} | frozen |",
        f"| Latest complete day | {result.latest_complete_day.isoformat()} | complete month |",
        f"| Full history | {result.full_days} days | {'pass' if result.full_days >= result.required_full_days else 'fail'} |",
        f"| IS | {result.is_days} days | diagnostic |",
        f"| Sealed OOS start | {result.oos_start_day.isoformat()} | frozen split |",
        f"| Sealed OOS | {result.oos_days} days | {'pass' if passed else 'fail'} |",
        f"| Required sealed OOS | {result.required_oos_days} days | fixed |",
        f"| OOS shortage | {result.shortage_days} days | {'pass' if not result.shortage_days else 'blocked'} |",
        f"| Required full history | {result.required_full_days} days | fixed |",
        f"| Earliest eligible complete day | {result.earliest_eligible_end_day.isoformat()} | informational |", "",
        "## Gate", "",
        f"- M1E sample-budget Gate: {'pass' if passed else 'blocked'}",
        "- OOS remains sealed: pass", "- Metadata-only boundary: pass",
        f"- IS-only design review authorized: {'yes' if passed else 'no'}",
        "- Strategy code authorized: no", "- Freqtrade backtesting authorized: no",
        "- M2 authorized: no", "",
        "Passing this Gate authorizes a separate IS-only rule-design review. It does not approve a strategy, open OOS, authorize backtesting, or permit trading.", "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description="M1E metadata-only sample-budget precheck")
    parser.add_argument("--manifest", type=Path, default=ROOT / "storage/logs/m1e_canonical_5m_v2_manifest.json")
    parser.add_argument("--ledger", type=Path, default=ROOT / "STRATEGY_TRIAL_LEDGER.yaml")
    parser.add_argument("--out", type=Path, default=ROOT / "reports/m1/M1E_1H_SAMPLE_BUDGET_REPORT.md")
    args = parser.parse_args()
    identity = validate_candidate_identity(
        args.ledger, candidate_id=CANDIDATE_ID,
        expected_hypothesis=EXPECTED_HYPOTHESIS, expected_sha256=EXPECTED_HASH,
    )
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = evaluate_calendar_budget(extract_m1e_requalification_metadata(manifest), identity)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_report(
        result, manifest_sha256=file_sha256(args.manifest), candidate_sha256=identity.sha256
    ), encoding="utf-8")
    print(f"report={args.out}")
    print(f"status={result.status} full={result.full_days} is={result.is_days} oos={result.oos_days}")
    return 0 if result.calendar_gate_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
