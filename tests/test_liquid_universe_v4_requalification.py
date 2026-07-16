from __future__ import annotations

import inspect
import tempfile
from pathlib import Path
import unittest

from btc_eth_dual_quant.data.lifecycle_artifacts import V4_MANIFEST_TYPES
from scripts import liquid_universe_v4_requalification as requalification
from scripts.liquid_universe_v4_requalification import assert_three_way


def artifacts(value: str = "same") -> dict:
    return {name: {"content_hash": f"{value}:{name}"} for name in V4_MANIFEST_TYPES}


class LiquidUniverseV4RequalificationTests(unittest.TestCase):
    def test_authoritative_wrapper_is_frozen_source_only(self):
        source = inspect.getsource(requalification.execute)
        self.assertIn("offline=True", source)
        self.assertIn("verify_remote_registry=False", source)
        self.assertNotIn("offline=False", source)

    def test_repaired_evidence_paths_do_not_overwrite_historical_v4(self):
        self.assertIn("liquid_universe_v4_repair_requalification", str(requalification.REPAIRED_EVIDENCE))
        self.assertNotEqual(
            requalification.REPAIRED_EVIDENCE,
            requalification.ROOT / "reports/m0/evidence/liquid_universe_v4",
        )
        self.assertIn("REPAIR_REQUALIFICATION", requalification.REPAIRED_REPORT.name)

    def test_three_way_exact_match_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports, diffs = {}, {}
            for name in ("cold", "warm", "worker"):
                reports[name] = root / f"{name}.md"
                diffs[name] = root / f"{name}-diff.md"
                reports[name].write_text("report\n")
                diffs[name].write_text("diff\n")
            same = artifacts()
            assert_three_way({name: same for name in reports}, reports, diffs)

    def test_three_way_hash_drift_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports, diffs = {}, {}
            for name in ("cold", "warm", "worker"):
                reports[name] = root / f"{name}.md"
                diffs[name] = root / f"{name}-diff.md"
                reports[name].write_text("report\n")
                diffs[name].write_text("diff\n")
            builds = {"cold": artifacts(), "warm": artifacts(), "worker": artifacts()}
            first = sorted(V4_MANIFEST_TYPES)[0]
            builds["worker"] = {**builds["worker"], first: {"content_hash": "changed"}}
            with self.assertRaisesRegex(ValueError, "artifact-set mismatch"):
                assert_three_way(builds, reports, diffs)

    def test_missing_worker_build_blocks(self):
        with self.assertRaisesRegex(ValueError, "cold/warm/worker"):
            assert_three_way({"cold": artifacts(), "warm": artifacts()}, {}, {})


if __name__ == "__main__":
    unittest.main()
