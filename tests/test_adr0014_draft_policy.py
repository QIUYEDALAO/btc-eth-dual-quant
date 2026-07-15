import copy
import json
from pathlib import Path
import unittest

from scripts.adr0014_draft_policy_check import (
    ADR,
    CONFORMANCE_MODEL,
    FAULT_MATRIX_MODEL,
    POLICY_MODEL,
    verify_models,
    verify_repository,
)


ROOT = Path(__file__).resolve().parents[1]


def load_models():
    return (
        json.loads(POLICY_MODEL.read_text(encoding="utf-8")),
        json.loads(FAULT_MATRIX_MODEL.read_text(encoding="utf-8")),
        json.loads(CONFORMANCE_MODEL.read_text(encoding="utf-8")),
        ADR.read_text(encoding="utf-8"),
    )


class ADR0014DraftPolicyTests(unittest.TestCase):
    def assert_mutation_fails(self, mutate):
        policy, faults, conformance, adr = load_models()
        mutate(policy, faults, conformance)
        self.assertTrue(verify_models(policy, faults, conformance, adr))

    def test_complete_structured_draft_passes(self):
        self.assertEqual(verify_repository(), [])

    def test_draft_is_docs_only_and_zero_authority(self):
        policy, faults, conformance, _ = load_models()
        for document in (policy, faults, conformance):
            self.assertEqual(document["status"], "proposed_draft_non_authoritative")
            self.assertFalse(document["runtime_authority"])
            self.assertFalse(document["policy_adopted"])
            self.assertFalse(document["implementation_authorized"])
        self.assertFalse(any(policy["authorization_matrix"].values()))

    def test_all_mandatory_changes_have_acceptance_and_fault_tests(self):
        _, faults, conformance, _ = load_models()
        fault_ids = {case["test_id"] for case in faults["fault_cases"]}
        self.assertEqual(
            set(conformance["mandatory_changes"]),
            {f"MC-{number:02d}" for number in range(1, 12)},
        )
        for entry in conformance["mandatory_changes"].values():
            self.assertTrue(entry["addressed"])
            self.assertTrue(entry["blocking_until_independent_review"])
            self.assertTrue(entry["acceptance_criteria"])
            self.assertTrue(set(entry["required_tests"]).issubset(fault_ids))

    def test_klay_event_contains_all_three_affected_days(self):
        policy, _, _, _ = load_models()
        rows = policy["lifecycle_event_model"]["frozen_klay_example"]["affected_raw_rows"]
        self.assertEqual(
            [(row["date"], row["classification"]) for row in rows],
            [
                ("2024-10-28", "cessation_day_partial_row"),
                ("2024-10-29", "post_cessation_normal_duration_placeholder"),
                ("2024-10-30", "post_cessation_malformed_placeholder"),
            ],
        )

    def test_deleting_2024_10_29_placeholder_fails(self):
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["lifecycle_event_model"][
                "frozen_klay_example"
            ].__setitem__(
                "affected_raw_rows",
                [
                    row
                    for row in policy["lifecycle_event_model"]["frozen_klay_example"][
                        "affected_raw_rows"
                    ]
                    if row["date"] != "2024-10-29"
                ],
            )
        )

    def test_narrow_close_before_open_only_rule_fails(self):
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["lifecycle_event_model"].__setitem__(
                "row_classifications", ["post_cessation_malformed_placeholder"]
            )
        )

    def test_missing_availability_end_or_wrong_pipeline_order_fails(self):
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["availability_epoch_model"][
                "required_fields"
            ].remove("availability_end_exclusive")
        )
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy.__setitem__(
                "qualification_pipeline_order",
                [
                    "validate_raw_data",
                    "build_expected_grid",
                    "apply_availability_mask",
                ],
            )
        )

    def test_partial_day_or_post_cessation_rows_cannot_enter_windows(self):
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["timeframe_semantics"]["1d"].__setitem__(
                "partial_day_complete_window_eligible", True
            )
        )
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["lifecycle_event_model"].__setitem__(
                "post_cessation_rows_complete_history_eligible", True
            )
        )

    def test_knowledge_and_effective_times_cannot_be_collapsed(self):
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["point_in_time_knowledge"].__setitem__(
                "required_times", ["event_time"]
            )
        )

    def test_membership_and_active_universe_cannot_be_mixed(self):
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["universe_views"].__setitem__(
                "separate_counts", False
            )
        )

    def test_termination_cannot_define_return_or_settlement(self):
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["non_targets"].remove("zero_return")
        )
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["universe_views"]["termination_means"].append(
                "cash"
            )
        )

    def test_successor_cannot_inherit_old_history(self):
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["successor_metadata"].__setitem__(
                "inherits_history", True
            )
        )

    def test_policy_and_event_registry_must_remain_separate(self):
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["authority_separation"].__setitem__(
                "separate_authorities", False
            )
        )

    def test_overlapping_epochs_archive_absence_and_temporary_events_fail(self):
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["availability_epoch_model"].__setitem__(
                "overlap_result", "pass"
            )
        )
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["evidence_sufficiency"].__setitem__(
                "archive_absence_is_proof", True
            )
        )
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["evidence_sufficiency"][
                "permanent_policy_event_types"
            ].append("temporary_suspension")
        )

    def test_v4_artifacts_and_zero_pass_counters_are_required(self):
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["future_v4_authority"][
                "required_artifacts"
            ].remove("active_universe_manifest")
        )
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["future_v4_authority"][
                "pass_requires_zero"
            ].remove("synthetic_fills")
        )

    def test_fault_matrix_ids_are_complete_and_unique(self):
        self.assert_mutation_fails(
            lambda _policy, faults, _conf: faults["fault_cases"].pop()
        )
        self.assert_mutation_fails(
            lambda _policy, faults, _conf: faults["fault_cases"][1].__setitem__(
                "test_id", faults["fault_cases"][0]["test_id"]
            )
        )

    def test_fixed_evidence_and_authorization_tampering_fails(self):
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy.__setitem__(
                "klay_evidence_hash", "0" * 64
            )
        )
        self.assert_mutation_fails(
            lambda policy, _faults, _conf: policy["authorization_matrix"].__setitem__(
                "v4_implementation", True
            )
        )

    def test_models_are_not_imported_by_runtime(self):
        names = {POLICY_MODEL.name, FAULT_MATRIX_MODEL.name, CONFORMANCE_MODEL.name}
        for root in (ROOT / "src", ROOT / "config"):
            for path in root.rglob("*"):
                if path.is_file():
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    self.assertTrue(names.isdisjoint({name for name in names if name in text}))


if __name__ == "__main__":
    unittest.main()
