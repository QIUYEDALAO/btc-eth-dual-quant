from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ADR = ROOT / "docs/decisions/ADR-0013-official-archive-row-conflict-policy.md"


class ADR0013DraftPolicyTests(unittest.TestCase):
    def test_policy_is_draft_and_grants_no_authorization(self):
        text = ADR.read_text(encoding="utf-8")
        self.assertIn("Status: Proposed draft; not adopted", text)
        for marker in (
            "V2 contract modified: no",
            "Policy adopted: no",
            "U-03E rerun authorized: no",
            "U-03F authorized: no",
            "U-04 authorized: no",
            "Strategy code: no",
            "Event scan: no",
            "Returns/backtesting: no",
            "OOS opened: no",
            "API/trading: no",
            "M2: no",
        ):
            self.assertIn(marker, text)

    def test_policy_is_general_and_fail_closed(self):
        text = ADR.read_text(encoding="utf-8")
        for marker in (
            "byte_identical_duplicate",
            "semantic_identical_duplicate",
            "conflicting_duplicate",
            "parser_created_duplicate",
            "both REST comparators",
            "qualification remains blocked",
            "new contract and manifest schema version",
            "rebuilt from scratch",
        ):
            self.assertIn(marker, text)

    def test_forbidden_shortcuts_are_explicitly_rejected(self):
        text = ADR.read_text(encoding="utf-8")
        for marker in (
            "absolute-valued",
            "dropped silently",
            "asset/date special case",
            "replacement member",
            "manual symbol exclusion",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
