from __future__ import annotations

import unittest
import copy
import subprocess
import sys
from decimal import Decimal

from scripts.u04_cross_sectional_data_qualification import utc_ms
from scripts.u04_cross_sectional_paper_observation import FIVE_MINUTES_MS, ONE_DAY_MS
from scripts.u12_cross_sectional_paper_observation import cluster_events, rank_top_quartile, select_events
from scripts.u12_cross_sectional_paper_observation_check import EVIDENCE, EXPECTED_MANIFESTS, RUN, validate
from scripts.u04_cross_sectional_data_qualification import load_json


class U12PaperObservationCoreTests(unittest.TestCase):
    def test_rank_top_quartile_is_deterministic(self):
        values = {f"S{index:02d}": Decimal(index) for index in range(15)}
        self.assertEqual(rank_top_quartile(values), {"S11", "S12", "S13", "S14"})
        tied = {f"S{index:02d}": Decimal(1) for index in range(10)}
        self.assertEqual(rank_top_quartile(tied), {"S00", "S01", "S02"})

    def test_prior_only_calendar_candidate_and_next_expected_open(self):
        start = utc_ms("2020-01-01T00:00:00Z")
        decision = start + 52 * 7 * ONE_DAY_MS
        end = decision + ONE_DAY_MS
        members = tuple(f"S{index:02d}" for index in range(15))
        membership = {}
        day = start
        while day <= decision:
            from scripts.u04_cross_sectional_paper_observation import month_for_ms
            membership[month_for_ms(day)] = members
            day += ONE_DAY_MS
        daily = {}
        common = {}
        for offset in range(52, 0, -1):
            history_day = decision - offset * 7 * ONE_DAY_MS
            daily[history_day] = {symbol: (Decimal("0.0100") if symbol == "S14" else Decimal(0)) for symbol in members}
            common[history_day] = Decimal(0)
        events, accounting = select_events(daily, common, membership, start, end, "p" * 64, "q" * 64)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["symbol"], "S14")
        self.assertEqual(events[0]["decision_time_ms"], decision)
        self.assertEqual(events[0]["reference_open_time_ms"], decision + FIVE_MINUTES_MS)
        self.assertEqual(accounting["history_ineligible"], 0)

    def test_connected_24h_cluster_uses_all_candidates(self):
        rows = [
            {"decision_time_ms": 0, "symbol": "A", "event_id": "a"},
            {"decision_time_ms": ONE_DAY_MS, "symbol": "B", "event_id": "b"},
            {"decision_time_ms": 2 * ONE_DAY_MS, "symbol": "C", "event_id": "c"},
            {"decision_time_ms": 4 * ONE_DAY_MS, "symbol": "D", "event_id": "d"},
        ]
        clustered = cluster_events(rows)
        self.assertEqual([row["symbol"] for row in clustered], ["A", "D"])

    def test_frozen_failed_result_and_tamper_detection(self):
        run = load_json(RUN)
        manifests = {name: load_json(EVIDENCE / f"{name}.json") for name in EXPECTED_MANIFESTS}
        self.assertEqual(validate(run, manifests), [])
        changed = copy.deepcopy(run)
        changed["metrics"]["complete_is_independent_episodes"] = 90
        self.assertTrue(validate(changed, manifests))
        changed = copy.deepcopy(run)
        changed["authorizations"]["paper_result_independent_review"] = True
        self.assertTrue(validate(changed, manifests))

    def test_second_result_run_is_locked(self):
        completed = subprocess.run([sys.executable, "scripts/u12_cross_sectional_paper_observation.py"], cwd=EVIDENCE.parents[3], text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("second result-bearing run is prohibited", completed.stderr)


if __name__ == "__main__":
    unittest.main()
