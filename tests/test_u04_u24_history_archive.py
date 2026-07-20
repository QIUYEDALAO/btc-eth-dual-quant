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
        self.assertEqual(data["archive_head_branch"], "codex/u04-u24-history-archive")
        snapshots = data["replay_source_snapshots"]
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0]["sha256"], "2b6db817003d1ba07bf4382220bc5455045d7ca713b57a4a95b6401ddc56ab9c")

    def test_replay_mounts_independent_read_only_snapshot(self) -> None:
        replay = (ROOT / "scripts/u04_u24_history_archive_replay.sh").read_text()
        self.assertNotIn('ln -s "$ROOT/storage/raw"', replay)
        self.assertIn('ln -s "$SNAPSHOT_ROOT/storage/raw"', replay)
        self.assertIn('chmod a-w', replay)
        self.assertIn('git -C "$SCRATCH/worktree" status --porcelain', replay)
        self.assertIn('verify_snapshot_set "$ROOT"', replay)

    def test_snapshot_write_is_blocked_or_hash_gate_detects_it(self) -> None:
        result = subprocess.run(
            ["bash", "scripts/u04_u24_history_archive_replay.sh"],
            cwd=ROOT,
            env={**__import__("os").environ, "ARCHIVE_REPLAY_SNAPSHOT_PROBE_ONLY": "1"},
            text=True,
            capture_output=True,
        )
        combined = result.stdout + result.stderr
        self.assertTrue(
            (result.returncode == 0 and "write blocked PASS" in combined)
            or (result.returncode != 0 and "hash changed" in combined),
            combined,
        )

    def test_archive_mode_requires_exact_manifest_branch(self) -> None:
        selector = (ROOT / "scripts/pr_ci_selective_validate.sh").read_text()
        self.assertIn('"$CURRENT_HEAD_BRANCH" == "$ARCHIVE_HEAD_BRANCH"', selector)
        self.assertIn("GITHUB_HEAD_REF", selector)


if __name__ == "__main__":
    unittest.main()
