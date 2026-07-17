import copy
import unittest

from scripts.adr0015_policy_draft_check import load_model, validate_model, verify_repository


class ADR0015PolicyDraftTests(unittest.TestCase):
    def assert_mutation_fails(self, mutate):
        model = copy.deepcopy(load_model())
        mutate(model)
        self.assertTrue(validate_model(model))

    def test_repository_draft_passes(self):
        self.assertEqual(verify_repository(), [])

    def test_draft_has_zero_authority(self):
        model = load_model()
        self.assertEqual(model["status"], "proposed_draft_non_authoritative")
        self.assertFalse(model["runtime_authority"])
        self.assertFalse(model["policy_adopted"])
        self.assertFalse(model["implementation_authorized"])
        self.assertFalse(any(model["authorization_matrix"].values()))

    def test_threshold_reduction_fails(self):
        self.assert_mutation_fails(
            lambda model: model["candidate_predicate"].__setitem__("minimum_invalid_active_fraction", 0.5)
        )
        self.assert_mutation_fails(
            lambda model: model["candidate_predicate"].__setitem__("minimum_invalid_active_members", 1)
        )

    def test_date_or_symbol_registry_fails(self):
        self.assert_mutation_fails(
            lambda model: model["candidate_predicate"].__setitem__("date_or_symbol_registry_allowed", True)
        )
        self.assert_mutation_fails(
            lambda model: model["diagnostic_facts_not_policy_exceptions"].__setitem__(
                "known_window_dates_are_runtime_inputs", True
            )
        )

    def test_partial_mask_or_valid_minority_retention_fails(self):
        self.assert_mutation_fails(
            lambda model: model["accepted_event_semantics"].__setitem__(
                "invalid_rows_only_partial_mask_allowed", True
            )
        )
        self.assert_mutation_fails(
            lambda model: model["accepted_event_semantics"].__setitem__(
                "valid_minority_rows_are_quarantined", False
            )
        )

    def test_raw_repair_fill_or_replacement_fails(self):
        for key in ("raw_row_rewrite_allowed", "timestamp_repair_allowed", "synthetic_fill_allowed",
                    "source_replacement_allowed", "replacement_member_allowed"):
            with self.subTest(key=key):
                self.assert_mutation_fails(
                    lambda model, key=key: model["accepted_event_semantics"].__setitem__(key, True)
                )

    def test_non_time_or_off_grid_exception_fails(self):
        self.assert_mutation_fails(lambda model: model["hard_block_conditions"].remove("open_time_off_grid"))
        self.assert_mutation_fails(
            lambda model: model["hard_block_conditions"].remove("non_time_field_invalid_or_nonfinite")
        )

    def test_gap_policy_direct_reuse_fails(self):
        self.assert_mutation_fails(
            lambda model: model["v2_gap_policy_relationship"].__setitem__(
                "direct_reuse_as_new_policy_authority", True
            )
        )

    def test_review_gate_or_severity_relaxation_fails(self):
        self.assert_mutation_fails(
            lambda model: model["independent_review_gate"].__setitem__("exact_draft_head_required", False)
        )
        self.assert_mutation_fails(
            lambda model: model["independent_review_gate"].__setitem__("maximum_high_findings", 1)
        )
        self.assert_mutation_fails(
            lambda model: model["independent_review_gate"].__setitem__("approval_adopts_policy", True)
        )

    def test_fault_case_deletion_or_non_blocking_result_fails(self):
        self.assert_mutation_fails(lambda model: model["fault_cases"].pop())
        self.assert_mutation_fails(
            lambda model: model["fault_cases"][0].__setitem__("expected", "pass")
        )

    def test_authority_expansion_fails(self):
        self.assert_mutation_fails(
            lambda model: model["authorization_matrix"].__setitem__(
                "production_policy_implementation", True
            )
        )

    def test_evidence_hash_drift_fails(self):
        self.assert_mutation_fails(
            lambda model: model["immutable_evidence_bindings"].__setitem__(
                "diagnostic_content_hash", "0" * 64
            )
        )


if __name__ == "__main__":
    unittest.main()
