from __future__ import annotations

import unittest
from copy import deepcopy
from decimal import Decimal

from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u07_cross_sectional_paper_observation_check import (
    EVIDENCE,
    MANIFEST_HASHES,
    REPORT,
    validate,
)
from scripts.u07_cross_sectional_paper_observation import (
    FOUR_HOURS_MS,
    ONE_HOUR_MS,
    cluster_events,
    evaluate_gates,
    observe_paths,
    select_events,
)


class U07CrossSectionalPaperObservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = git_json(
            "3aed4c337ff984b3e07ad9a4c7cda898425b3791",
            "config/u07_cross_sectional_paper_protocol_v1.json",
        )

    def _hourly(self, returns: list[Decimal]) -> tuple[dict, dict]:
        symbols = [f"S{index:02d}" for index in range(len(returns))]
        decision = 2 * FOUR_HOURS_MS
        hourly = {}
        for symbol, value in zip(symbols, returns):
            closes = {decision - offset * ONE_HOUR_MS: Decimal("100") for offset in range(8)}
            closes[decision] = Decimal("100") * (Decimal(1) + value)
            hourly[symbol] = closes
        return hourly, {"1970-01": tuple(symbols)}

    def test_event_accepts_exact_stress_breadth_and_resilience(self) -> None:
        returns = [Decimal("-0.03")] * 14 + [Decimal("-0.004")]
        hourly, membership = self._hourly(returns)
        events, accounting = select_events(
            hourly_closes=hourly, membership=membership, is_start_ms=0,
            is_end_ms=2 * FOUR_HOURS_MS, protocol_hash="p", qualification_hash="q",
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["symbol"], "S14")
        self.assertEqual(events[0]["negative_member_count"], 15)
        self.assertEqual(accounting["decision_times_evaluated"], 1)

    def test_event_rejects_weak_stress_breadth_resilience_or_missing_data(self) -> None:
        cases = [
            [Decimal("-0.02")] * 14 + [Decimal("0")],
            [Decimal("-0.03")] * 11 + [Decimal("0.01")] * 4,
            [Decimal("-0.03")] * 15,
        ]
        for values in cases:
            hourly, membership = self._hourly(values)
            events, _ = select_events(
                hourly_closes=hourly, membership=membership, is_start_ms=0,
                is_end_ms=2 * FOUR_HOURS_MS, protocol_hash="p", qualification_hash="q",
            )
            self.assertEqual(events, [])
        hourly, membership = self._hourly([Decimal("-0.03")] * 14 + [Decimal("-0.004")])
        del hourly["S00"][7 * ONE_HOUR_MS]
        events, accounting = select_events(
            hourly_closes=hourly, membership=membership, is_start_ms=0,
            is_end_ms=2 * FOUR_HOURS_MS, protocol_hash="p", qualification_hash="q",
        )
        self.assertEqual(events, [])
        self.assertEqual(accounting["cross_section_ineligible"], 1)

    def test_winner_tie_break_and_connected_48h_cluster(self) -> None:
        hourly, membership = self._hourly(
            [Decimal("-0.03")] * 13 + [Decimal("-0.004"), Decimal("-0.004")]
        )
        events, accounting = select_events(
            hourly_closes=hourly, membership=membership, is_start_ms=0,
            is_end_ms=2 * FOUR_HOURS_MS, protocol_hash="p", qualification_hash="q",
        )
        self.assertEqual(events[0]["symbol"], "S13")
        self.assertEqual(accounting["simultaneous_candidates_discarded"], 1)
        candidates = [
            {"decision_time_ms": hour * ONE_HOUR_MS, "event_id": str(index)}
            for index, hour in enumerate((0, 48, 96, 145))
        ]
        self.assertEqual([row["event_id"] for row in cluster_events(candidates)], ["0", "3"])

    def test_path_uses_candidate_and_fixed_peer_median(self) -> None:
        episode = {
            "episode_id": "ep", "event_id": "ev", "symbol": "A",
            "decision_time_ms": -1, "reference_open_time_ms": 0,
            "active_members": ["A", "B", "C"],
        }
        captured = {}
        for index in range(576):
            opened = index * 300_000
            for symbol, multiplier in (("A", 2), ("B", 1), ("C", 1)):
                close = Decimal("100") * (Decimal(1) + Decimal(index * multiplier) / Decimal("100000"))
                captured[(symbol, opened)] = (Decimal("100"), close, close, close)
        paths, censored = observe_paths([episode], captured, {})
        self.assertEqual(censored, {})
        self.assertEqual(len(paths), 1)
        self.assertGreater(Decimal(paths[0]["relative_continuation"]["24"]), 0)
        self.assertEqual(paths[0]["peer_count"], 2)

    def test_empty_paths_fail_frozen_gates_without_mutation(self) -> None:
        metrics, checks = evaluate_gates([], self.protocol, mismatch_count=0)
        self.assertFalse(all(checks.values()))
        self.assertEqual(metrics["complete_is_independent_episodes"], 0)
        self.assertEqual(self.protocol["paper_gates"]["complete_is_independent_episodes_minimum"], 60)

    def test_committed_failed_result_is_exact_and_tamper_fails(self) -> None:
        summary = load_json(EVIDENCE / "run_manifest.json")
        manifests = {name: load_json(EVIDENCE / f"{name}.json") for name in MANIFEST_HASHES}
        report = REPORT.read_text(encoding="utf-8")
        self.assertEqual(validate(summary, manifests, report), [])
        changed = deepcopy(summary)
        changed["metrics"]["complete_is_independent_episodes"] += 1
        self.assertIn("run content hash drift", validate(changed, manifests, report))
        changed = deepcopy(summary)
        changed["authorizations"]["backtesting"] = True
        self.assertIn("isolation or downstream authorization changed", validate(changed, manifests, report))
        changed_manifests = deepcopy(manifests)
        changed_manifests["paths"]["content"][0]["relative_continuation"]["24"] = "1"
        self.assertIn("manifest hash drift: paths", validate(summary, changed_manifests, report))


if __name__ == "__main__":
    unittest.main()
