from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.adr0018_scheduled_market_cessation_check import (
    CONTRACT,
    DECISION,
    ROOT,
    derive_forced_exit_open,
    digest,
    validate,
)


class ADR0018Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def clone(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        relatives = [
            CONTRACT.relative_to(ROOT),
            DECISION.relative_to(ROOT),
            Path("reports/m1/evidence/external_strategy_boundary_authority/source_preflight.json"),
            Path("reports/m1/evidence/external_strategy_boundary_authority/source_preflight_command.json"),
            Path("config/membership_exit_boundary_authorization_v1.json"),
            Path("reports/m1/evidence/external_strategy_runtime/is_boundary_qualification.json"),
            Path("config/external_strategy_oos_guard_v1.json"),
            Path("config/external_strategy_candidate_freeze_v1.json"),
            Path("reports/expert/evidence/pr116_exact_head_review_v1.json"),
        ]
        for relative in relatives:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        return temporary, root

    def write_contract(self, root: Path, value: dict) -> None:
        path = root / CONTRACT.relative_to(ROOT)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def mutation_fails(self, mutate) -> None:
        temporary, root = self.clone()
        self.addCleanup(temporary.cleanup)
        changed = copy.deepcopy(self.contract)
        mutate(changed)
        changed["content_hash"] = digest(changed)
        self.write_contract(root, changed)
        self.assertTrue(validate(root))

    def test_repository_contract_and_bundle_bytes_are_exact(self) -> None:
        self.assertEqual(validate(), [])
        self.assertEqual(self.contract["content_hash"], digest(self.contract))

    def test_forced_exit_is_derived_from_cessation(self) -> None:
        self.assertEqual(derive_forced_exit_open("2024-07-22T03:00:00Z"), "2024-07-22T02:55:00Z")
        with self.assertRaises(ValueError):
            derive_forced_exit_open("2024-07-22T03:01:00Z")

    def test_boundary_replacement_and_scope_tamper_fail(self) -> None:
        self.mutation_fails(lambda value: value["boundary_set_revision"].__setitem__("total_identity_count", 93))
        self.mutation_fails(lambda value: value["boundary_set_revision"]["one_for_one_replacement"]["add"].__setitem__(1, "2024-07-22T03:00:00Z"))
        self.mutation_fails(lambda value: value["boundary_set_revision"].__setitem__("additions_beyond_replacement", 1))

    def test_successor_forward_search_and_history_inheritance_fail(self) -> None:
        self.mutation_fails(lambda value: value["decision"].__setitem__("allow_successor_symbol_price_substitution", True))
        self.mutation_fails(lambda value: value["generic_rule"].__setitem__("forward_search_allowed", True))
        self.mutation_fails(lambda value: value["generic_rule"].__setitem__("successor_inherits_history_or_rank", True))
        self.mutation_fails(lambda value: value["rndr_event"].__setitem__("use_render_price_for_rndr_exit", True))

    def test_precedence_is_forced_exit_then_entry_rejection(self) -> None:
        precedence = self.contract["generic_rule"]["forced_exit_precedence"]
        self.assertIn("close every already-open position", precedence[0])
        self.assertIn("reject any new entry", precedence[1])
        self.assertIn("reject all later", precedence[2])
        self.mutation_fails(lambda value: value["generic_rule"]["forced_exit_precedence"].reverse())

    def test_indicator_isolation_reset_and_independent_orders_are_mandatory(self) -> None:
        rule = self.contract["generic_rule"]
        self.assertFalse(rule["append_boundary_row_to_candidate_ohlcv"])
        self.assertFalse(rule["append_boundary_row_to_indicator_history"])
        self.assertTrue(rule["reset_and_rewarm_required_after_any_later_readmission"])
        self.assertTrue(self.contract["required_preflight_before_freeze"]["normal_reverse_shuffled_independent_constructions_required"])
        self.mutation_fails(lambda value: value["generic_rule"].__setitem__("append_boundary_row_to_indicator_history", True))
        self.mutation_fails(lambda value: value["required_preflight_before_freeze"].__setitem__("normal_reverse_shuffled_independent_constructions_required", False))

    def test_results_oos_and_trading_permissions_remain_false(self) -> None:
        for key in ("original_is", "modified_is", "selection_trial_materialization", "oos", "dry_run", "api_private_endpoints", "paper_live", "order_placement", "execution_live", "m2"):
            self.assertFalse(self.contract["permissions"][key])
        self.mutation_fails(lambda value: value["permissions"].__setitem__("original_is", True))
        self.mutation_fails(lambda value: value["permissions"].__setitem__("oos", True))

    def test_candidate_row_is_not_claimed_as_validated_market_evidence(self) -> None:
        self.assertTrue(self.contract["rndr_event"]["exact_archive_and_row_not_yet_validated"])
        self.mutation_fails(lambda value: value["rndr_event"].__setitem__("exact_archive_and_row_not_yet_validated", False))


if __name__ == "__main__":
    unittest.main()
