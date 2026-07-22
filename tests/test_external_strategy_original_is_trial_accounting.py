from __future__ import annotations

import copy
from datetime import date, timedelta
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from btc_eth_dual_quant.audit.external_strategy_trial_bundle import (
    SCENARIOS,
    materialize_trial_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "external_strategy_original_is_trial_check",
    ROOT / "scripts/external_strategy_original_is_trial_check.py",
)
CHECK = importlib.util.module_from_spec(SPEC)
if SPEC.loader is None:
    raise RuntimeError("trial checker loader unavailable")
SPEC.loader.exec_module(CHECK)


def load(root: Path, relative: str) -> dict:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def write(root: Path, relative: str, value: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class OriginalISTrialAccountingTests(unittest.TestCase):
    def clone(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        for relative in (
            "config",
            "reports/expert/evidence",
            "reports/m1/evidence/external_strategy_runtime",
            "reports/m1/evidence/external_strategy_boundary_authority",
            "reports/m1/evidence/external_strategy_is_state",
            "reports/m1/evidence/external_strategy_is_trials",
            "external_strategies/adapters",
        ):
            shutil.copytree(ROOT / relative, root / relative)
        return temporary, root

    def envelope(
        self,
        root: Path,
        *,
        trial_id: str = "trial-001",
        candidate_index: int = 0,
        timestamp: str = "2026-07-22T00:00:00Z",
        variant_type: str = "original",
    ) -> dict:
        authority = load(root, "config/external_strategy_original_is_authority_v1.json")
        freeze = load(root, "config/external_strategy_candidate_freeze_v1.json")
        protocol = load(root, "config/external_strategy_unified_is_protocol_v1.json")
        data = load(root, "config/external_strategy_data_authority_v1.json")
        benchmark = load(root, "config/external_strategy_benchmark_v1.json")
        dsr = load(root, "config/external_strategy_dsr_reference_trials_v1.json")
        candidate = freeze["frozen_candidates"][candidate_index]
        runtime = authority["runtime_candidates"][candidate_index]
        return {
            "schema_version": "external-strategy-is-result-v1",
            "trial_id": trial_id,
            "candidate_id": candidate["id"],
            "variant_id": "original-v1" if variant_type == "original" else "modified-v1",
            "variant_type": variant_type,
            "source_hash": candidate["source_sha256"],
            "source_declaration_hash": candidate["source_declaration_hash"],
            "candidate_freeze_hash": freeze["content_hash"],
            "unified_is_protocol_hash": protocol["content_hash"],
            "data_authority_hash": data["canonical_content_hash"],
            "benchmark_contract_hash": benchmark["canonical_content_hash"],
            "dsr_reference_hash": dsr["canonical_content_hash"],
            "original_is_authority_hash": authority["content_hash"],
            "runtime_route_manifest_hash": authority["bindings"]["runtime_route"]["content_hash"],
            "causal_summary_hash": authority["bindings"]["causal_summary"]["content_hash"],
            "boundary_authority_hash": authority["bindings"]["completed_boundary_authority"]["content_hash"],
            "base_adapter_hash": runtime["base_adapter_hash"],
            "variant_executable_hash": runtime["variant_executable_hash"],
            "runtime_effective_settings_hash": runtime["runtime_effective_settings_hash"],
            "runtime_resolved_parameters_hash": runtime["runtime_resolved_parameters_hash"],
            "modification_package_id": None,
            "modification_package_hash": None,
            "first_materialized_utc": timestamp,
            "append_only": True,
        }

    def executor(self, *, metric_changes: dict | None = None, equity_changes: dict | None = None):
        anchor = date(2020, 6, 30)
        points = [
            {"day": str(anchor + timedelta(days=index)), "equity": 100000.0}
            for index in range(1534)
        ]

        def run(scenario: str) -> dict[str, dict]:
            metrics = {
                "net_return": 0.0,
                "daily_mtm_sharpe": 0.0,
                "psr": 0.0,
                "max_drawdown": 0.0,
                "completed_trades": 0,
                "delete_best_3_return": 0.0,
                "profitable_subperiod_count": 0,
                "equal_weight_benchmark": {"net_return": 0.0},
                "risk_matched_benchmark": {"net_return": 0.0},
                "hard_gate_status": "failed",
            }
            if metric_changes:
                metrics.update(metric_changes)
            equity = {"points": copy.deepcopy(points)}
            if equity_changes:
                equity.update(copy.deepcopy(equity_changes))
            return {"trades": {"trades": []}, "equity": equity, "metrics": metrics}

        return run

    def refresh_state(self, root: Path, trial_ids: list[str], sharpes: list[float] | None = None) -> None:
        state = load(root, "reports/m1/evidence/external_strategy_is_state/selection_state_v1.json")
        trial_root = root / "reports/m1/evidence/external_strategy_is_trials"
        ordered = []
        for trial_id in trial_ids:
            manifest = load(root, f"reports/m1/evidence/external_strategy_is_trials/{trial_id}/trial.bundle.json")
            try:
                materialized = CHECK.parse_utc(manifest["base_envelope"]["first_materialized_utc"])
            except (TypeError, ValueError):
                materialized = CHECK.datetime.max.replace(tzinfo=CHECK.timezone.utc)
            ordered.append((materialized, trial_id, manifest["bundle_content_hash"]))
        ordered.sort()
        ids = [item[1] for item in ordered]
        values = sharpes if sharpes is not None else [0.0] * len(ids)
        state.update(
            {
                "status": "zero_trials_pending_first_original_is" if not ids else "original_is_trials_materialized_append_only",
                "selection_trial_count": len(ids),
                "required_trial_count": 3 + len(ids),
                "trial_order": ids,
                "trial_bundle_hashes": {item[1]: item[2] for item in ordered},
                "selection_trial_sharpes": {"Base": values, "CostX2": values},
            }
        )
        state["content_hash"] = CHECK.canonical_hash(state)
        write(root, "reports/m1/evidence/external_strategy_is_state/selection_state_v1.json", state)

    def materialize(self, root: Path, **envelope_options: object) -> None:
        trial_id = str(envelope_options.get("trial_id", "trial-001"))
        materialize_trial_bundle(
            root / "reports/m1/evidence/external_strategy_is_trials",
            trial_id=trial_id,
            base_envelope=self.envelope(root, **envelope_options),
            executor=self.executor(),
            staging_token=(trial_id.replace("-", "") + "x" * 32)[:32],
        )

    def test_zero_state_and_one_complete_trial_pass(self) -> None:
        self.assertEqual(CHECK.validate(ROOT), [])
        temporary, root = self.clone()
        self.addCleanup(temporary.cleanup)
        self.materialize(root)
        self.refresh_state(root, ["trial-001"])
        self.assertEqual(CHECK.validate(root), [])

    def test_state_count_dsr_sequence_and_order_drift_fail(self) -> None:
        temporary, root = self.clone()
        self.addCleanup(temporary.cleanup)
        self.materialize(root, trial_id="trial-002", candidate_index=1, timestamp="2026-07-22T02:00:00Z")
        self.materialize(root, trial_id="trial-001", candidate_index=0, timestamp="2026-07-22T01:00:00Z")
        self.refresh_state(root, ["trial-002", "trial-001"])
        self.assertEqual(CHECK.validate(root), [])
        state_path = "reports/m1/evidence/external_strategy_is_state/selection_state_v1.json"
        state = load(root, state_path)
        state["trial_order"].reverse()
        state["selection_trial_sharpes"]["Base"].append(9.0)
        state["selection_trial_count"] = 3
        state["content_hash"] = CHECK.canonical_hash(state)
        write(root, state_path, state)
        failures = CHECK.validate(root)
        self.assertTrue(any("trial_order" in item for item in failures))
        self.assertTrue(any("selection_trial_count" in item for item in failures))
        self.assertTrue(any("selection_trial_sharpes" in item for item in failures))

    def test_runtime_envelope_invalid_utc_and_final_dsr_fail(self) -> None:
        temporary, root = self.clone()
        self.addCleanup(temporary.cleanup)
        envelope = self.envelope(root, timestamp="not-utc")
        envelope["runtime_resolved_parameters_hash"] = "0" * 64
        materialize_trial_bundle(
            root / "reports/m1/evidence/external_strategy_is_trials",
            trial_id="trial-001",
            base_envelope=envelope,
            executor=self.executor(metric_changes={"dsr": 0.99}),
            staging_token="z" * 32,
        )
        self.refresh_state(root, ["trial-001"])
        failures = CHECK.validate(root)
        self.assertTrue(any("runtime_resolved_parameters_hash" in item for item in failures))
        self.assertTrue(any("invalid first_materialized_utc" in item for item in failures))
        self.assertTrue(any("final DSR" in item for item in failures))

    def test_metrics_equity_trade_and_oos_tamper_fail(self) -> None:
        temporary, root = self.clone()
        self.addCleanup(temporary.cleanup)
        self.materialize(root)
        self.refresh_state(root, ["trial-001"])
        result_path = root / "reports/m1/evidence/external_strategy_is_trials/trial-001/trial-001.Base.metrics.json"
        payload = json.loads(result_path.read_text())
        payload["daily_mtm_sharpe"] = 4.0
        result_path.chmod(0o600)
        result_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        result_path.chmod(0o444)
        failures = CHECK.validate(root)
        self.assertTrue(any("invalid materialized trial bundle" in item for item in failures))

    def test_duplicate_original_modified_without_package_and_failed_rescue_fail(self) -> None:
        temporary, root = self.clone()
        self.addCleanup(temporary.cleanup)
        self.materialize(root, trial_id="trial-001", timestamp="2026-07-22T01:00:00Z")
        self.materialize(root, trial_id="trial-002", timestamp="2026-07-22T02:00:00Z")
        self.refresh_state(root, ["trial-001", "trial-002"])
        failures = CHECK.validate(root)
        self.assertTrue(any("more than one original" in item for item in failures))

        temporary2, root2 = self.clone()
        self.addCleanup(temporary2.cleanup)
        self.materialize(root2, trial_id="trial-001", timestamp="2026-07-22T01:00:00Z")
        self.materialize(
            root2,
            trial_id="trial-002",
            timestamp="2026-07-22T02:00:00Z",
            variant_type="modified",
        )
        self.refresh_state(root2, ["trial-001", "trial-002"])
        failures2 = CHECK.validate(root2)
        self.assertTrue(any("lacks preregistered package" in item for item in failures2))
        self.assertTrue(any("cannot rescue failed original" in item for item in failures2))


if __name__ == "__main__":
    unittest.main()
