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

    def test_u03f_failed_audit_is_closed_and_v4_is_audit_blocked(self):
        state = yaml.safe_load((ROOT / "PROJECT_STATE.yaml").read_text())
        self.assertEqual(validate(state), [])

        self.assertFalse(any(item.get("id") == "U-03E-V4-RUN" for item in state["open_work"]))
        self.assertFalse(any(item.get("id") == "U-03F" for item in state["open_work"]))
        audit = next(
            item
            for item in state["completed_milestones"]
            if item.get("phase") == "U-03F V4 independent audit"
        )
        self.assertEqual(audit["status"], "failed_audit")
        self.assertEqual(audit["merged_pr"], 95)
        self.assertEqual(audit["critical_findings"], 1)
        self.assertEqual(audit["high_findings"], 7)
        requalification = next(
            item
            for item in state["completed_milestones"]
            if item.get("phase") == "Liquid universe V4 fixed-range public requalification"
        )
        self.assertEqual(
            requalification["status"],
            "pass_revalidation_required_after_failed_independent_audit",
        )
        self.assertEqual(requalification["qualification_authority"], "audit_blocked")
        self.assertEqual(requalification["audit_status"], "failed_audit")
        self.assertEqual(requalification["merged_pr"], 89)
        self.assertEqual(
            requalification["merge_commit"],
            "77cb0969980978e65f3560f38f50924c73dfee6e",
        )
        self.assertFalse(any(item.get("id") == "ADR-0014-ADOPT" for item in state["open_work"]))
        self.assertFalse(any(item.get("id") == "ADR-0014-REVIEW" for item in state["open_work"]))
        adoption = next(
            item
            for item in state["completed_milestones"]
            if item.get("phase") == "ADR-0014 conditional adoption"
        )
        self.assertEqual(adoption["merged_pr"], 85)
        self.assertEqual(adoption["merge_commit"], "0f5f76f86973316ac66b8e3f9d6e65419b310ec9")
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
        conformance = next(
            item
            for item in state["completed_milestones"]
            if item.get("phase") == "ADR-0014 required-changes independent conformance review"
        )
        self.assertEqual(conformance["reviewed_head_sha"], "31c967c785128671769eb713baed265da8ae0f2a")
        self.assertEqual(conformance["verdict"], "approve")
        self.assertEqual(conformance["critical_findings"], 0)
        self.assertEqual(conformance["high_findings"], 0)
        implementation = next(
            item
            for item in state["completed_milestones"]
            if item.get("phase") == "Liquid universe V4 lifecycle availability implementation"
        )
        self.assertEqual(implementation["merged_pr"], 86)
        self.assertEqual(implementation["merge_commit"], "fccc9972502732319d38eb36775d007396df25db")
        implementation_review = next(
            item
            for item in state["completed_milestones"]
            if item.get("phase") == "Liquid universe V4 implementation independent review"
        )
        self.assertEqual(implementation_review["merged_pr"], 87)
        self.assertEqual(implementation_review["verdict"], "approve")
        self.assertEqual(implementation_review["critical_findings"], 0)
        self.assertEqual(implementation_review["high_findings"], 0)
        auditor_review = next(
            item
            for item in state["completed_milestones"]
            if item.get("phase") == "U-03F V4 independent auditor implementation review"
        )
        self.assertEqual(auditor_review["merged_pr"], 93)
        self.assertEqual(auditor_review["reviewed_pr"], 92)
        self.assertEqual(
            auditor_review["reviewed_head_sha"],
            "d055efc1e46fb90b60a4553b9c5e2d1589bd7f9e",
        )
        self.assertEqual(auditor_review["verdict"], "approve")
        auditor_implementation = next(
            item
            for item in state["completed_milestones"]
            if item.get("phase") == "U-03F V4 independent auditor implementation"
        )
        self.assertEqual(auditor_implementation["merged_pr"], 92)
        self.assertEqual(
            auditor_implementation["merge_commit"],
            "d107894f393de01b2a046a8ffd2ee937a07bdc2b",
        )

        changed = copy.deepcopy(state)
        milestone = next(
            item
            for item in changed["completed_milestones"]
            if item.get("phase") == "ADR-0014 required-changes independent conformance review"
        )
        milestone["reviewed_head_sha"] = "0" * 40
        self.assertIn("ADR-0014 conformance milestone binding changed", validate(changed))

        changed = copy.deepcopy(state)
        changed["open_work"].append({"id": "U-03F", "status": "failed_audit", "pr": 95})
        self.assertIn(
            "merged failed U-03F must not remain in open_work",
            validate(changed),
        )

        changed = copy.deepcopy(state)
        milestone = next(
            item
            for item in changed["completed_milestones"]
            if item.get("phase") == "U-03F V4 independent audit"
        )
        milestone["verdict"] = "pass"
        self.assertIn("merged failed U-03F milestone binding changed", validate(changed))

        changed = copy.deepcopy(state)
        milestone = next(
            item
            for item in changed["completed_milestones"]
            if item.get("phase") == "Liquid universe V4 fixed-range public requalification"
        )
        milestone["source_freeze_hash"] = "0" * 64
        self.assertIn(
            "merged V4 requalification milestone binding changed",
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
