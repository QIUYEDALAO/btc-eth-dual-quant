#!/usr/bin/env python3
"""Validate the truthful M1H-03 qualification and failed-feasibility record."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))

import yaml

from m1h_paper_protocol_check import EXPECTED_CANDIDATE, EXPECTED_HASH, load, validate


QUALIFICATION_REPORT = ROOT / "reports/m1/M1H_FUNDING_DATA_QUALIFICATION_REPORT.md"
FEASIBILITY_REPORT = ROOT / "reports/m1/M1H_IS_PAPER_FEASIBILITY_REPORT.md"
STATE_PATH = ROOT / "PROJECT_STATE.yaml"
LEDGER_PATH = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
QUEUE_PATH = ROOT / "config/strategy_candidate_queue.json"


def require_markers(path: Path, markers: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [f"{path.name} missing: {marker}" for marker in markers if marker not in text]


def check() -> list[str]:
    failures = validate(load())
    failures += require_markers(QUALIFICATION_REPORT, [
        "- Status: pass",
        "- Funding event scan executed: no",
        "- Funding event count computed: no",
        "- MFE/MAE/recovery computed: no",
        "- Formal strategy returns computed: no",
        "- OOS funding values parsed: no",
        "- OOS spot OHLC parsed: no",
        "- Per-event interval continuity: pass",
        "- M1H-03B authorized in this task: yes",
        "- M2 authorized: no",
    ])
    failures += require_markers(FEASIBILITY_REPORT, [
        "- Status: failed_feasibility",
        "- Formal strategy returns computed: no",
        "- PnL/equity/Sharpe computed: no",
        "- Backtest executed: no",
        "- OOS events/prices/returns accessed: no",
        "- OOS opened: no",
        "- Median 24h MFE: 2.3108%",
        "- Median 24h close displacement: 0.0714%",
        "| combined_median_24h_close_displacement | fail |",
        "| each_symbol_median_24h_close_displacement | fail |",
        "| single_year_concentration | fail |",
        "- M1H Fixed Rule Contract Design authorized next: no",
        "- Strategy code authorized: no",
        "- Backtesting authorized: no",
        "- M2 authorized: no",
    ])

    state = yaml.safe_load(STATE_PATH.read_text(encoding="utf-8"))
    allowed_states = {
        (
            "M1H failed feasibility; BTC/ETH two-asset indicator research stopped",
            "m1h_failed_feasibility_candidate_queue_exhausted_oos_sealed_no_m2",
        ),
        (
            "BTC/ETH candidate queue exhausted; liquid-universe ADR authorized",
            "btc_eth_candidate_queue_exhausted_liquid_universe_adr_authorized_no_m2",
        ),
    }
    if (state.get("current_phase"), state.get("current_status")) not in allowed_states:
        failures.append("PROJECT_STATE is not an allowed M1H terminal governance state")

    ledger = yaml.safe_load(LEDGER_PATH.read_text(encoding="utf-8"))
    candidates = [item for item in ledger.get("candidates", []) if item.get("id") == EXPECTED_CANDIDATE]
    if len(candidates) != 1:
        failures.append("M1H ledger identity must appear exactly once")
    else:
        candidate = candidates[0]
        if candidate.get("sha256") != EXPECTED_HASH or candidate.get("status") != "failed_feasibility":
            failures.append("M1H ledger hash/status changed incorrectly")
        if candidate.get("oos_opened") is not False:
            failures.append("M1H OOS must remain sealed")

    queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    queued = [item for item in queue.get("queue", []) if item.get("candidate_id") == EXPECTED_CANDIDATE]
    if len(queued) != 1 or queued[0].get("status") != "failed_feasibility":
        failures.append("candidate queue must record M1H failed_feasibility")
    if queue.get("stop_policy", {}).get("after_all_three_fail") != "stop_btc_eth_two_asset_indicator_research":
        failures.append("candidate queue terminal stop changed")
    return failures


def main() -> int:
    failures = check()
    if failures:
        print("m1h03_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1h03_check PASS")
    print("qualification=pass paper_feasibility=failed_feasibility oos_opened=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
