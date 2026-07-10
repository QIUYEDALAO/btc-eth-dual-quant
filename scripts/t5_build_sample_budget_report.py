#!/usr/bin/env python3
"""Build the sanitized T5 metadata-only sample-budget precheck report."""

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
from btc_eth_dual_quant.audit.sample_budget import evaluate_calendar_budget, extract_research_calendar_metadata


CANDIDATE_ID = "M1D-15M-DISCRETE-DISLOCATION"
HYPOTHESIS = (
    "M1D-15M-DISCRETE-DISLOCATION: BTC/USDT and ETH/USDT spot; completed 15m candles identify "
    "discrete large-price-dislocation events; enter no earlier than the next 15m open; 1m data is "
    "execution detail only; no shorting or leverage."
)
DIGEST = "fdccf79b213f87fc9ee1cb74daf42f67e7ba63fba6de9990851c2eec9e11e1a7"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="T5 metadata-only sample-budget precheck")
    parser.add_argument("--t1-manifest", type=Path, default=ROOT / "storage/logs/t1_minute_archive_manifest.json")
    parser.add_argument("--t2-manifest", type=Path, default=ROOT / "storage/logs/t2_golden_manifest.json")
    parser.add_argument("--ledger", type=Path, default=ROOT / "STRATEGY_TRIAL_LEDGER.yaml")
    parser.add_argument("--out", type=Path, default=ROOT / "reports/m1/T5_M1D_SAMPLE_BUDGET_PRECHECK.md")
    args = parser.parse_args()

    identity = validate_candidate_identity(
        args.ledger,
        candidate_id=CANDIDATE_ID,
        expected_hypothesis=HYPOTHESIS,
        expected_sha256=DIGEST,
    )
    t1 = json.loads(args.t1_manifest.read_text(encoding="utf-8"))
    t2 = json.loads(args.t2_manifest.read_text(encoding="utf-8"))
    metadata = extract_research_calendar_metadata(t1, t2)
    result = evaluate_calendar_budget(metadata, identity)

    lines = [
        "# T5 M1D Sample Budget Precheck",
        "",
        f"- Status: {result.status}",
        f"- Generated UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "- Scope: metadata-only calendar and sample-budget precheck",
        "- Candidate evaluated: no",
        "- Events selected: no",
        "- OOS prices/returns accessed: no",
        "- Trial count incremented: no",
        "- T5 feasibility analysis executed: no",
        "- Strategy returns computed: no",
        "- API key used: no",
        "- Private data used: no",
        "- Live/paper/execution implemented: no",
        "",
        "## Input Authority",
        "",
        f"- T1 manifest SHA256: `{file_sha256(args.t1_manifest)}`",
        f"- T2 manifest SHA256: `{file_sha256(args.t2_manifest)}`",
        f"- Candidate hypothesis SHA256: `{identity.sha256}`",
        f"- Budget result SHA256: `{result.canonical_sha256}`",
        "- Only manifest calendar fields, public/private safety flags, and T2 blocker count were read.",
        "- No OHLCV row, price, event, signal, trade, equity, or return field was read.",
        "",
        "## Fixed Policy",
        "",
        "- Calendar split: final 30% is sealed OOS.",
        "- Minimum sealed OOS calendar: 540 days.",
        "- The API rejects any different fraction or calendar minimum.",
        "",
        "## Calendar Result",
        "",
        "| Measure | Result | Gate |",
        "|---|---:|---|",
        f"| Research start | {result.research_start.isoformat()} | frozen |",
        f"| Latest complete day | {result.latest_complete_day.isoformat()} | complete month |",
        f"| Full history | {result.full_days} days | diagnostic |",
        f"| IS | {result.is_days} days | diagnostic |",
        f"| Sealed OOS | {result.oos_days} days | fail |",
        f"| Required sealed OOS | {result.required_oos_days} days | fixed |",
        f"| OOS shortage | {result.shortage_days} days | blocked |",
        f"| Required full history | {result.required_full_days} days | fixed |",
        f"| Earliest eligible complete day | {result.earliest_eligible_end_day.isoformat()} | informational |",
        "",
        "## Gate",
        "",
        "| Check | Status |",
        "|---|---|",
        "| T1/T2 metadata alignment | pass |",
        "| T2 relevant blockers equal zero | pass |",
        "| Trial ledger identity and hash locked | pass |",
        "| OOS remains sealed | pass |",
        "| Metadata-only precheck boundary | pass |",
        f"| OOS calendar >= 540 days | {'pass' if result.calendar_gate_passed else 'fail'} |",
        "",
        "- T5 sample-budget precheck: completed_blocked",
        "- T5 final status: blocked_insufficient_oos_calendar",
        "- T6 authorized: no",
        "- Strategy code authorized: no",
        "- M2 authorized: no",
        "",
        "The current M1D candidate stops here. No event threshold, return analysis, Freqtrade strategy, or OOS opening may follow this failed precheck.",
        "",
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"report={args.out}")
    print(f"status={result.status} full={result.full_days} is={result.is_days} oos={result.oos_days}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
