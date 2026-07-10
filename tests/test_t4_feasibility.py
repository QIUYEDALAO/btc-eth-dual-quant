from __future__ import annotations

import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import yaml

from btc_eth_dual_quant.audit.feasibility import (
    BAR_MS,
    DAY_MS,
    HORIZONS,
    CostScenario,
    EventReference,
    ISWindow,
    build_feasibility_summary,
    cluster_diagnostics,
    net_return,
    observe_event,
    occupancy_diagnostics,
    profile_golden_15m,
    project_sample_budget,
    validate_candidate_identity,
)


ROOT = Path(__file__).resolve().parents[1]
HYPOTHESIS = (
    "M1D-15M-DISCRETE-DISLOCATION: BTC/USDT and ETH/USDT spot; completed 15m candles identify "
    "discrete large-price-dislocation events; enter no earlier than the next 15m open; 1m data is "
    "execution detail only; no shorting or leverage."
)
DIGEST = hashlib.sha256(HYPOTHESIS.encode("utf-8")).hexdigest()


def ledger(candidate: dict | None = None) -> dict:
    item = candidate or {
        "id": "M1D-15M-DISCRETE-DISLOCATION",
        "status": "declared_unopened",
        "hypothesis": HYPOTHESIS,
        "sha256": DIGEST,
        "oos_opened": False,
    }
    return {"version": 1, "hash_algorithm": "sha256", "candidates": [item]}


def bar(index: int, *, base: float = 100.0) -> dict:
    opened = base + index
    return {
        "open_time": index * BAR_MS,
        "close_time": (index + 1) * BAR_MS - 1,
        "open": str(opened),
        "high": str(opened + 2),
        "low": str(opened - 2),
        "close": str(opened + 1),
    }


def observation(event_index: int = 0, *, window_end_bars: int = 40):
    bars = [bar(index) for index in range(40)]
    reference = EventReference("M1D-15M-DISCRETE-DISLOCATION", "BTCUSDT", bars[event_index]["close_time"])
    return observe_event(reference, bars=bars, is_window=ISWindow(0, window_end_bars * BAR_MS))


