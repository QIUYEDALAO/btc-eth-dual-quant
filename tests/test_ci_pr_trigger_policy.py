from __future__ import annotations

import unittest

from scripts.ci_pr_trigger_policy_check import MAIN_WORKFLOW, PR_WORKFLOW, ROOT, validate


class CITriggerPolicyTests(unittest.TestCase):
    def test_repository_ci_trigger_policy_passes(self) -> None:
        self.assertEqual(validate(), [])

    def test_only_selective_workflow_handles_pull_requests(self) -> None:
        pull_request_files = []
        for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            if "pull_request:" in text or "pull_request," in text or ", pull_request" in text:
                pull_request_files.append(path)
        self.assertEqual(pull_request_files, [PR_WORKFLOW])

    def test_selective_workflow_cancels_obsolete_heads(self) -> None:
        text = PR_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("cancel-in-progress: true", text)
        self.assertIn("bash scripts/pr_ci_selective_validate.sh", text)

    def test_only_consolidated_regression_handles_main_push(self) -> None:
        push_files = []
        for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
            if "push:" in path.read_text(encoding="utf-8"):
                push_files.append(path)
        self.assertEqual(push_files, [MAIN_WORKFLOW])
        self.assertIn("branches: [main]", MAIN_WORKFLOW.read_text(encoding="utf-8"))

    def test_selector_cannot_recurse_or_expand_trigger_only_changes(self) -> None:
        text = (ROOT / "scripts/pr_ci_selective_validate.sh").read_text(encoding="utf-8")
        self.assertIn("workflow_body_changed", text)
        self.assertIn('"$validator" != scripts/pr_ci_selective_validate.sh', text)


if __name__ == "__main__":
    unittest.main()
