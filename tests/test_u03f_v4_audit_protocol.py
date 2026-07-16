from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "u03f_v4_audit_protocol_check",
    ROOT / "scripts/u03f_v4_audit_protocol_check.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class U03FV4AuditProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = MODULE.load_protocol()

    def test_repository_protocol_and_report_pass(self) -> None:
        self.assertEqual(MODULE.validate_protocol(self.protocol), [])
        self.assertEqual(MODULE.validate_repository_bindings(self.protocol), [])
        self.assertEqual(MODULE.validate_report(), [])

    def test_all_frozen_bindings_are_immutable(self) -> None:
        for section, key in MODULE.FROZEN_BINDING_PATHS:
            changed = copy.deepcopy(self.protocol)
            changed[section][key] = "0" * 64
            with self.subTest(section=section, key=key):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_manifest_hash_map_is_exact(self) -> None:
        changed = copy.deepcopy(self.protocol)
        changed["production_manifest_hashes"].pop("membership_manifest")
        self.assertTrue(MODULE.validate_protocol(changed))
        changed = copy.deepcopy(self.protocol)
        changed["production_manifest_hashes"]["membership_manifest"] = "0" * 64
        self.assertTrue(MODULE.validate_protocol(changed))

    def test_verdicts_and_zero_authorization_are_frozen(self) -> None:
        changed = copy.deepcopy(self.protocol)
        changed["allowed_verdicts"].append("pass_with_warning")
        self.assertTrue(MODULE.validate_protocol(changed))
        for key in self.protocol["authorization"]:
            changed = copy.deepcopy(self.protocol)
            changed["authorization"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_exact_and_semantic_mismatches_cannot_be_ignored(self) -> None:
        for key in (
            "freeze_before_result",
            "exact_mismatch_must_be_reported",
            "semantic_mismatch_must_be_reported",
            "economic_materiality_exception_allowed",
            "tolerance_membership_rank_timestamp_status_allowed",
            "production_markdown_as_computation_input_allowed",
            "production_builder_as_audit_result_allowed",
        ):
            changed = copy.deepcopy(self.protocol)
            changed["independence_and_comparison"][key] = not changed["independence_and_comparison"][key]
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_protocol_hash_is_deterministic_and_excludes_declared_wrapper_fields(self) -> None:
        first = MODULE.protocol_content_hash(self.protocol)
        changed = copy.deepcopy(self.protocol)
        changed["generated_utc"] = "2099-01-01T00:00:00Z"
        self.assertEqual(first, MODULE.protocol_content_hash(changed))
        changed["audit_scope"]["range_end"] = "2026-05"
        self.assertNotEqual(first, MODULE.protocol_content_hash(changed))


if __name__ == "__main__":
    unittest.main()
