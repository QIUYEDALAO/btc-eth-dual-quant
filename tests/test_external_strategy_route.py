from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("external_strategy_route_check", ROOT / "scripts/external_strategy_route_check.py")
CHECK = importlib.util.module_from_spec(SPEC)
if SPEC.loader is None:
    raise RuntimeError("checker loader unavailable")
SPEC.loader.exec_module(CHECK)
TRIAL_SPEC = importlib.util.spec_from_file_location("external_strategy_trial_accounting_check", ROOT / "scripts/external_strategy_trial_accounting_check.py")
TRIAL_CHECK = importlib.util.module_from_spec(TRIAL_SPEC)
if TRIAL_SPEC.loader is None:
    raise RuntimeError("trial checker loader unavailable")
TRIAL_SPEC.loader.exec_module(TRIAL_CHECK)


def load(root: Path, name: str) -> dict:
    return json.loads((root / name).read_text())


def write_json(root: Path, name: str, value: dict) -> None:
    (root / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def digest(value: dict) -> str:
    value = copy.deepcopy(value)
    value.pop("content_hash", None)
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


class ExternalStrategyRouteTests(unittest.TestCase):
    def clone_contract(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        for rel in ("config", "reports/m0", "reports/m1/evidence", "external_strategies", "docs/decisions"):
            shutil.copytree(ROOT / rel, root / rel)
        (root / "STRATEGY_TRIAL_LEDGER.yaml").write_bytes((ROOT / "STRATEGY_TRIAL_LEDGER.yaml").read_bytes())
        (root / "THIRD_PARTY_NOTICES.md").write_bytes((ROOT / "THIRD_PARTY_NOTICES.md").read_bytes())
        (root / "reports/m1/U25_SUPERSESSION_AND_EXTERNAL_STRATEGY_ROUTE.md").write_bytes((ROOT / "reports/m1/U25_SUPERSESSION_AND_EXTERNAL_STRATEGY_ROUTE.md").read_bytes())
        for report in (
            "reports/m1/M1A_TREND_BACKTEST_REPORT.md", "reports/m1/M1A_REVIEW_DECISION.md",
            "reports/m1/M1B_EVENT_TIME_REVALIDATION_REPORT.md", "reports/m1/M1B_FINAL_DECISION.md",
            "reports/m1/T3_UNIFIED_METRICS_AND_POLICY_BENCHMARK_REPORT.md",
            "reports/expert/2026-07-10-FABLE5-EXPERT-REVIEW.md",
        ):
            target = root / report
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / report).read_bytes())
        source_impl = ROOT / "src/btc_eth_dual_quant/audit/unified_metrics.py"
        target_impl = root / "src/btc_eth_dual_quant/audit/unified_metrics.py"
        target_impl.parent.mkdir(parents=True)
        target_impl.write_bytes(source_impl.read_bytes())
        candle_impl = ROOT / "src/btc_eth_dual_quant/audit/completed_candle_derivation.py"
        candle_target = root / "src/btc_eth_dual_quant/audit/completed_candle_derivation.py"
        candle_target.write_bytes(candle_impl.read_bytes())
        trial_checker = root / "scripts/external_strategy_trial_accounting_check.py"
        trial_checker.parent.mkdir(parents=True, exist_ok=True)
        trial_checker.write_bytes((ROOT / "scripts/external_strategy_trial_accounting_check.py").read_bytes())
        return temporary, root

    def refresh_adr_hashes(self, root: Path, *keys: str) -> None:
        adr = load(root, "config/adr0016_existing_strategy_route_v1.json")
        paths = {
            "inventory": "config/external_strategy_inventory_v1.json", "screen": "reports/m1/evidence/external_strategy_source_screen_v1.json",
            "freeze": "config/external_strategy_candidate_freeze_v1.json", "unified_is_protocol": "config/external_strategy_unified_is_protocol_v1.json",
            "supersession": "config/u25_existing_strategy_supersession_v1.json", "oos_guard": "config/external_strategy_oos_guard_v1.json",
            "dsr_reference": "config/external_strategy_dsr_reference_trials_v1.json",
        }
        for key in keys:
            adr["exact_hashes"][f"{key}_bytes_sha256"] = hashlib.sha256((root / paths[key]).read_bytes()).hexdigest()
        write_json(root, "config/adr0016_existing_strategy_route_v1.json", adr)

    def test_repository_contract_passes_under_python_optimize(self):
        self.assertEqual(CHECK.validate(ROOT), [])
        result = subprocess.run(["python3", "-O", "scripts/external_strategy_route_check.py"], cwd=ROOT, env={**os.environ, "PYTHONPATH": ".:.deps:src"}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("assert ", (ROOT / "scripts/external_strategy_route_check.py").read_text())

    def test_inventory_license_and_unredistributed_source(self):
        inv = load(ROOT, "config/external_strategy_inventory_v1.json")
        self.assertEqual([x["order"] for x in inv["candidates"]], list(range(1, 21)))
        elliot = inv["candidates"][-1]
        self.assertEqual(elliot["license_status"], "unverified_not_redistributed")
        self.assertFalse(elliot["source_materialized"])
        self.assertFalse((ROOT / "external_strategies/original/20-ElliotV5_SMA/ElliotV5_SMA.py").exists())
        results = {x["id"]: x for x in load(ROOT, "reports/m1/evidence/external_strategy_source_screen_v1.json")["results"]}
        self.assertEqual(results["Bandtastic"]["license_evidence"]["declared_license"], "MIT")
        self.assertIn("Robert Roman", results["Bandtastic"]["license_evidence"]["authors"])
        self.assertEqual(len([x for x in results.values() if x["source_materialized"]]), 19)
        self.assertNotIn("is", inv.get("runtime_identity", {}))
        protocol = load(ROOT, "config/external_strategy_unified_is_protocol_v1.json")
        self.assertEqual(inv["calendar_authority"], {"path":"config/external_strategy_unified_is_protocol_v1.json", "content_hash":protocol["content_hash"]})

    def test_six_candidate_ast_declarations_are_complete_and_zero_result(self):
        results = {x["id"]: x for x in load(ROOT, "reports/m1/evidence/external_strategy_source_screen_v1.json")["results"]}
        expected_timeframes = {"Supertrend":"1h","Strategy001":"5m","UniversalMACD":"5m","Bandtastic":"15m","Diamond":"5m","Heracles":"4h"}
        for candidate_id, timeframe in expected_timeframes.items():
            declaration = results[candidate_id]["source_declaration"]
            self.assertEqual(declaration["assignments"]["timeframe"], timeframe)
            self.assertTrue(declaration["strategy_classes"])
            self.assertIn("populate_indicators", declaration["behavior_methods"])
            self.assertFalse(declaration["position_increase_capability"])
            self.assertFalse(declaration["behavior_methods"]["leverage"])
            self.assertIsNone(declaration["runtime_effective_settings_hash"])
            self.assertIsNone(declaration["runtime_resolved_parameters_hash"])
        strategy001 = results["Strategy001"]["source_declaration"]["assignments"]
        for name in ("process_only_new_candles", "startup_candle_count", "ignore_roi_if_entry_signal"):
            self.assertIn(name, strategy001)

    def test_unified_protocol_trial_and_parameter_preconditions(self):
        protocol = load(ROOT, "config/external_strategy_unified_is_protocol_v1.json")
        self.assertEqual(protocol["content_hash"], digest(protocol))
        self.assertEqual(protocol["multiple_testing"]["dsr_trial_count_formula"], "3 + selection_trial_count")
        self.assertEqual(protocol["execution_counters"], {"freqtrade_loads": 0, "causal_validations": 0, "is_trials": 0})
        freeze = load(ROOT, "config/external_strategy_candidate_freeze_v1.json")
        self.assertEqual((freeze["required_external_parameter_file_count"], freeze["required_config_override_count"]), (0, 0))
        self.assertIsNone(freeze["observed_external_parameter_file_count"])
        self.assertIsNone(freeze["observed_config_override_count"])
        pending = {x["id"] for x in freeze["frozen_candidates"] if x["runtime_resolution_status"] == "runtime_resolution_pending"}
        self.assertEqual(pending, {"Supertrend", "Diamond", "Heracles"})
        self.assertTrue(all(x["runtime_resolved_parameters_hash"] is None for x in freeze["frozen_candidates"]))
        self.assertTrue(all(x["runtime_effective_settings_hash"] is None for x in freeze["frozen_candidates"]))
        self.assertTrue(all(x["base_adapter_hash"] is None for x in freeze["frozen_candidates"]))
        self.assertTrue(all(set(x["modification_package"]) == {"id","before_hash","after_hash","atomic_changes","package_hash"} for x in freeze["frozen_candidates"]))

    def test_data_benchmark_portfolio_and_selection_contracts(self):
        protocol = load(ROOT, "config/external_strategy_unified_is_protocol_v1.json")
        self.assertEqual(protocol["portfolio"]["stake_amount_usdt"], "10000")
        self.assertEqual(protocol["portfolio"]["maximum_open_trades"], 5)
        self.assertEqual(protocol["selection_order"], ["all_hard_gates_pass","base_dsr_desc","costx2_dsr_desc","costx2_daily_mtm_sharpe_desc","costx2_max_drawdown_asc","turnover_asc","candidate_id_asc"])
        authority = load(ROOT, "config/external_strategy_data_authority_v1.json")
        self.assertEqual(len(authority["bound_manifests"]), 16)
        self.assertEqual(authority["result_access"]["oos_values_decoded"], 0)
        benchmark = load(ROOT, "config/external_strategy_benchmark_v1.json")
        self.assertFalse(benchmark["guards"]["candidate_performance_result_materialized"])
        calendar = protocol["calendar"]
        self.assertEqual((calendar["full_days"], calendar["is_days"], calendar["sealed_oos_days"]), (2191, 1533, 658))
        self.assertEqual(calendar["actual_sealed_oos_fraction"], "0.300319488818")
        dsr = load(ROOT, "config/external_strategy_dsr_reference_trials_v1.json")
        self.assertEqual(dsr["required_trial_count"], 3)
        self.assertEqual(dsr["historical"]["Base"], ["0.7367", "7.1534", "0.7882"])

    def test_selection_key_uses_every_frozen_tie_break_in_order(self):
        base = {"all_hard_gates_pass":True,"base_dsr":0.96,"costx2_dsr":0.96,"costx2_daily_mtm_sharpe":1.1,"costx2_max_drawdown":0.1,"turnover":2.0,"candidate_id":"B"}
        fields = [
            ("all_hard_gates_pass", False), ("base_dsr", 0.95), ("costx2_dsr", 0.95),
            ("costx2_daily_mtm_sharpe", 1.0), ("costx2_max_drawdown", 0.11),
            ("turnover", 2.1), ("candidate_id", "C"),
        ]
        for field, losing_value in fields:
            loser = dict(base)
            loser[field] = losing_value
            self.assertLess(CHECK.selection_key(base), CHECK.selection_key(loser), field)

    def test_root_freeze_blocks_coordinated_child_rehash(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        protocol = load(root, "config/external_strategy_unified_is_protocol_v1.json")
        protocol["portfolio"]["stake_amount_usdt"] = "20000"
        protocol["content_hash"] = digest(protocol)
        write_json(root, "config/external_strategy_unified_is_protocol_v1.json", protocol)
        adr = load(root, "config/adr0016_existing_strategy_route_v1.json")
        adr["exact_hashes"]["unified_is_protocol_content_hash"] = protocol["content_hash"]
        adr["exact_hashes"]["unified_is_protocol_bytes_sha256"] = hashlib.sha256((root / "config/external_strategy_unified_is_protocol_v1.json").read_bytes()).hexdigest()
        write_json(root, "config/adr0016_existing_strategy_route_v1.json", adr)
        root_freeze = load(root, "config/adr0016_pre_runtime_contract_freeze_v1.json")
        root_freeze["contract_files"]["config/external_strategy_unified_is_protocol_v1.json"] = hashlib.sha256((root / "config/external_strategy_unified_is_protocol_v1.json").read_bytes()).hexdigest()
        root_freeze["contract_files"]["config/adr0016_existing_strategy_route_v1.json"] = hashlib.sha256((root / "config/adr0016_existing_strategy_route_v1.json").read_bytes()).hexdigest()
        root_freeze["canonical_content_hashes"]["unified_is_protocol"] = protocol["content_hash"]
        write_json(root, "config/adr0016_pre_runtime_contract_freeze_v1.json", root_freeze)
        self.assertTrue(any("root freeze byte hash mismatch" in value for value in CHECK.validate(root)))

    def test_recomputed_document_hash_cannot_bypass_adr_anchor(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        freeze = load(root, "config/external_strategy_candidate_freeze_v1.json")
        freeze["selection_trial_count"] = 1
        freeze["content_hash"] = digest(freeze)
        write_json(root, "config/external_strategy_candidate_freeze_v1.json", freeze)
        self.assertTrue(any("ADR exact byte hash mismatch" in x for x in CHECK.validate(root)))

    def test_local_source_and_inventory_commit_tamper_fail(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        source = root / "external_strategies/original/01-Supertrend/Supertrend.py"
        source.write_bytes(source.read_bytes() + b"\n# tamper\n")
        self.assertTrue(any("local/upstream source identity mismatch" in x for x in CHECK.validate(root)))
        inv = load(root, "config/external_strategy_inventory_v1.json")
        inv["repositories"]["official"]["commit"] = "0" * 40
        write_json(root, "config/external_strategy_inventory_v1.json", inv)
        self.assertTrue(any("inventory" in x or "commit mismatch" in x for x in CHECK.validate(root)))

    def test_missing_archive_member_fails_even_after_hash_recomputation(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        archive = root / "external_strategies/upstream_archives/official.tar.gz"
        replacement = root / "replacement.tar.gz"
        with tarfile.open(archive, "r:gz") as source, tarfile.open(replacement, "w:gz") as target:
            for member in source.getmembers():
                if member.name.endswith("/user_data/strategies/Supertrend.py"):
                    continue
                target.addfile(member, source.extractfile(member) if member.isfile() else None)
        replacement.replace(archive)
        evidence = load(root, "reports/m1/evidence/external_strategy_source_screen_v1.json")
        new_archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
        for item in evidence["results"]:
            if item["repository_archive_path"] == "external_strategies/upstream_archives/official.tar.gz":
                item["repository_archive_sha256"] = new_archive_hash
        evidence["content_hash"] = digest(evidence)
        write_json(root, "reports/m1/evidence/external_strategy_source_screen_v1.json", evidence)
        freeze = load(root, "config/external_strategy_candidate_freeze_v1.json")
        freeze["screen_content_hash"] = evidence["content_hash"]
        freeze["content_hash"] = digest(freeze)
        write_json(root, "config/external_strategy_candidate_freeze_v1.json", freeze)
        self.refresh_adr_hashes(root, "screen", "freeze")
        self.assertTrue(any("candidate archive member missing" in x for x in CHECK.validate(root)))

    def test_trial_and_oos_tamper_fail(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        protocol = load(root, "config/external_strategy_unified_is_protocol_v1.json")
        protocol["multiple_testing"]["selection_trial_count"] = 1
        protocol["content_hash"] = digest(protocol)
        write_json(root, "config/external_strategy_unified_is_protocol_v1.json", protocol)
        self.assertTrue(CHECK.validate(root))
        oos = load(root, "config/external_strategy_oos_guard_v1.json")
        oos["oos_authorized"] = True
        write_json(root, "config/external_strategy_oos_guard_v1.json", oos)
        self.assertTrue(any("OOS" in x or "ADR exact" in x for x in CHECK.validate(root)))

    def test_calendar_dsr_and_authoritative_report_tamper_fail(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        protocol = load(root, "config/external_strategy_unified_is_protocol_v1.json")
        protocol["calendar"]["full_days"] = 2190
        write_json(root, "config/external_strategy_unified_is_protocol_v1.json", protocol)
        self.assertTrue(any("calendar" in value for value in CHECK.validate(root)))
        temporary_inventory, root_inventory = self.clone_contract()
        self.addCleanup(temporary_inventory.cleanup)
        inventory = load(root_inventory, "config/external_strategy_inventory_v1.json")
        inventory["calendar_authority"]["content_hash"] = "0" * 64
        write_json(root_inventory, "config/external_strategy_inventory_v1.json", inventory)
        self.assertTrue(any("inventory/unified protocol calendar authority mismatch" in value for value in CHECK.validate(root_inventory)))
        temporary2, root2 = self.clone_contract()
        self.addCleanup(temporary2.cleanup)
        dsr = load(root2, "config/external_strategy_dsr_reference_trials_v1.json")
        dsr["historical"]["Base"][0] = "9.9"
        write_json(root2, "config/external_strategy_dsr_reference_trials_v1.json", dsr)
        self.assertTrue(any("DSR" in value for value in CHECK.validate(root2)))
        temporary3, root3 = self.clone_contract()
        self.addCleanup(temporary3.cleanup)
        report = root3 / "reports/m1/M1A_TREND_BACKTEST_REPORT.md"
        report.write_bytes(report.read_bytes() + b"\ntamper\n")
        self.assertTrue(any("DSR authoritative report hash mismatch" in value for value in CHECK.validate(root3)))

    def test_secret_and_diff_scans_keep_upstream_boundaries(self):
        scanner = (ROOT / "scripts/m0_secret_scan.py").read_text()
        self.assertIn('path.startswith("external_strategies/original/")', scanner)
        selector = (ROOT / "scripts/pr_ci_selective_validate.sh").read_text()
        self.assertIn("git diff --check \"$BASE_SHA\" HEAD -- . ':(exclude)external_strategies/original/**'", selector)

    def materialize_valid_trial(self, root: Path, *, status: str = "failed", variant_type: str = "original") -> tuple[Path, dict]:
        directory = root / "reports/m1/evidence/external_strategy_is_trials"
        freeze = load(root, "config/external_strategy_candidate_freeze_v1.json")
        candidate = freeze["frozen_candidates"][0]
        candidate["adapter_hash"] = "a" * 64
        candidate["base_adapter_hash"] = "a" * 64
        candidate["runtime_effective_settings_hash"] = "b" * 64
        candidate["runtime_resolved_parameters_hash"] = "c" * 64
        freeze["selection_trial_count"] = 1
        freeze["content_hash"] = digest(freeze)
        write_json(root, "config/external_strategy_candidate_freeze_v1.json", freeze)
        protocol = load(root, "config/external_strategy_unified_is_protocol_v1.json")
        protocol["multiple_testing"]["selection_trial_count"] = 1
        protocol["content_hash"] = digest(protocol)
        write_json(root, "config/external_strategy_unified_is_protocol_v1.json", protocol)
        dsr = load(root, "config/external_strategy_dsr_reference_trials_v1.json")
        dsr["selection_trial_count"] = 1
        dsr["required_trial_count"] = 4
        dsr["selection_trial_sharpes"] = {"Base": [0.0], "CostX2": [0.0]}
        dsr["canonical_content_hash"] = CHECK.canonical_named_hash(dsr, "canonical_content_hash")
        write_json(root, "config/external_strategy_dsr_reference_trials_v1.json", dsr)
        authority = load(root, "config/external_strategy_data_authority_v1.json")
        benchmark = load(root, "config/external_strategy_benchmark_v1.json")
        result_files = []
        for scenario in ("Base", "CostX2", "StressA", "StressB"):
            for kind in ("trades", "equity", "metrics"):
                name = f"trial-001.{scenario}.{kind}.json"
                payload = {
                    "schema_version":"external-strategy-is-result-v1", "trial_id":"trial-001",
                    "candidate_id":candidate["id"], "variant_id":"original-v1", "variant_type":variant_type,
                    "scenario":scenario, "kind":kind, "candidate_freeze_hash":freeze["content_hash"],
                    "unified_is_protocol_hash":protocol["content_hash"],
                    "data_authority_hash":authority["canonical_content_hash"],
                    "benchmark_contract_hash":benchmark["canonical_content_hash"],
                    "dsr_reference_hash":dsr["canonical_content_hash"],
                    "base_adapter_hash":candidate["base_adapter_hash"],
                    "variant_executable_hash":candidate["base_adapter_hash"],
                }
                if kind == "trades":
                    payload["trades"] = []
                elif kind == "equity":
                    anchor = date(2020, 6, 30)
                    payload["points"] = [
                        {"day":str(anchor + timedelta(days=offset)), "equity":100000.0}
                        for offset in range(1534)
                    ]
                else:
                    payload.update({
                        "net_return":0.0, "daily_mtm_sharpe":0.0,
                        "psr":0.0, "dsr":0.0, "max_drawdown":0.0, "completed_trades":0,
                        "delete_best_3_return":0.0, "profitable_subperiod_count":0,
                        "equal_weight_benchmark":{"net_return":0.0,"daily_mtm_sharpe":0.0,"max_drawdown":0.0},
                        "risk_matched_benchmark":{"net_return":0.0,"daily_mtm_sharpe":0.0,"max_drawdown":0.0},
                        "hard_gate_status":"pass" if status == "pass" else "failed",
                    })
                write_json(root, str((directory / name).relative_to(root)), payload)
                result_files.append({
                    "path": name, "kind": kind, "scenario": scenario,
                    "byte_sha256": hashlib.sha256((directory / name).read_bytes()).hexdigest(),
                    "semantic_hash": TRIAL_CHECK.semantic_hash(payload),
                })
        package = candidate["modification_package"]
        manifest = {
            "trial_id":"trial-001","candidate_id":candidate["id"],"variant_id":"original-v1","variant_type":variant_type,
            "source_hash":candidate["source_sha256"],"source_declaration_hash":candidate["source_declaration_hash"],
            "adapter_hash":candidate["adapter_hash"],"base_adapter_hash":candidate["base_adapter_hash"],
            "variant_executable_hash":candidate["base_adapter_hash"],"runtime_effective_settings_hash":candidate["runtime_effective_settings_hash"],
            "runtime_resolved_parameters_hash":candidate["runtime_resolved_parameters_hash"],
            "candidate_freeze_hash":freeze["content_hash"],"unified_is_protocol_hash":protocol["content_hash"],
            "data_authority_hash":authority["canonical_content_hash"],"benchmark_contract_hash":benchmark["canonical_content_hash"],
            "dsr_reference_hash":dsr["canonical_content_hash"],"modification_package_id":package["id"],
            "modification_package_hash":package["package_hash"],"first_materialized_utc":"2030-01-01T00:00:00Z",
            "performance_materialized":True,"cost_scenarios":["Base","CostX2","StressA","StressB"],
            "status":status,"append_only":True,"result_files":result_files,
        }
        path = directory / "trial-001.trial.json"
        write_json(root, str(path.relative_to(root)), manifest)
        ledger = yaml.safe_load((root / "STRATEGY_TRIAL_LEDGER.yaml").read_text())
        ledger["rules"]["selection_trial_count"] = 1
        ledger["rules"]["selection_trial_manifest_hashes"] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()}
        (root / "STRATEGY_TRIAL_LEDGER.yaml").write_text(yaml.safe_dump(ledger, sort_keys=False))
        return path, manifest

    def mutate_result(self, root: Path, path: Path, manifest: dict, scenario: str, kind: str, **changes: object) -> None:
        descriptor = next(item for item in manifest["result_files"] if item["scenario"] == scenario and item["kind"] == kind)
        result_path = path.parent / descriptor["path"]
        payload = load(root, str(result_path.relative_to(root)))
        payload.update(changes)
        write_json(root, str(result_path.relative_to(root)), payload)
        descriptor["byte_sha256"] = hashlib.sha256(result_path.read_bytes()).hexdigest()
        descriptor["semantic_hash"] = TRIAL_CHECK.semantic_hash(payload)
        write_json(root, str(path.relative_to(root)), manifest)

    def add_unmaterialized_modified(self, root: Path, path: Path, original: dict, timestamp: str) -> None:
        modified = copy.deepcopy(original)
        modified.update({
            "trial_id":"trial-002", "variant_id":"modified-v1", "variant_type":"modified",
            "first_materialized_utc":timestamp, "performance_materialized":False,
            "status":"failed", "result_files":[],
        })
        write_json(root, str((path.parent / "trial-002.trial.json").relative_to(root)), modified)

    def test_trial_accounting_zero_and_single_four_cost_trial(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        self.assertEqual(TRIAL_CHECK.validate(root), [])
        path, manifest = self.materialize_valid_trial(root)
        self.assertEqual(TRIAL_CHECK.validate(root), [])
        manifest["runtime_resolved_parameters_hash"] = None
        write_json(root, str(path.relative_to(root)), manifest)
        self.assertTrue(any("runtime hash missing" in value for value in TRIAL_CHECK.validate(root)))

    def test_trial_accounting_recomputes_metrics_and_rejects_flat_nonzero_sharpe(self):
        fields = {
            "daily_mtm_sharpe": 1.25,
            "net_return": 0.01,
            "psr": 0.5,
            "max_drawdown": 0.1,
        }
        for field, value in fields.items():
            with self.subTest(field=field):
                temporary, root = self.clone_contract()
                self.addCleanup(temporary.cleanup)
                path, manifest = self.materialize_valid_trial(root)
                self.mutate_result(root, path, manifest, "Base", "metrics", **{field: value})
                self.assertTrue(any(f"reconciliation mismatch: trial-001:Base:{field}" in item for item in TRIAL_CHECK.validate(root)))

    def test_trial_accounting_recomputes_trade_count_dsr_and_excludes_stress(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        path, manifest = self.materialize_valid_trial(root)
        self.mutate_result(root, path, manifest, "Base", "metrics", completed_trades=1)
        self.assertTrue(any("metrics/trades completed count mismatch" in item for item in TRIAL_CHECK.validate(root)))

        temporary2, root2 = self.clone_contract()
        self.addCleanup(temporary2.cleanup)
        path2, manifest2 = self.materialize_valid_trial(root2)
        self.mutate_result(root2, path2, manifest2, "Base", "metrics", dsr=0.25)
        self.assertTrue(any("DSR/equity reconciliation mismatch" in item for item in TRIAL_CHECK.validate(root2)))

        temporary3, root3 = self.clone_contract()
        self.addCleanup(temporary3.cleanup)
        self.materialize_valid_trial(root3)
        dsr = load(root3, "config/external_strategy_dsr_reference_trials_v1.json")
        dsr["selection_trial_sharpes"]["StressA"] = [0.0]
        write_json(root3, "config/external_strategy_dsr_reference_trials_v1.json", dsr)
        self.assertTrue(any("exactly Base and CostX2" in item for item in TRIAL_CHECK.validate(root3)))

    def test_trial_accounting_rejects_unmaterialized_or_failed_original_rescue_and_bad_order(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        path, original = self.materialize_valid_trial(root, status="pass")
        original["performance_materialized"] = False
        original["result_files"] = []
        write_json(root, str(path.relative_to(root)), original)
        self.add_unmaterialized_modified(root, path, original, "2031-01-01T00:00:00Z")
        self.assertTrue(any("cannot rescue absent, unmaterialized" in item for item in TRIAL_CHECK.validate(root)))

        for scenario in ("Base", "CostX2"):
            with self.subTest(scenario=scenario):
                temporary_case, root_case = self.clone_contract()
                self.addCleanup(temporary_case.cleanup)
                path_case, original_case = self.materialize_valid_trial(root_case, status="pass")
                self.mutate_result(root_case, path_case, original_case, scenario, "metrics", hard_gate_status="failed")
                self.add_unmaterialized_modified(root_case, path_case, original_case, "2031-01-01T00:00:00Z")
                self.assertTrue(any("cannot rescue absent, unmaterialized" in item for item in TRIAL_CHECK.validate(root_case)))

        for timestamp in ("2029-01-01T00:00:00Z", "2030-01-01T00:00:00Z"):
            with self.subTest(timestamp=timestamp):
                temporary_case, root_case = self.clone_contract()
                self.addCleanup(temporary_case.cleanup)
                path_case, original_case = self.materialize_valid_trial(root_case, status="pass")
                self.add_unmaterialized_modified(root_case, path_case, original_case, timestamp)
                self.assertTrue(any("strictly after original" in item for item in TRIAL_CHECK.validate(root_case)))

    def test_trial_accounting_rejects_warmup_oos_and_cross_boundary_trades(self):
        cases = [
            ("2020-06-30T00:00:00Z", "2020-06-30T01:00:00Z"),
            ("2024-09-10T23:00:00Z", "2024-09-11T00:00:00Z"),
            ("2024-09-11T00:00:00Z", "2024-09-11T01:00:00Z"),
            ("2024-09-10T23:30:00Z", "2024-09-11T00:30:00Z"),
        ]
        for opened, closed in cases:
            with self.subTest(opened=opened, closed=closed):
                temporary, root = self.clone_contract()
                self.addCleanup(temporary.cleanup)
                path, manifest = self.materialize_valid_trial(root)
                trade = {"trade_id":"t1","pair":"BTC/USDT","open_time":opened,"close_time":closed,"stake_amount":10000.0,"position_increase":False}
                self.mutate_result(root, path, manifest, "Base", "trades", trades=[trade])
                self.mutate_result(root, path, manifest, "Base", "metrics", completed_trades=1)
                self.assertTrue(any("trade outside sealed IS interval" in item for item in TRIAL_CHECK.validate(root)))

    def test_trial_accounting_rejects_oos_equity_observation_and_executable_drift(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        path, manifest = self.materialize_valid_trial(root)
        descriptor = next(item for item in manifest["result_files"] if item["scenario"] == "Base" and item["kind"] == "equity")
        result_path = path.parent / descriptor["path"]
        payload = load(root, str(result_path.relative_to(root)))
        payload["points"].append({"day":"2024-09-11", "equity":100000.0})
        write_json(root, str(result_path.relative_to(root)), payload)
        descriptor["byte_sha256"] = hashlib.sha256(result_path.read_bytes()).hexdigest()
        descriptor["semantic_hash"] = TRIAL_CHECK.semantic_hash(payload)
        manifest["variant_executable_hash"] = "d" * 64
        write_json(root, str(path.relative_to(root)), manifest)
        failures = TRIAL_CHECK.validate(root)
        self.assertTrue(any("equity boundary/count mismatch" in item for item in failures))
        self.assertTrue(any("original executable identity mismatch" in item for item in failures))

    def test_trial_accounting_rejects_path_hash_reuse_and_failed_rescue(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        path, manifest = self.materialize_valid_trial(root, status="failed")
        manifest["result_files"][0]["path"] = "../escape.json"
        write_json(root, str(path.relative_to(root)), manifest)
        self.assertTrue(any("unsafe trial result path" in value for value in TRIAL_CHECK.validate(root)))
        manifest["result_files"][0]["path"] = "trial-001.Base.trades.json"
        manifest["result_files"][0]["byte_sha256"] = "0" * 64
        write_json(root, str(path.relative_to(root)), manifest)
        self.assertTrue(any("byte hash mismatch" in value for value in TRIAL_CHECK.validate(root)))
        result_path = root / "reports/m1/evidence/external_strategy_is_trials/trial-001.Base.trades.json"
        manifest["result_files"][0]["byte_sha256"] = hashlib.sha256(result_path.read_bytes()).hexdigest()
        manifest["result_files"][0]["semantic_hash"] = "0" * 64
        write_json(root, str(path.relative_to(root)), manifest)
        self.assertTrue(any("semantic hash mismatch" in value for value in TRIAL_CHECK.validate(root)))
        manifest["variant_type"] = "modified"
        write_json(root, str(path.relative_to(root)), manifest)
        self.assertTrue(any("cannot rescue absent, unmaterialized, failed, or unreconciled original" in value for value in TRIAL_CHECK.validate(root)))

    def test_trial_accounting_rejects_exact_contract_and_cost_drift(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        path, manifest = self.materialize_valid_trial(root, status="pass")
        manifest["source_hash"] = "0" * 64
        manifest["cost_scenarios"] = ["Base"]
        write_json(root, str(path.relative_to(root)), manifest)
        failures = TRIAL_CHECK.validate(root)
        self.assertTrue(any("exact hash mismatch" in value for value in failures))
        self.assertTrue(any("four-cost" in value for value in failures))

    def test_trial_accounting_rejects_orphan_duplicate_and_count_drift(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        directory = root / "reports/m1/evidence/external_strategy_is_trials"
        (directory / "orphan.metrics.json").write_text("{}\n")
        self.assertTrue(any("orphan IS result" in value for value in TRIAL_CHECK.validate(root)))
        ledger = yaml.safe_load((root / "STRATEGY_TRIAL_LEDGER.yaml").read_text())
        ledger["rules"]["selection_trial_count"] = 1
        (root / "STRATEGY_TRIAL_LEDGER.yaml").write_text(yaml.safe_dump(ledger, sort_keys=False))
        self.assertTrue(any("selection_trial_count drift" in value for value in TRIAL_CHECK.validate(root)))

    def test_trial_accounting_rejects_duplicate_variant_manifests_and_four_modified_candidates(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        path, manifest = self.materialize_valid_trial(root, status="pass")
        directory = path.parent
        duplicate = copy.deepcopy(manifest)
        duplicate.update({"trial_id":"trial-002", "variant_id":"original-v2", "performance_materialized":False, "result_files":[]})
        write_json(root, str((directory / "trial-002.trial.json").relative_to(root)), duplicate)
        self.assertTrue(any("more than one original manifest" in value for value in TRIAL_CHECK.validate(root)))

        for index, candidate in enumerate(load(root, "config/external_strategy_candidate_freeze_v1.json")["frozen_candidates"][:4], start=10):
            modified = copy.deepcopy(duplicate)
            modified.update({"trial_id":f"trial-{index}", "candidate_id":candidate["id"], "variant_id":"modified-v1", "variant_type":"modified"})
            write_json(root, str((directory / f"trial-{index}.trial.json").relative_to(root)), modified)
        duplicate_modified = copy.deepcopy(modified)
        duplicate_modified.update({"trial_id":"trial-20", "variant_id":"modified-v2"})
        write_json(root, str((directory / "trial-20.trial.json").relative_to(root)), duplicate_modified)
        failures = TRIAL_CHECK.validate(root)
        self.assertTrue(any("more than three modified candidates" in value for value in failures))
        self.assertTrue(any("more than one modified manifest" in value for value in failures))

    def test_trial_accounting_rejects_invalid_utc_envelope_empty_result_and_dsr_drift(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        path, manifest = self.materialize_valid_trial(root)
        manifest["first_materialized_utc"] = "2030-01-01T00:00:00+08:00"
        write_json(root, str(path.relative_to(root)), manifest)
        self.assertTrue(any("invalid first_materialized_utc" in value for value in TRIAL_CHECK.validate(root)))

        manifest["first_materialized_utc"] = "2030-01-01T00:00:00Z"
        manifest["performance_materialized"] = 1
        write_json(root, str(path.relative_to(root)), manifest)
        self.assertTrue(any("not strict boolean" in value for value in TRIAL_CHECK.validate(root)))

        manifest["performance_materialized"] = True
        descriptor = next(item for item in manifest["result_files"] if item["scenario"] == "Base" and item["kind"] == "metrics")
        result = path.parent / descriptor["path"]
        payload = load(root, str(result.relative_to(root)))
        payload["scenario"] = "CostX2"
        write_json(root, str(result.relative_to(root)), payload)
        descriptor["byte_sha256"] = hashlib.sha256(result.read_bytes()).hexdigest()
        descriptor["semantic_hash"] = TRIAL_CHECK.semantic_hash(payload)
        write_json(root, str(path.relative_to(root)), manifest)
        self.assertTrue(any("result envelope mismatch" in value for value in TRIAL_CHECK.validate(root)))

        write_json(root, str(result.relative_to(root)), {})
        descriptor["byte_sha256"] = hashlib.sha256(result.read_bytes()).hexdigest()
        descriptor["semantic_hash"] = TRIAL_CHECK.semantic_hash({})
        write_json(root, str(path.relative_to(root)), manifest)
        self.assertTrue(any("result envelope fields missing" in value for value in TRIAL_CHECK.validate(root)))

        dsr = load(root, "config/external_strategy_dsr_reference_trials_v1.json")
        dsr["selection_trial_sharpes"]["Base"] = []
        write_json(root, "config/external_strategy_dsr_reference_trials_v1.json", dsr)
        self.assertTrue(any("DSR selection Sharpe sequence" in value for value in TRIAL_CHECK.validate(root)))

    def test_trial_accounting_rejects_dsr_sequence_order_drift(self):
        temporary, root = self.clone_contract()
        self.addCleanup(temporary.cleanup)
        path, first = self.materialize_valid_trial(root, status="pass")
        directory = path.parent
        second = copy.deepcopy(first)
        second.update({"trial_id":"trial-002", "variant_id":"modified-v1", "variant_type":"modified", "first_materialized_utc":"2029-01-01T00:00:00Z"})
        second_files = []
        for descriptor in first["result_files"]:
            source = directory / descriptor["path"]
            payload = json.loads(source.read_text())
            payload.update({"trial_id":"trial-002", "variant_id":"modified-v1", "variant_type":"modified"})
            if payload["kind"] == "metrics" and payload["scenario"] in {"Base", "CostX2"}:
                payload["daily_mtm_sharpe"] = 2.0
            name = descriptor["path"].replace("trial-001", "trial-002")
            write_json(root, str((directory / name).relative_to(root)), payload)
            second_files.append({**descriptor, "path":name, "byte_sha256":hashlib.sha256((directory / name).read_bytes()).hexdigest(), "semantic_hash":TRIAL_CHECK.semantic_hash(payload)})
        second["result_files"] = second_files
        write_json(root, str((directory / "trial-002.trial.json").relative_to(root)), second)
        dsr = load(root, "config/external_strategy_dsr_reference_trials_v1.json")
        dsr["selection_trial_count"], dsr["required_trial_count"] = 2, 5
        dsr["selection_trial_sharpes"] = {"Base":[1.25, 2.0], "CostX2":[1.0, 2.0]}
        write_json(root, "config/external_strategy_dsr_reference_trials_v1.json", dsr)
        self.assertTrue(any("DSR selection Sharpe sequence mismatch" in value for value in TRIAL_CHECK.validate(root)))


if __name__ == "__main__":
    unittest.main()
