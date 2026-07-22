from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "external_strategy_original_is_authority_check",
    ROOT / "scripts/external_strategy_original_is_authority_check.py",
)
CHECK = importlib.util.module_from_spec(SPEC)
if SPEC.loader is None:
    raise RuntimeError("authority checker loader unavailable")
SPEC.loader.exec_module(CHECK)


def load(root: Path, relative: str) -> dict:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def write(root: Path, relative: str, value: dict) -> None:
    (root / relative).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class OriginalISAuthorityTests(unittest.TestCase):
    def clone(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        for relative in ("config", "reports/expert/evidence", "reports/m1/evidence/external_strategy_runtime", "reports/m1/evidence/external_strategy_boundary_authority", "external_strategies/adapters"):
            shutil.copytree(ROOT / relative, root / relative)
        return temporary, root

    def test_repository_authority_passes_normal_and_optimized_python(self) -> None:
        self.assertEqual(CHECK.validate(ROOT), [])
        result = subprocess.run(
            ["python3", "-O", "scripts/external_strategy_original_is_authority_check.py"],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": ".:.deps:src"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("assert ", (ROOT / "scripts/external_strategy_original_is_authority_check.py").read_text())

    def test_authority_rehash_cannot_bypass_exact_root(self) -> None:
        temporary, root = self.clone()
        self.addCleanup(temporary.cleanup)
        authority = load(root, "config/external_strategy_original_is_authority_v1.json")
        authority["execution_contract"]["original_trial_per_candidate"] = 2
        authority["content_hash"] = CHECK.canonical_hash(authority)
        write(root, "config/external_strategy_original_is_authority_v1.json", authority)
        failures = CHECK.validate(root)
        self.assertTrue(any("exact root hash mismatch" in item for item in failures))
        self.assertTrue(any("execution contract drift" in item for item in failures))

    def test_runtime_candidate_and_causal_tamper_fail_even_with_parent_rehash(self) -> None:
        temporary, root = self.clone()
        self.addCleanup(temporary.cleanup)
        route_path = "reports/m1/evidence/external_strategy_runtime/runtime_route_manifest.json"
        route = load(root, route_path)
        route["candidates"][0]["runtime_resolved_parameters_hash"] = "0" * 64
        route["content_hash"] = CHECK.canonical_hash(route)
        write(root, route_path, route)
        authority = load(root, "config/external_strategy_original_is_authority_v1.json")
        authority["bindings"]["runtime_route"]["byte_sha256"] = CHECK.sha256_bytes(root / route_path)
        authority["bindings"]["runtime_route"]["content_hash"] = route["content_hash"]
        authority["content_hash"] = CHECK.canonical_hash(authority)
        write(root, "config/external_strategy_original_is_authority_v1.json", authority)
        failures = CHECK.validate(root)
        self.assertTrue(any("exact root hash mismatch" in item for item in failures))
        self.assertTrue(any("runtime candidate exact hash drift" in item for item in failures))

    def test_oos_boundary_and_isolation_drift_fail(self) -> None:
        temporary, root = self.clone()
        self.addCleanup(temporary.cleanup)
        oos_path = "config/external_strategy_oos_guard_v1.json"
        oos = load(root, oos_path)
        oos["oos_authorized"] = True
        write(root, oos_path, oos)
        failures = CHECK.validate(root)
        self.assertTrue(any("OOS guard" in item for item in failures))

        temporary2, root2 = self.clone()
        self.addCleanup(temporary2.cleanup)
        boundary_path = "reports/m1/evidence/external_strategy_boundary_authority/completed_boundary_authority.json"
        boundary = load(root2, boundary_path)
        boundary["runtime_consumption_contract"]["append_to_candidate_ohlcv"] = True
        boundary["content_hash"] = CHECK.canonical_hash(boundary)
        write(root2, boundary_path, boundary)
        authority = load(root2, "config/external_strategy_original_is_authority_v1.json")
        authority["bindings"]["completed_boundary_authority"]["byte_sha256"] = CHECK.sha256_bytes(root2 / boundary_path)
        authority["bindings"]["completed_boundary_authority"]["content_hash"] = boundary["content_hash"]
        authority["content_hash"] = CHECK.canonical_hash(authority)
        write(root2, "config/external_strategy_original_is_authority_v1.json", authority)
        failures2 = CHECK.validate(root2)
        self.assertTrue(any("permits OHLCV append" in item for item in failures2))

    def test_candidate_order_permission_and_review_drift_fail(self) -> None:
        temporary, root = self.clone()
        self.addCleanup(temporary.cleanup)
        authority = load(root, "config/external_strategy_original_is_authority_v1.json")
        authority["runtime_candidates"] = list(reversed(copy.deepcopy(authority["runtime_candidates"])))
        authority["permissions"]["oos"] = True
        authority["bindings"]["pr119_review"]["reviewed_head"] = "0" * 40
        authority["content_hash"] = CHECK.canonical_hash(authority)
        write(root, "config/external_strategy_original_is_authority_v1.json", authority)
        failures = CHECK.validate(root)
        self.assertTrue(any("candidate order" in item for item in failures))
        self.assertTrue(any("prohibited permission enabled: oos" in item for item in failures))
        self.assertTrue(any("reviewed head drift" in item for item in failures))


if __name__ == "__main__":
    unittest.main()
