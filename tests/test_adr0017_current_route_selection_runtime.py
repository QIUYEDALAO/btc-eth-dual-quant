from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.adr0017_current_route_selection_runtime_check import CONTRACT, ROOT, digest, validate


class ADR0017Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT.read_text())

    def clone(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        for relative in self.contract["bindings"]["contract_byte_hashes"]:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        target = root / CONTRACT.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(CONTRACT.read_bytes())
        return temporary, root

    def write_contract(self, root: Path, value: dict) -> None:
        (root / CONTRACT.relative_to(ROOT)).write_text(json.dumps(value, indent=2) + "\n")

    def test_repository_contract_is_exact(self) -> None:
        self.assertEqual(validate(), [])
        self.assertEqual(self.contract["content_hash"], digest(self.contract))

    def test_generated_time_is_not_identity(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(digest(changed), self.contract["content_hash"])

    def test_historical_trials_are_retained_but_not_same_distribution(self) -> None:
        historical = self.contract["statistical_selection"]["historical_m1a_m1b_m1c"]
        self.assertTrue(historical["retained_in_historical_trial_ledger"])
        self.assertTrue(historical["reported"])
        self.assertFalse(historical["deleted"])
        self.assertFalse(historical["current_route_same_distribution_reference"])

    def test_dsr_is_rank_not_absolute_gate(self) -> None:
        policy = self.contract["statistical_selection"]["dsr"]
        self.assertTrue(policy["mandatory_to_compute"])
        self.assertTrue(policy["mandatory_to_report"])
        self.assertTrue(policy["primary_selection_rank"])
        self.assertFalse(policy["absolute_is_hard_gate"])
        self.assertNotIn("dsr", " ".join(self.contract["statistical_selection"]["non_dsr_hard_gates"]))

    def test_binding_tamper_fails(self) -> None:
        temporary, root = self.clone()
        self.addCleanup(temporary.cleanup)
        path = root / "config/external_strategy_candidate_freeze_v1.json"
        path.write_bytes(path.read_bytes() + b"\n")
        self.assertTrue(any("bound file hash drift" in item for item in validate(root)))

    def test_permission_or_selection_tamper_fails(self) -> None:
        temporary, root = self.clone()
        self.addCleanup(temporary.cleanup)
        changed = copy.deepcopy(self.contract)
        changed["permissions"]["oos"] = True
        changed["content_hash"] = digest(changed)
        self.write_contract(root, changed)
        self.assertTrue(validate(root))

        changed = copy.deepcopy(self.contract)
        changed["statistical_selection"]["dsr"]["absolute_is_hard_gate"] = True
        changed["content_hash"] = digest(changed)
        self.write_contract(root, changed)
        self.assertTrue(validate(root))

    def test_final_selection_and_zero_state_are_frozen(self) -> None:
        final = self.contract["final_selection"]
        self.assertEqual(final["maximum_selected_candidates"], 1)
        self.assertEqual(final["terminal_success_status"], "pending_explicit_unique_oos_authorization")
        self.assertEqual(self.contract["zero_state_at_adoption"]["oos_rows_decoded"], 0)


if __name__ == "__main__":
    unittest.main()
