#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "config" / "m1g_is_paper_protocol.json"


def load(path: Path = PROTOCOL_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(protocol: dict) -> list[str]:
    failures: list[str] = []
    expected = {
        "version": 1,
        "protocol_id": "M1G-02-PANIC-DISLOCATION-PAPER-V1",
        "candidate_id": "M1G-1H-PANIC-DISLOCATION-MEAN-REVERSION",
        "hypothesis_sha256": "288d3c37b577f6523890155b3ab4e31e4150fea876e8c66bf5c0c69403c4f2fc",
    }
    for key, value in expected.items():
        if protocol.get(key) != value:
            failures.append(f"{key} changed")
    if protocol.get("scope") != {
        "symbols": ["BTCUSDT", "ETHUSDT"], "timeframe": "1h",
        "is_start": "2020-07-01T00:00:00Z", "is_end_exclusive": "2024-09-11T00:00:00Z",
        "oos_opened": False, "formal_strategy_return_permitted": False,
    }:
        failures.append("scope or OOS seal changed")
    if protocol.get("diagnostic_event") != {
        "close_return_maximum": "-0.0240", "reference_window_bars": 168,
        "absolute_return_multiple_minimum": "3.0", "true_range_multiple_minimum": "2.5",
        "close_location_maximum": "0.25", "reference_statistics": "prior_window_median_only",
        "minimum_segment_age_bars": 169, "cluster_window_hours": 24,
        "cluster_representative": "first_event_only", "four_hour_filter_used": False,
        "volume_used": False,
    }:
        failures.append("diagnostic event changed after freeze")
    observation = protocol.get("observation", {})
    if observation.get("fixed_horizon_bars") != [1, 2, 4, 8, 12, 24] or observation.get("path_horizon_bars") != 24:
        failures.append("observation horizons changed")
    if observation.get("entry_fill_model_used") is not False or observation.get("position_or_exit_model_used") is not False:
        failures.append("protocol must not introduce fills or positions")
    if protocol.get("paper_gates") != {
        "projected_full_events_minimum": 120, "projected_oos_events_minimum": 30,
        "median_24h_mfe_minimum": "0.0180", "each_symbol_complete_events_minimum": 20,
        "each_symbol_median_24h_mfe_minimum": "0.0180", "minimum_years_with_ten_events": 3,
        "maximum_single_year_event_share": "0.45",
        "events_in_quarantine_or_unrewarmed_segments_maximum": 0,
    }:
        failures.append("paper Gates changed")
    if protocol.get("projection_calendar_days") != {"is": 1533, "full": 2191, "oos": 658}:
        failures.append("projection calendar changed")
    if protocol.get("authorization") != {
        "paper_protocol_frozen": True, "paper_diagnostic_run": False,
        "fixed_rule_contract": False, "strategy_code": False,
        "freqtrade_backtesting": False, "oos_access": False, "m2": False,
    }:
        failures.append("protocol task authorization changed")
    return failures


def main() -> int:
    failures = validate(load())
    if failures:
        print("m1g_paper_protocol_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1g_paper_protocol_check PASS")
    print("event_scan_executed=no oos_opened=no authorized_next=separate_is_paper_run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
