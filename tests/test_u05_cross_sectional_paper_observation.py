from __future__ import annotations

import unittest
from copy import deepcopy
from decimal import Decimal

from scripts.u05_cross_sectional_paper_observation import (
    FOUR_HOURS_MS,
    ONE_HOUR_MS,
    cluster_events,
    evaluate_gates,
    observe_paths,
    select_events,
)
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u05_cross_sectional_paper_observation_check import EVIDENCE, REPORT, validate
from scripts.u04_cross_sectional_data_qualification import load_json


class U05CrossSectionalPaperObservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = git_json("8d8652796e22a15285ba682b4524baa0218ca5a6", "config/u05_cross_sectional_paper_protocol_v1.json")

    def _hourly(self, returns: list[Decimal]) -> tuple[dict, dict]:
        symbols = [f"S{i:02d}" for i in range(len(returns))]
        decision = 8 * ONE_HOUR_MS
        hourly = {}
        for symbol, value in zip(symbols, returns):
            closes = {decision - offset * ONE_HOUR_MS: Decimal("100") for offset in range(8)}
            closes[decision] = Decimal("100") * (Decimal(1) + value)
            hourly[symbol] = closes
        return hourly, {"1970-01": tuple(symbols)}

    def test_event_accepts_exact_twelve_of_fifteen_and_common_move(self) -> None:
        hourly, membership = self._hourly([Decimal("0.02")] * 12 + [Decimal("-0.01")] * 3)
        events, accounting = select_events(
            hourly_closes=hourly, membership=membership, is_start_ms=0,
            is_end_ms=8 * ONE_HOUR_MS, protocol_hash="p", qualification_hash="q",
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["positive_member_count"], 12)
        self.assertEqual(accounting["decision_times_evaluated"], 1)

    def test_event_rejects_breadth_common_move_or_missing_constituent(self) -> None:
        cases = [
            [Decimal("0.02")] * 11 + [Decimal("-0.01")] * 4,
            [Decimal("0.01")] * 15,
        ]
        for values in cases:
            hourly, membership = self._hourly(values)
            events, _ = select_events(hourly_closes=hourly, membership=membership, is_start_ms=0, is_end_ms=8 * ONE_HOUR_MS, protocol_hash="p", qualification_hash="q")
            self.assertEqual(events, [])
        hourly, membership = self._hourly([Decimal("0.02")] * 15)
        del hourly["S00"][7 * ONE_HOUR_MS]
        events, accounting = select_events(hourly_closes=hourly, membership=membership, is_start_ms=0, is_end_ms=8 * ONE_HOUR_MS, protocol_hash="p", qualification_hash="q")
        self.assertEqual(events, [])
        self.assertEqual(accounting["cross_section_ineligible"], 1)

    def test_connected_24h_cluster_keeps_first_and_chains(self) -> None:
        events = []
        for index, hour in enumerate((0, 24, 48, 73)):
            events.append({"decision_time_ms": hour * ONE_HOUR_MS, "event_id": str(index)})
        representatives = cluster_events(events)
        self.assertEqual([row["event_id"] for row in representatives], ["0", "3"])

    def test_path_uses_member_median_positive_fraction_and_base_recovery(self) -> None:
        reference = 0
        symbols = ["A", "B", "C"]
        episode = {"episode_id": "ep", "event_id": "ev", "decision_time_ms": -1, "reference_open_time_ms": reference, "active_members": symbols}
        captured = {}
        for index in range(288):
            opened = index * 300_000
            for number, symbol in enumerate(symbols):
                start = Decimal("100")
                close = start * (Decimal(1) + Decimal(index + number) / Decimal("10000"))
                captured[(symbol, opened)] = (start, close, close, close)
        paths, censored = observe_paths([episode], captured, {})
        self.assertEqual(censored, {})
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0]["positive_member_fraction"]["24"], "1")
        self.assertIsNotNone(paths[0]["first_base_cost_recovery_minutes"])

    def test_frozen_gates_fail_without_mutation(self) -> None:
        paths = []
        metrics, checks = evaluate_gates(paths, self.protocol, mismatch_count=0)
        self.assertFalse(all(checks.values()))
        self.assertEqual(metrics["complete_is_independent_episodes"], 0)
        self.assertEqual(self.protocol["paper_gates"]["complete_is_independent_episodes_minimum"], 90)

    def test_committed_failed_result_is_exact_and_tamper_fails(self) -> None:
        summary = load_json(EVIDENCE / "run_manifest.json")
        manifests = {name: load_json(EVIDENCE / f"{name}.json") for name in ("accounting", "episodes", "events", "paths")}
        report = REPORT.read_text(encoding="utf-8")
        self.assertEqual(validate(summary, manifests, report), [])
        changed = deepcopy(summary)
        changed["metrics"]["complete_is_independent_episodes"] += 1
        self.assertIn("run content hash drift", validate(changed, manifests, report))
        changed = deepcopy(summary)
        changed["authorizations"]["backtesting"] = True
        failures = validate(changed, manifests, report)
        self.assertIn("failed result authorizes downstream work", failures)
        changed_manifests = deepcopy(manifests)
        changed_manifests["paths"]["content"][0]["common_demand_close_displacement"]["24"] = "1"
        self.assertIn("manifest hash drift: paths", validate(summary, changed_manifests, report))


if __name__ == "__main__":
    unittest.main()
