from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HistoryArchiveTests(unittest.TestCase):
    def test_archive_manifest_is_exact(self) -> None:
        result = subprocess.run(
            ["python3", "scripts/u04_u24_history_archive_check.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_archive_permissions_are_fail_closed(self) -> None:
        data = json.loads((ROOT / "config/u04_u24_history_archive_v1.json").read_text())
        self.assertFalse(data["historical_evidence_mutation_authorized"])
        self.assertFalse(data["tree_changed_by_reachability_merge"])
        self.assertEqual(len(data["anchored_exact_heads"]), 8)
        self.assertEqual(len(data["replay_stages"]), 21)


if __name__ == "__main__":
    unittest.main()
