import copy
from pathlib import Path
import unittest

import yaml

from scripts.project_state_transition_check import validate

ROOT = Path(__file__).resolve().parents[1]


class LiquidUniverseStateMachineTests(unittest.TestCase):
    def test_repository_state_passes(self):
        state = yaml.safe_load((ROOT / "PROJECT_STATE.yaml").read_text())
        self.assertEqual(validate(state), [])

    def test_authorization_or_unknown_transition_fails(self):
        state = yaml.safe_load((ROOT / "PROJECT_STATE.yaml").read_text())
        changed = copy.deepcopy(state)
        changed["research_authorizations"]["strategy_code"] = True
        self.assertTrue(validate(changed))
        changed = copy.deepcopy(state)
        changed["current_status"] = "handwritten-pass"
        self.assertTrue(validate(changed))

    def test_adr0014_review_closeout_requires_draft_revision_and_zero_authority(self):
        state = yaml.safe_load((ROOT / "PROJECT_STATE.yaml").read_text())
        self.assertEqual(validate(state), [])

        draft = next(item for item in state["open_work"] if item.get("id") == "ADR-0014-DRAFT")
        self.assertEqual(draft["status"], "draft_revision_authorized_not_started")
        self.assertFalse(draft["adopted"])
        self.assertFalse(any(item.get("id") == "ADR-0014-REVIEW" for item in state["open_work"]))
        review = next(
            item
            for item in state["completed_milestones"]
            if item.get("phase") == "ADR-0014 independent policy review"
        )
        self.assertEqual(review["merged_pr"], 82)
        self.assertEqual(
            review["merge_commit"],
            "d507684564fc31812c8e7d4adb06d7ab61c7dab7",
        )

        changed = copy.deepcopy(state)
        changed["open_work"] = [
            item for item in changed["open_work"] if item.get("id") != "ADR-0014-DRAFT"
        ]
        self.assertIn(
            "current V2 task missing from open_work: ADR-0014-DRAFT",
            validate(changed),
        )

        changed = copy.deepcopy(state)
        changed["research_authorizations"]["backtesting"] = True
        self.assertIn("research authorization matrix changed", validate(changed))

    def test_merged_blocked_requalification_requires_closed_milestone(self):
        state = yaml.safe_load((ROOT / "PROJECT_STATE.yaml").read_text())
        state["current_phase"] = "Liquid universe V2 public requalification blocked"
        state["current_status"] = "liquid_universe_v2_requalification_blocked_data_conflict_no_strategy_no_m2"
        state["open_work"] = [
            item for item in state["open_work"] if item.get("id") != "U-03E-ADJ"
        ]
        changed = copy.deepcopy(state)
        changed["completed_milestones"] = [
            item
            for item in changed["completed_milestones"]
            if item.get("phase") != "Liquid universe V2 public requalification"
        ]
        self.assertIn("merged blocked U-03E milestone missing", validate(changed))

        changed = copy.deepcopy(state)
        changed["open_work"].append(
            {"id": "U-03E", "status": "blocked_data_conflict", "pr": 71}
        )
        failures = validate(changed)
        self.assertIn("merged blocked U-03E must not remain in open_work", failures)
        self.assertIn("open_work references merged PR #71", failures)


if __name__ == "__main__":
    unittest.main()
