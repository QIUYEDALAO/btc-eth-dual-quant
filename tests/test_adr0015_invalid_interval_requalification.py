from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from btc_eth_dual_quant.data.invalid_interval_quarantine import ADR0015_MANIFEST_TYPES
from btc_eth_dual_quant.data.lifecycle_artifacts import V4_MANIFEST_TYPES
from scripts import adr0015_invalid_interval_requalification as run_stage
from scripts.liquid_universe_v4_requalification import assert_three_way


def artifacts(value: str = "same") -> dict:
    names = V4_MANIFEST_TYPES | set(ADR0015_MANIFEST_TYPES)
    return {name: {"content_hash": f"{value}:{name}"} for name in names}


class ADR0015RequalificationTests(unittest.TestCase):
    def test_stage_uses_independent_nonhistorical_paths(self) -> None:
        self.assertIn("adr0015_requalification", str(run_stage.EVIDENCE))
        self.assertNotIn("repair_requalification", str(run_stage.EVIDENCE))
        self.assertIn("storage/logs", str(run_stage.WORK_ROOT))

    def test_stage_binds_exact_reviewed_and_integrated_implementation(self) -> None:
        self.assertEqual(run_stage.RUN_BINDINGS["reviewed_implementation_head"], run_stage.REVIEWED_IMPLEMENTATION_HEAD)
        self.assertEqual(run_stage.RUN_BINDINGS["controlled_integration_merge"], run_stage.CONTROLLED_INTEGRATION_MERGE)
        self.assertEqual(len(run_stage.EXACT_IMPLEMENTATION_FILES), 7)

    def test_three_way_includes_policy_supplement_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = {}
            diffs = {}
            for name in ("cold", "warm", "worker"):
                reports[name] = root / f"{name}.md"
                diffs[name] = root / f"{name}-diff.md"
                reports[name].write_text("same\n")
                diffs[name].write_text("same\n")
            builds = {name: artifacts() for name in reports}
            assert_three_way(builds, reports, diffs)
            builds["worker"][ADR0015_MANIFEST_TYPES[0]] = {"content_hash": "drift"}
            with self.assertRaisesRegex(ValueError, "artifact-set mismatch"):
                assert_three_way(builds, reports, diffs)

    def test_preflight_uses_local_git_only(self) -> None:
        run_stage.preflight_exact_implementation()


if __name__ == "__main__":
    unittest.main()
