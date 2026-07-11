#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "config/m1e_is_paper_protocol.json"
REPORT = ROOT / "reports/m1/M1E_IS_PAPER_FEASIBILITY_REPORT.md"


def validate(protocol: dict) -> list[str]:
    failures: list[str] = []
    event = protocol.get("diagnostic_event", {})
    observation = protocol.get("observation", {})
    gates = protocol.get("paper_gates", {})
    expected_event = {
        "compression_window_bars": 24,
        "compression_reference_bars": 4320,
        "compression_quantile": "0.20",
        "compression_quantile_interpolation": "linear",
        "breakout_lookback_bars": 24,
        "expansion_true_range_multiple": "2.0",
        "minimum_segment_age_bars": 4345,
        "cluster_window_hours": 24,
        "cluster_representative": "first_event_only",
        "four_hour_filter_used": False,
        "volume_used": False,
    }
    if event != expected_event:
        failures.append("diagnostic event protocol changed after freeze")
    if observation.get("fixed_horizon_bars") != [1, 2, 4, 8, 12, 24] or observation.get("entry_fill_model_used") is not False or observation.get("position_or_exit_model_used") is not False:
        failures.append("observation protocol changed")
    expected_gates = {
        "projected_full_events_minimum": 120,
        "projected_oos_events_minimum": 30,
        "median_24h_mfe_minimum": "0.0180",
        "each_symbol_complete_events_minimum": 20,
        "each_symbol_median_24h_mfe_minimum": "0.0180",
        "minimum_years_with_ten_events": 3,
        "maximum_single_year_event_share": "0.45",
        "events_in_quarantine_or_unrewarmed_segments_maximum": 0,
    }
    if gates != expected_gates:
        failures.append("paper Gate changed after freeze")
    auth = protocol.get("authorization", {})
    if auth.get("paper_diagnostic_run") is not True or any(auth.get(key) is not False for key in ("fixed_rule_contract", "strategy_code", "freqtrade_backtesting", "oos_access", "m2")):
        failures.append("downstream authorization changed")
    return failures


def main() -> int:
    failures = validate(json.loads(PROTOCOL.read_text(encoding="utf-8")))
    report = REPORT.read_text(encoding="utf-8")
    for marker in (
        "- Status: failed_feasibility",
        "- Formal strategy returns computed: no",
        "- OOS prices/returns accessed: no",
        "- OOS opened: no",
        "| combined_median_mfe | fail |",
        "| each_symbol_median_mfe | fail |",
        "- M1E-07 fixed rule contract authorized: no",
    ):
        if marker not in report:
            failures.append(f"report marker missing: {marker}")
    if failures:
        print("m1e_paper_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1e_paper_check PASS")
    print("status=failed_feasibility next_candidate=M1G oos_opened=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
