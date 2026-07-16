from __future__ import annotations

import copy
import hashlib
import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "u03f_v4_repair_protocol_check", ROOT / "scripts/u03f_v4_repair_protocol_check.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class U03FV4RepairProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = MODULE.load_protocol()

    def test_repository_protocol_inputs_and_docs_pass(self) -> None:
        self.assertEqual(MODULE.validate_protocol(self.protocol), [])
        self.assertEqual(MODULE.validate_immutable_inputs(self.protocol), [])
        self.assertEqual(MODULE.validate_docs(), [])

    def test_historical_binding_fetches_only_the_exact_frozen_commit(self) -> None:
        payload = b"historical production bytes"
        results = [
            subprocess.CompletedProcess([], 128, b"", b"missing"),
            subprocess.CompletedProcess([], 0, b"", b""),
            subprocess.CompletedProcess([], 0, payload, b""),
        ]
        with mock.patch.object(MODULE.subprocess, "run", side_effect=results) as run:
            actual = MODULE._historical_sha256(
                MODULE.STARTING_MAIN_SHA,
                "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py",
            )
        self.assertEqual(actual, hashlib.sha256(payload).hexdigest())
        self.assertEqual(
            run.call_args_list[1].args[0],
            ["git", "fetch", "--no-tags", "--depth=1", "origin", MODULE.STARTING_MAIN_SHA],
        )

    def test_historical_binding_fetch_failure_remains_fail_closed(self) -> None:
        results = [
            subprocess.CompletedProcess([], 128, b"", b"missing"),
            subprocess.CompletedProcess([], 128, b"", b"unavailable"),
        ]
        with mock.patch.object(MODULE.subprocess, "run", side_effect=results):
            with self.assertRaisesRegex(ValueError, "historical repair binding unavailable"):
                MODULE._historical_sha256(
                    MODULE.STARTING_MAIN_SHA,
                    "scripts/liquid_universe_v4_public_run.py",
                )

    def test_historical_binding_rejects_unfrozen_revision_without_fetch(self) -> None:
        with mock.patch.object(MODULE.subprocess, "run") as run:
            with self.assertRaisesRegex(ValueError, "historical repair binding revision changed"):
                MODULE._historical_sha256("0" * 40, "scripts/liquid_universe_v4_public_run.py")
        run.assert_not_called()

    def test_findings_and_faults_are_complete(self) -> None:
        for finding in MODULE.FINDING_IDS:
            changed = copy.deepcopy(self.protocol)
            changed["finding_requirements"] = [
                item for item in changed["finding_requirements"] if item["finding_id"] != finding
            ]
            with self.subTest(finding=finding):
                self.assertTrue(MODULE.validate_protocol(changed))
        for fault in MODULE.FAULT_IDS:
            changed = copy.deepcopy(self.protocol)
            changed["required_fault_tests"].pop(fault)
            with self.subTest(fault=fault):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_repair_shortcuts_fail_closed(self) -> None:
        for key in (
            "historical_evidence_mutation_allowed", "source_download_or_replacement_allowed",
            "validation_gate_reduction_allowed", "public_requalification_in_implementation_pr_allowed",
        ):
            changed = copy.deepcopy(self.protocol)
            changed["repair_scope"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_review_requalification_and_audit_gates_cannot_be_lowered(self) -> None:
        mutations = (
            ("exact_head_review_gate", "high_findings_required", 1),
            ("exact_head_review_gate", "allowed_verdict", "approve_with_required_changes"),
            ("public_requalification_gate", "all_blocking_counters_must_be_zero", False),
            ("public_requalification_gate", "source_archive_count_expected", 27735),
            ("new_independent_audit_gate", "exact_production_manifests_required", 14),
            ("new_independent_audit_gate", "auditor_algorithm_hash_drift_allowed", True),
        )
        for section, key, value in mutations:
            changed = copy.deepcopy(self.protocol)
            changed[section][key] = value
            with self.subTest(section=section, key=key):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_downstream_authorizations_remain_false(self) -> None:
        for key in MODULE.FALSE_AUTHORIZATIONS:
            changed = copy.deepcopy(self.protocol)
            changed["authorization"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_protocol(changed))

    def test_protocol_hash_is_deterministic_and_excludes_generated_time(self) -> None:
        first = MODULE.protocol_content_hash(self.protocol)
        changed = copy.deepcopy(self.protocol)
        changed["generated_utc"] = "2099-01-01T00:00:00Z"
        self.assertEqual(first, MODULE.protocol_content_hash(changed))
        changed["public_requalification_gate"]["range_end"] = "2026-05"
        self.assertNotEqual(first, MODULE.protocol_content_hash(changed))


if __name__ == "__main__":
    unittest.main()
