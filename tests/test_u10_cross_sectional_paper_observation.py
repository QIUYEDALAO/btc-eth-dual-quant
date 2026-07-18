from __future__ import annotations

import unittest
import copy
from decimal import Decimal

from scripts.u04_cross_sectional_paper_observation import ONE_DAY_MS
from scripts.u04_cross_sectional_data_qualification import utc_ms
from scripts.u10_cross_sectional_paper_observation import (
    PATH_MS,
    cluster_events,
    descending_scores,
    evaluate_gates,
    select_events,
)
from scripts.u10_cross_sectional_paper_observation_check import EVIDENCE, REPORT, validate
from scripts.u04_cross_sectional_data_qualification import load_json


class U10PaperObservationTests(unittest.TestCase):
    def test_frozen_result_and_tamper_detection(self):
        summary = load_json(EVIDENCE / "run_manifest.json")
        manifests = {name: load_json(EVIDENCE / f"{name}.json") for name in ("accounting", "episodes", "events", "paths")}
        self.assertEqual(validate(summary, manifests, REPORT.read_text()), [])
        changed = copy.deepcopy(summary)
        changed["metrics"]["complete_is_independent_episodes"] = 90
        self.assertTrue(validate(changed, manifests, REPORT.read_text()))
        changed = copy.deepcopy(summary)
        changed["authorizations"]["backtesting"] = True
        self.assertTrue(validate(changed, manifests, REPORT.read_text()))

    def test_descending_scores_are_deterministic(self):
        values = {"B": Decimal("2"), "A": Decimal("2"), "C": Decimal("1")}
        self.assertEqual(descending_scores(values), {"A": 3, "B": 2, "C": 1})

    def test_joint_price_volume_candidate(self):
        symbols = tuple(f"S{i:02d}" for i in range(12))
        membership = {"2020-01": symbols, "2020-02": symbols}
        daily = {symbol: {} for symbol in symbols}
        start = utc_ms("2020-01-01T00:00:00Z")
        decision = start + 28 * ONE_DAY_MS
        for index, symbol in enumerate(symbols):
            for day_index in range(29):
                day = start + day_index * ONE_DAY_MS
                close = Decimal("100")
                quote = Decimal("100")
                if symbol == "S00" and day_index == 28:
                    close = Decimal("104")
                if symbol == "S00" and day_index >= 26:
                    quote = Decimal("200")
                daily[symbol][day] = {"open": close, "close": close, "quote": quote}
        events, accounting = select_events(daily, membership, start, decision + ONE_DAY_MS, "p", "q")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["symbol"], "S00")
        self.assertGreaterEqual(Decimal(events[0]["candidate_relative_trend"]), Decimal("0.0300"))
        self.assertGreaterEqual(Decimal(events[0]["candidate_volume_share_ratio"]), Decimal("1.25"))
        self.assertEqual(accounting["joint_candidate_days"], 1)

    def test_missing_history_fails_closed(self):
        symbols = tuple(f"S{i:02d}" for i in range(10))
        membership = {"1970-01": symbols}
        daily = {symbol: {} for symbol in symbols}
        events, accounting = select_events(daily, membership, 0, ONE_DAY_MS, "p", "q")
        self.assertEqual(events, [])
        self.assertEqual(accounting["cross_section_ineligible"], 1)

    def test_connected_clustering_uses_all_candidates(self):
        base = {"symbol": "A", "active_members": ["A", "B"], "reference_open_time_ms": 1}
        events = []
        for index, decision in enumerate((0, PATH_MS, 2 * PATH_MS, 3 * PATH_MS + 1)):
            events.append({**base, "decision_time_ms": decision, "event_id": str(index)})
        episodes = cluster_events(events)
        self.assertEqual([row["event_id"] for row in episodes], ["0", "3"])

    def test_gates_use_frozen_72h_fields(self):
        protocol = {
            "scope": {"full_calendar_days": 2373, "is_calendar_days": 1715, "oos_calendar_days": 658},
            "paper_gates": {
                "complete_is_independent_episodes_minimum": 1,
                "projected_full_independent_episodes_minimum": 1,
                "projected_sealed_oos_independent_episodes_minimum": 0,
                "minimum_years_with_twelve_complete_episodes": 0,
                "maximum_single_year_episode_share": "1",
                "maximum_single_symbol_episode_share": "1",
                "minimum_distinct_event_symbols": 1,
                "minimum_distinct_event_months": 1,
                "combined_median_72h_relative_continuation_minimum": "0.0180",
                "combined_median_72h_candidate_absolute_close_displacement_minimum": "0.0180",
                "fraction_complete_episodes_with_positive_72h_relative_continuation_minimum": "0.60",
                "qualification_quarantine_lifecycle_or_order_mismatches_maximum": 0,
            },
        }
        path = {
            "decision_time_ms": 1577836800000,
            "symbol": "A",
            "relative_continuation": {"72": "0.020"},
            "candidate_absolute_close_displacement": {"72": "0.030"},
        }
        metrics, checks = evaluate_gates([path], protocol, 0)
        self.assertEqual(Decimal(metrics["median_72h_relative_continuation"]), Decimal("0.02"))
        self.assertTrue(all(checks.values()))
        _, mismatch_checks = evaluate_gates([path], protocol, 1)
        self.assertFalse(mismatch_checks["authority_and_order_mismatches"])


if __name__ == "__main__":
    unittest.main()
