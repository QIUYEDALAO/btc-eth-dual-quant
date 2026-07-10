#!/usr/bin/env python3
"""Build the sanitized T4 IS-only feasibility-harness report."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.audit.feasibility import CostScenario, HORIZONS, validate_candidate_identity


CANDIDATE_ID = "M1D-15M-DISCRETE-DISLOCATION"
HYPOTHESIS = (
    "M1D-15M-DISCRETE-DISLOCATION: BTC/USDT and ETH/USDT spot; completed 15m candles identify "
    "discrete large-price-dislocation events; enter no earlier than the next 15m open; 1m data is "
    "execution detail only; no shorting or leverage."
)
DIGEST = "fdccf79b213f87fc9ee1cb74daf42f67e7ba63fba6de9990851c2eec9e11e1a7"
FULL_DAYS = 1004
IS_DAYS = 702
OOS_DAYS = 302
REQUIRED_OOS_DAYS = 540
REQUIRED_FULL_DAYS = 1800


def load_smoke(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "pass" or len(payload.get("profiles", [])) != 2:
        raise ValueError("T4 golden structure smoke evidence is incomplete")
    if any(profile.get("rows") != 96384 for profile in payload["profiles"]):
        raise ValueError("T4 golden structure row count differs from T2 authority")
    if any(payload.get(flag) is not False for flag in ("candidate_events_selected", "candidate_returns_computed", "oos_returns_accessed")):
        raise ValueError("T4 structure smoke crossed an IS-only safety boundary")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="T4 sanitized feasibility-harness report")
    parser.add_argument("--ledger", type=Path, default=ROOT / "STRATEGY_TRIAL_LEDGER.yaml")
    parser.add_argument("--smoke", type=Path, default=ROOT / "storage/logs/t4_golden_structure_smoke.json")
    parser.add_argument("--out", type=Path, default=ROOT / "reports/m1/T4_IS_ONLY_FEASIBILITY_HARNESS_REPORT.md")
    args = parser.parse_args()

    identity = validate_candidate_identity(
        args.ledger,
        candidate_id=CANDIDATE_ID,
        expected_hypothesis=HYPOTHESIS,
        expected_sha256=DIGEST,
    )
    smoke = load_smoke(args.smoke)
    profiles = sorted(smoke["profiles"], key=lambda item: item["symbol"])
    shortage = REQUIRED_OOS_DAYS - OOS_DAYS

    lines = [
        "# T4 IS-Only Feasibility Harness Report",
        "",
        "- Status: pass",
        f"- Generated UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "- Scope: reusable IS-only event feasibility tooling foundation",
        "- Candidate evaluated: no",
        "- Candidate events selected: no",
        "- Candidate returns computed: no",
        "- OOS returns accessed: no",
        "- Strategy code implemented: no",
        "- API key used: no",
        "- Live/paper/execution implemented: no",
        "",
        "## Trial-Ledger Lock",
        "",
        f"- Candidate identity checked: `{identity.candidate_id}`",
        f"- Hypothesis SHA256: `{identity.sha256}`",
        "- Ledger status required: `declared_unopened`",
        "- `oos_opened` required: `false`",
        "- A changed hypothesis, wrong hash, duplicate ID, or opened OOS is rejected before analysis.",
        "",
        "## Fixed Observation Semantics",
        "",
        "- Caller supplies preregistered event timestamps; the harness does not detect events or generate signals.",
        "- Event evidence is a completed 15m bar; observation entry is the next contiguous 15m open.",
        f"- Fixed horizons: `{','.join(str(item) for item in HORIZONS)}` completed 15m bars.",
        "- Horizon return uses the corresponding completed bar close.",
        "- Missing, duplicate, unordered, off-grid, same-bar, or cross-IS observations are rejected or right-censored.",
        "",
        "## Fixed Cost Scenarios",
        "",
        "| Scenario | Per-side cost | Round-trip approximation |",
        "|---|---:|---:|",
    ]
    for scenario in CostScenario:
        lines.append(f"| {scenario.label} | {float(scenario.per_side):.2%} | {2 * float(scenario.per_side):.2%} |")
    lines.extend(
        [
            "",
            "Net return is `(exit * (1 - cost)) / (entry * (1 + cost)) - 1`; callers cannot override the four scenarios.",
            "",
            "## Diagnostic Coverage",
            "",
            "- Horizon sample count, mean, median, win rate, sample standard deviation, P5/P95, and Cost x2 net margin.",
            "- MAE, MFE, worst observed path, 24-hour connected clusters, and rolling 24-hour/7-day/30-day event counts.",
            "- Monthly/annualizable frequency inputs, interval-union occupancy, overlap count, concurrency, and longest sleep.",
            "- Full/OOS sample projections use only IS event rate and calendar length; no OOS prices or returns are accepted by the API.",
            "",
            "## Local Golden Structure Smoke",
            "",
            "| Symbol | 15m rows | First open ms | Last open ms | Canonical SHA256 |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for profile in profiles:
        lines.append(
            f"| {profile['symbol']} | {profile['rows']} | {profile['first_open_ms']} | "
            f"{profile['last_open_ms']} | `{profile['canonical_sha256']}` |"
        )
    lines.extend(
        [
            "",
            "The smoke reads ignored T2 golden 15m files only to validate ordering, continuity, OHLC legality, row count, and deterministic hash. Detailed evidence remains under ignored `storage/logs/`.",
            "",
            "## Calendar Sample Budget",
            "",
            "| Item | Value | Gate |",
            "|---|---:|---|",
            f"| Formal full-history days | {FULL_DAYS} | diagnostic |",
            f"| IS days (first 70%) | {IS_DAYS} | diagnostic |",
            f"| Sealed OOS days (last 30%) | {OOS_DAYS} | fail |",
            f"| Required OOS days | {REQUIRED_OOS_DAYS} | fixed |",
            f"| OOS calendar shortage | {shortage} | blocked |",
            f"| Required full-history days at 30% OOS | {REQUIRED_FULL_DAYS} | fixed |",
            "| Earliest projected full-history end | 2028-09-03 | informational |",
            "",
            "T4 can pass as tooling foundation, but the current T5 OOS calendar gate necessarily fails. T5 must run the sample-budget precheck first and stop without lowering the 540-day requirement.",
            "",
            "## Gate",
            "",
            "| Check | Status |",
            "|---|---|",
            "| Trial-ledger identity and SHA256 locked | pass |",
            "| OOS remains unopened | pass |",
            "| Next-open and right-censor semantics implemented | pass |",
            "| Fixed horizons and fixed costs implemented | pass |",
            "| Frequency, clustering, path-risk, occupancy, and budget diagnostics implemented | pass |",
            "| Local T2 golden 15m structural smoke | pass |",
            "| Candidate evaluated | no |",
            "| Current 540-day OOS calendar requirement | fail |",
            "",
            "- T4 harness foundation: pass",
            "- T5 precheck authorized after T4 merge: yes",
            "- T5 calendar gate currently pass: no",
            "- M1D feasibility authorized: no; T5 sample-budget precheck must run first",
            "- M1D strategy code authorized: no",
            "- M2 authorized: no",
            "",
            "T4 passing does not establish candidate feasibility, strategy profitability, or M2 eligibility.",
            "",
        ]
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"report={args.out}")
    print("status=pass candidate_evaluated=no oos_returns_accessed=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
