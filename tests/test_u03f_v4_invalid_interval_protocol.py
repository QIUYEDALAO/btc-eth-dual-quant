from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "u03f_v4_invalid_interval_protocol_check",
    ROOT / "scripts/u03f_v4_invalid_interval_protocol_check.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class InvalidIntervalProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = MODULE.load_protocol()

    def test_repository_protocol_inputs_and_docs_pass(self) -> None:
        self.assertEqual(MODULE.validate_protocol(self.protocol), [])
        self.assertEqual(MODULE.validate_immutable_inputs(self.protocol), [])
        self.assertEqual(MODULE.validate_docs(), [])

    def test_known_blocked_input_is_frozen(self) -> None:
        for key, value in (
            ("processing_errors", 118),
            ("stop_reason_count", 118),
            ("source_archive_count", 27735),
            ("repair_requalification_status", "pass"),
        ):
            changed = copy.deepcopy(self.protocol)
            changed["known_blocked_input"][key] = value
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_source_and_policy_shortcuts_fail_closed(self) -> None:
        for key in (
            "network_access_allowed",
            "source_download_or_replacement_allowed",
            "daily_or_rest_substitution_allowed",
            "historical_evidence_mutation_allowed",
            "production_pipeline_change_allowed",
            "policy_adoption_allowed",
            "validation_gate_reduction_allowed",
        ):
            changed = copy.deepcopy(self.protocol)
            changed["diagnostic_scope"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_integer_and_determinism_gates_cannot_be_weakened(self) -> None:
        mutations = (
            ("orders", ["normal"]),
            ("open_time_grid_ms", 1),
            ("valid_close_delta_ms", 299000),
            ("synchronous_minimum_symbols", 1),
            ("synchronous_minimum_fraction", 0.5),
            ("archive_binding_required_before_parse", False),
            ("raw_row_hash_required", False),
            ("raw_field_repair_allowed", True),
            ("synthetic_fill_allowed", True),
        )
        for key, value in mutations:
            changed = copy.deepcopy(self.protocol)
            changed["diagnostic_algorithm"][key] = value
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_direct_exception_and_existing_policy_adoption_are_forbidden(self) -> None:
        for key in ("direct_existing_gap_policy_adoption_allowed", "per_row_exception_registry_allowed"):
            changed = copy.deepcopy(self.protocol)
            changed["decision_gate"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_downstream_authorizations_remain_false(self) -> None:
        for key in MODULE.FALSE_AUTHORIZATIONS:
            changed = copy.deepcopy(self.protocol)
            changed["authorization"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_protocol_hash_is_deterministic_and_excludes_generated_time(self) -> None:
        first = MODULE.protocol_content_hash(self.protocol)
        self.assertEqual(first, MODULE.EXPECTED_PROTOCOL_CONTENT_HASH)
        changed = copy.deepcopy(self.protocol)
        changed["generated_utc"] = "2099-01-01T00:00:00Z"
        self.assertEqual(first, MODULE.protocol_content_hash(changed))
        changed["known_blocked_input"]["processing_errors"] = 118
        self.assertNotEqual(first, MODULE.protocol_content_hash(changed))
        self.assertIn("protocol content hash changed", MODULE.validate_protocol(changed))


if __name__ == "__main__":
    unittest.main()
