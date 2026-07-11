from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("candidate_queue_check", ROOT / "scripts/candidate_queue_check.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class CandidateQueueGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.queue = MODULE.load(MODULE.QUEUE_PATH)
        self.ledger = MODULE.load(MODULE.LEDGER_PATH)

    def test_repository_queue_and_trial_count_pass(self) -> None:
        self.assertEqual(MODULE.validate(self.queue, self.ledger), [])

    def test_order_alias_or_transition_change_fails(self) -> None:
        for key, value in (("alias", "M1X"), ("failure_transition", "M1E"), ("order", 9)):
            changed = copy.deepcopy(self.queue)
            changed["queue"][1][key] = value
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate(changed, self.ledger))

    def test_only_three_historical_trials_are_opened(self) -> None:
        changed = copy.deepcopy(self.ledger)
        next(item for item in changed["candidates"] if item["id"] == "M1E-1H-TREND-BREAKOUT")["oos_opened"] = True
        self.assertTrue(MODULE.validate(self.queue, changed))
        changed = copy.deepcopy(self.ledger)
        next(item for item in changed["candidates"] if item["id"] == "M1A-DAILY-TREND")["oos_opened"] = False
        self.assertTrue(MODULE.validate(self.queue, changed))

    def test_cost_sample_and_numerical_gates_cannot_be_lowered(self) -> None:
        paths = (
            ("costs_per_side", "cost_x2", "0.0020"),
            ("paper_feasibility", "projected_full_trades_minimum", 80),
            ("numerical_gates", "oos_daily_mtm_psr_minimum", "0.90"),
            ("numerical_gates", "daily_mtm_max_drawdown_maximum", "0.20"),
        )
        for section, key, value in paths:
            changed = copy.deepcopy(self.queue)
            changed["common_policy"][section][key] = value
            with self.subTest(section=section, key=key):
                self.assertTrue(MODULE.validate(changed, self.ledger))

    def test_no_downstream_authorization_can_be_enabled(self) -> None:
        for key in self.queue["authorization"]:
            changed = copy.deepcopy(self.queue)
            changed["authorization"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate(changed, self.ledger))

    def test_m1h_reuses_existing_hypothesis_and_m1g_is_unopened(self) -> None:
        by_alias = {item["alias"]: item for item in self.queue["queue"]}
        self.assertEqual(by_alias["M1H"]["candidate_id"], "FUNDING-EXTREME-SPOT-CONTRARIAN")
        candidates = {item["id"]: item for item in self.ledger["candidates"]}
        self.assertFalse(candidates[by_alias["M1H"]["candidate_id"]]["oos_opened"])
        self.assertFalse(candidates[by_alias["M1G"]["candidate_id"]]["oos_opened"])


if __name__ == "__main__":
    unittest.main()
