from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "adr0015_invalid_interval_audit_protocol_check",
    ROOT / "scripts/adr0015_invalid_interval_audit_protocol_check.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ADR0015AuditProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = MODULE.load_protocol()

    def test_repository_protocol_and_report_pass(self) -> None:
        self.assertEqual(MODULE.validate_protocol(self.protocol), [])
        self.assertEqual(MODULE.validate_repository_bindings(self.protocol), [])
        self.assertEqual(MODULE.validate_report(), [])

    def test_every_authority_and_manifest_binding_fails_on_tamper(self) -> None:
        for section, values in (
            ("authority_bindings", MODULE.EXPECTED_AUTHORITY),
            ("production_manifest_hashes", MODULE.EXPECTED_MANIFEST_HASHES),
        ):
            for key in values:
                changed = copy.deepcopy(self.protocol)
                changed[section][key] = "0" * 64
                with self.subTest(section=section, key=key):
                    self.assertTrue(MODULE.validate_protocol(changed))

    def test_nineteen_of_nineteen_zero_mismatch_gate_is_frozen(self) -> None:
        for key in self.protocol["comparison_gate"]:
            changed = copy.deepcopy(self.protocol)
            changed["comparison_gate"][key] += 1
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_independence_shortcuts_fail_closed(self) -> None:
        for key, value in self.protocol["independence_and_comparison"].items():
            changed = copy.deepcopy(self.protocol)
            changed["independence_and_comparison"][key] = not value
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_real_audit_and_downstream_authorizations_remain_false(self) -> None:
        allowed_true = {
            "independent_auditor_fixture_implementation_after_protocol_freeze",
            "independent_auditor_fault_injection_after_protocol_freeze",
            "independent_auditor_exact_head_review_after_implementation",
        }
        for key, value in self.protocol["authorization"].items():
            self.assertEqual(value, key in allowed_true)
        for key in set(self.protocol["authorization"]) - allowed_true:
            changed = copy.deepcopy(self.protocol)
            changed["authorization"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_verdicts_recomputations_and_severity_cannot_be_relaxed(self) -> None:
        changed = copy.deepcopy(self.protocol)
        changed["allowed_verdicts"].append("pass_with_warning")
        self.assertTrue(MODULE.validate_protocol(changed))
        changed = copy.deepcopy(self.protocol)
        changed["required_recomputations"].pop()
        self.assertTrue(MODULE.validate_protocol(changed))
        changed = copy.deepcopy(self.protocol)
        changed["severity_rules"]["critical"].pop()
        self.assertTrue(MODULE.validate_protocol(changed))

    def test_generated_time_is_excluded_but_gate_drift_changes_identity(self) -> None:
        frozen = MODULE.protocol_content_hash(self.protocol)
        changed = copy.deepcopy(self.protocol)
        changed["generated_utc"] = "2099-01-01T00:00:00Z"
        self.assertEqual(frozen, MODULE.protocol_content_hash(changed))
        changed["comparison_gate"]["production_manifests_exact_required"] = 18
        self.assertNotEqual(frozen, MODULE.protocol_content_hash(changed))


if __name__ == "__main__":
    unittest.main()
