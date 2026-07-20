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

    def test_replay_mounts_gitignored_frozen_source_store(self) -> None:
        replay = (ROOT / "scripts/u04_u24_history_archive_replay.sh").read_text()
        self.assertIn('ln -s "$ROOT/storage/raw" "$SCRATCH/worktree/storage/raw"', replay)
        self.assertIn('! -e "$SCRATCH/worktree/storage/raw"', replay)

    def test_archive_mode_requires_exact_manifest_branch(self) -> None:
        selector = (ROOT / "scripts/pr_ci_selective_validate.sh").read_text()
        self.assertIn('"$CURRENT_HEAD_BRANCH" == "$ARCHIVE_HEAD_BRANCH"', selector)
        self.assertIn("GITHUB_HEAD_REF", selector)


if __name__ == "__main__":
    unittest.main()