class LedgerIdentityTests(unittest.TestCase):
    def validate(self, payload: dict):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.yaml"
            path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
            return validate_candidate_identity(
                path,
                candidate_id="M1D-15M-DISCRETE-DISLOCATION",
                expected_hypothesis=HYPOTHESIS,
                expected_sha256=DIGEST,
            )

    def test_exact_unopened_identity_passes(self) -> None:
        identity = self.validate(ledger())
        self.assertEqual(identity.sha256, DIGEST)
        self.assertFalse(identity.oos_opened)

    def test_changed_hypothesis_or_hash_is_rejected(self) -> None:
        changed = ledger()["candidates"][0]
        changed["hypothesis"] += " changed"
        with self.assertRaisesRegex(ValueError, "hypothesis or hash"):
            self.validate(ledger(changed))

    def test_oos_opened_and_duplicate_id_are_rejected(self) -> None:
        opened = dict(ledger()["candidates"][0], oos_opened=True)
        with self.assertRaisesRegex(ValueError, "OOS is open"):
            self.validate(ledger(opened))
        duplicate = ledger()
        duplicate["candidates"].append(dict(duplicate["candidates"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate candidate IDs"):
            self.validate(duplicate)


class EventSemanticsTests(unittest.TestCase):
    def test_golden_structure_profile_is_repeatable(self) -> None:
        rows = [bar(index) for index in range(30)]
        first = profile_golden_15m(rows)
        second = profile_golden_15m(rows)
        self.assertEqual(first.rows, 30)
        self.assertEqual(first.first_open_ms, 0)
        self.assertEqual(first.last_open_ms, 29 * BAR_MS)
        self.assertEqual(first.canonical_sha256, second.canonical_sha256)

    def test_next_open_and_all_fixed_horizons(self) -> None:
        result = observation()
        self.assertEqual(result.entry_open_ms, BAR_MS)
        self.assertEqual(tuple(item.horizon_bars for item in result.horizons), HORIZONS)
        self.assertEqual(result.horizons[0].exit_close_ms, 2 * BAR_MS - 1)
        self.assertEqual(result.horizons[-1].exit_close_ms, 25 * BAR_MS - 1)
        self.assertEqual(result.right_censored_horizons, ())

    def test_cross_is_horizons_are_right_censored_without_future_rows(self) -> None:
        result = observation(event_index=10, window_end_bars=20)
        self.assertEqual(tuple(item.horizon_bars for item in result.horizons), (1, 2, 4, 8))
        self.assertEqual(result.right_censored_horizons, (12, 24))

    def test_missing_unsorted_duplicate_and_same_bar_event_are_rejected(self) -> None:
        rows = [bar(index) for index in range(30)]
        reference = EventReference("C", "BTCUSDT", rows[0]["close_time"])
        with self.assertRaisesRegex(ValueError, "contiguous"):
            observe_event(reference, bars=rows[:5] + rows[6:], is_window=ISWindow(0, 30 * BAR_MS))
        with self.assertRaisesRegex(ValueError, "sorted"):
            observe_event(reference, bars=[rows[1], rows[0], *rows[2:]], is_window=ISWindow(0, 30 * BAR_MS))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            observe_event(reference, bars=[rows[0], rows[0], *rows[1:]], is_window=ISWindow(0, 30 * BAR_MS))
        same_bar = EventReference("C", "BTCUSDT", rows[0]["open_time"])
        with self.assertRaisesRegex(ValueError, "completed 15m bar"):
            observe_event(same_bar, bars=rows, is_window=ISWindow(0, 30 * BAR_MS))

    def test_cost_scenarios_are_fixed_and_monotonic(self) -> None:
        values = [net_return(100, 102, scenario) for scenario in CostScenario]
        self.assertEqual([scenario.label for scenario in CostScenario], ["base", "cost_x2", "event_stress_a", "event_stress_b"])
        self.assertTrue(all(left > right for left, right in zip(values, values[1:])))
        self.assertAlmostEqual(values[0], 102 * 0.9985 / (100 * 1.0015) - 1)

    def test_observation_hash_is_repeatable(self) -> None:
        self.assertEqual(observation().input_sha256, observation().input_sha256)


class DiagnosticsTests(unittest.TestCase):
    def test_clustering_occupancy_and_summary_are_deterministic(self) -> None:
        first = observation(event_index=0)
        second = observation(event_index=4)
        third = observation(event_index=39 - 25)
        window = ISWindow(0, 40 * BAR_MS)
        clustered = cluster_diagnostics([first, second, third], window)
        self.assertEqual(clustered.events, 3)
        self.assertGreaterEqual(clustered.max_events_rolling_24h, 2)
        self.assertEqual(clustered.events_by_utc_month, (("1970-01", 3),))
        occupied = occupancy_diagnostics([first, second], window)
        h24 = next(item for item in occupied if item.horizon_bars == 24)
        self.assertEqual(h24.overlapping_events, 1)
        self.assertEqual(h24.max_concurrent_events, 2)
        summary_a = build_feasibility_summary([third, first, second], is_window=window, full_days=1004, oos_days=302)
        summary_b = build_feasibility_summary([first, second, third], is_window=window, full_days=1004, oos_days=302)
        self.assertEqual(summary_a.canonical_sha256, summary_b.canonical_sha256)

    def test_sample_budget_records_current_calendar_blocker(self) -> None:
        budget = project_sample_budget(observed_events=20, is_days=702, full_days=1004, oos_days=302)
        self.assertFalse(budget.oos_calendar_gate)
        self.assertEqual(budget.required_oos_days, 540)
        self.assertEqual(budget.oos_days, 302)

    def test_api_has_no_oos_return_input_or_strategy_logic(self) -> None:
        source = (ROOT / "src/btc_eth_dual_quant/audit/feasibility.py").read_text(encoding="utf-8")
        for forbidden in (
            "oos_returns",
            "populate_entry",
            "populate_exit",
            "create_order",
            "cancel_order",
            "place_order",
            "execution/live",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
