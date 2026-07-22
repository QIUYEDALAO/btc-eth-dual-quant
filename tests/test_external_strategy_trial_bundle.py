from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

from btc_eth_dual_quant.audit.external_strategy_trial_bundle import (
    KINDS,
    SCENARIOS,
    SimulatedTrialCrash,
    TrialBundleError,
    TrialBundleExists,
    TrialExecutorError,
    TrialTerminalIncident,
    incident_paths,
    materialize_trial_bundle,
    materialized_trial_ids,
    recover_orphaned_staging,
    recover_trial_bundle,
    semantic_hash,
    validate_trial_bundle,
)


def envelope(trial_id: str = "trial-001") -> dict[str, object]:
    return {
        "schema_version": "external-strategy-is-result-v1",
        "trial_id": trial_id,
        "candidate_id": "SyntheticCandidate",
        "variant_id": "original-v1",
        "variant_type": "original",
        "source_hash": "0" * 64,
        "source_declaration_hash": "a" * 64,
        "candidate_freeze_hash": "1" * 64,
        "unified_is_protocol_hash": "2" * 64,
        "data_authority_hash": "3" * 64,
        "benchmark_contract_hash": "4" * 64,
        "dsr_reference_hash": "5" * 64,
        "original_is_authority_hash": "8" * 64,
        "runtime_route_manifest_hash": "9" * 64,
        "causal_summary_hash": "b" * 64,
        "boundary_authority_hash": "c" * 64,
        "base_adapter_hash": "6" * 64,
        "variant_executable_hash": "7" * 64,
        "runtime_effective_settings_hash": "d" * 64,
        "runtime_resolved_parameters_hash": "e" * 64,
        "modification_package_id": None,
        "modification_package_hash": None,
        "first_materialized_utc": "2026-07-22T00:00:00Z",
        "append_only": True,
    }


class RecordingExecutor:
    def __init__(self, *, fail_on: str | None = None) -> None:
        self.calls: list[str] = []
        self.fail_on = fail_on

    def __call__(self, scenario: str) -> dict[str, dict]:
        self.calls.append(scenario)
        if scenario == self.fail_on:
            raise RuntimeError("synthetic executor failure")
        cost_index = SCENARIOS.index(scenario)
        return {
            "trades": {"trades": [{"trade_id": "t1", "cost_index": cost_index}]},
            "equity": {"points": [{"day": "2020-06-30", "equity": 100000 - cost_index}]},
            "metrics": {"net_return": -cost_index / 1000, "hard_gate_status": "failed"},
        }


class AtomicTrialBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "trials"

    def test_complete_bundle_has_exact_twelve_hash_bound_envelopes_and_read_only_files(self) -> None:
        executor = RecordingExecutor()
        receipt = materialize_trial_bundle(
            self.root,
            trial_id="trial-001",
            base_envelope=envelope(),
            executor=executor,
            staging_token="a" * 32,
        )

        self.assertEqual(executor.calls, list(SCENARIOS))
        self.assertEqual(receipt.result_file_count, 12)
        self.assertTrue(receipt.governance_complete)
        self.assertEqual(materialized_trial_ids(self.root), ("trial-001",))
        manifest = json.loads((receipt.directory / "trial.bundle.json").read_text())
        self.assertEqual(
            {(row["scenario"], row["kind"]) for row in manifest["result_files"]},
            {(scenario, kind) for scenario in SCENARIOS for kind in KINDS},
        )
        self.assertEqual(len({row["path"] for row in manifest["result_files"]}), 12)
        for row in manifest["result_files"]:
            self.assertEqual(Path(row["path"]).parts[0], "trial-001")
            payload = json.loads((self.root / row["path"]).read_text())
            self.assertEqual(payload["trial_id"], "trial-001")
            self.assertEqual(payload["scenario"], row["scenario"])
            self.assertEqual(payload["kind"], row["kind"])
            self.assertEqual(semantic_hash(payload), row["semantic_hash"])
            self.assertEqual(os.stat(self.root / row["path"]).st_mode & 0o222, 0)
        self.assertEqual(os.stat(receipt.directory).st_mode & 0o222, 0)

    def test_pre_rename_crash_keeps_zero_trials_and_records_no_performance_incident(self) -> None:
        executor = RecordingExecutor()
        with self.assertRaises(SimulatedTrialCrash):
            materialize_trial_bundle(
                self.root,
                trial_id="trial-001",
                base_envelope=envelope(),
                executor=executor,
                crash_at="pre_rename",
                staging_token="b" * 32,
            )

        self.assertEqual(executor.calls, list(SCENARIOS))
        self.assertEqual(materialized_trial_ids(self.root), ())
        paths = incident_paths(self.root, "trial-001")
        self.assertEqual(len(paths), 1)
        incident = json.loads(paths[0].read_text())
        self.assertFalse(incident["performance_materialized"])
        self.assertFalse(incident["result_values_recorded"])
        self.assertFalse(incident["bundle_exists"])
        forbidden = {"scenario", "trades", "equity", "metrics", "result_files"}
        self.assertTrue(forbidden.isdisjoint(incident))
        second = RecordingExecutor()
        with self.assertRaises(TrialTerminalIncident):
            materialize_trial_bundle(
                self.root,
                trial_id="trial-001",
                base_envelope=envelope(),
                executor=second,
                staging_token="c" * 32,
            )
        self.assertEqual(second.calls, [])

    def test_post_rename_recovery_only_completes_governance_without_executor(self) -> None:
        executor = RecordingExecutor()
        with self.assertRaises(SimulatedTrialCrash):
            materialize_trial_bundle(
                self.root,
                trial_id="trial-001",
                base_envelope=envelope(),
                executor=executor,
                crash_at="post_rename",
                staging_token="d" * 32,
            )
        self.assertEqual(executor.calls, list(SCENARIOS))
        before = validate_trial_bundle(self.root, "trial-001")
        self.assertFalse(before.governance_complete)

        first = recover_trial_bundle(self.root, "trial-001")
        second = recover_trial_bundle(self.root, "trial-001")
        self.assertTrue(first.governance_complete)
        self.assertEqual(first, second)
        self.assertEqual(executor.calls, list(SCENARIOS))
        marker = json.loads((self.root / ".governance/trial-001.json").read_text())
        self.assertEqual(marker["selection_trial_increment"], 1)
        self.assertFalse(marker["executor_reinvoked_during_recovery"])

    def test_executor_failure_is_terminal_pre_materialization_and_never_reruns(self) -> None:
        executor = RecordingExecutor(fail_on="CostX2")
        with self.assertRaises(TrialExecutorError):
            materialize_trial_bundle(
                self.root,
                trial_id="trial-001",
                base_envelope=envelope(),
                executor=executor,
                staging_token="e" * 32,
            )
        self.assertEqual(executor.calls, ["Base", "CostX2"])
        self.assertEqual(materialized_trial_ids(self.root), ())
        incident = json.loads(incident_paths(self.root, "trial-001")[0].read_text())
        self.assertEqual(incident["reason"], "executor_failed")
        self.assertEqual(incident["executor_invocations"], 1)

        retry = RecordingExecutor()
        with self.assertRaises(TrialTerminalIncident):
            materialize_trial_bundle(
                self.root,
                trial_id="trial-001",
                base_envelope=envelope(),
                executor=retry,
                staging_token="f" * 32,
            )
        self.assertEqual(retry.calls, [])

    def test_paths_reject_traversal_cross_trial_reuse_and_overwrite(self) -> None:
        for trial_id in ("../trial", "trial/child", ".hidden", ".."):
            with self.subTest(trial_id=trial_id):
                with self.assertRaises(TrialBundleError):
                    materialize_trial_bundle(
                        self.root,
                        trial_id=trial_id,
                        base_envelope=envelope(trial_id),
                        executor=RecordingExecutor(),
                    )

        executor = RecordingExecutor()
        materialize_trial_bundle(
            self.root,
            trial_id="trial-001",
            base_envelope=envelope(),
            executor=executor,
            staging_token="g" * 32,
        )
        duplicate = RecordingExecutor()
        with self.assertRaises(TrialBundleExists):
            materialize_trial_bundle(
                self.root,
                trial_id="trial-001",
                base_envelope=envelope(),
                executor=duplicate,
                staging_token="h" * 32,
            )
        self.assertEqual(duplicate.calls, [])

        manifest_path = self.root / "trial-001/trial.bundle.json"
        os.chmod(manifest_path, 0o600)
        manifest = json.loads(manifest_path.read_text())
        changed = copy.deepcopy(manifest)
        changed["result_files"][0]["path"] = changed["result_files"][0]["path"].replace(
            "trial-001/", "trial-999/"
        )
        changed["bundle_content_hash"] = semantic_hash(
            {key: value for key, value in changed.items() if key != "bundle_content_hash"}
        )
        manifest_path.write_text(json.dumps(changed, indent=2, sort_keys=True) + "\n")
        os.chmod(manifest_path, 0o444)
        with self.assertRaisesRegex(TrialBundleError, "exactly <trial_id>/<basename>"):
            validate_trial_bundle(self.root, "trial-001")

    def test_orphaned_staging_recovery_creates_incident_without_materialization(self) -> None:
        staging = self.root / ".staging" / f"trial-001--{'i' * 32}"
        staging.mkdir(parents=True)
        (staging / "partial.json").write_text('{"opaque":"not-authoritative"}\n')

        recovered = recover_orphaned_staging(self.root, trial_id="trial-001")
        self.assertEqual(len(recovered), 1)
        self.assertFalse(staging.exists())
        self.assertEqual(materialized_trial_ids(self.root), ())
        incident = json.loads(recovered[0].read_text())
        self.assertEqual(incident["reason"], "orphaned_staging_recovered")
        self.assertFalse(incident["performance_materialized"])


if __name__ == "__main__":
    unittest.main()
