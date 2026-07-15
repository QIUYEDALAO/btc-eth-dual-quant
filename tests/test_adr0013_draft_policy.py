from pathlib import Path
import unittest

from scripts.adr0013_conformance_check import verify_adr_text


ROOT = Path(__file__).resolve().parents[1]
ADR = ROOT / "docs/decisions/ADR-0013-official-archive-row-conflict-policy.md"


class ADR0013AdoptionTests(unittest.TestCase):
    def test_independent_review_mandatory_changes_are_complete(self):
        text = ADR.read_text(encoding="utf-8")
        self.assertEqual(verify_adr_text(text), [])
        for change_id in range(1, 11):
            self.assertIn(f"## A{change_id}:", text)

    def test_authorization_is_narrow(self):
        text = ADR.read_text(encoding="utf-8")
        self.assertIn("Status: Accepted for V3 implementation and U-03E requalification only", text)
        self.assertIn("V3 contract implementation: true", text)
        self.assertIn("Conflict resolution registry implementation: true", text)
        self.assertIn("U-03E V3 rerun: true", text)
        for marker in (
            "U-03F: false",
            "U-04: false",
            "Hypothesis preregistration: false",
            "Strategy code: false",
            "Event scan: false",
            "Returns/backtesting: false",
            "OOS: false",
            "API/trading: false",
            "M2: false",
        ):
            self.assertIn(marker, text)

    def test_live_rest_and_unknown_conflicts_fail_closed(self):
        text = ADR.read_text(encoding="utf-8")
        self.assertIn("Qualification must never query live REST", text)
        self.assertIn("blocked_pending_adjudication", text)
        self.assertIn("An absent entry or any changed source/evidence hash", text)

    def test_duplicate_group_cannot_hide_third_conflict(self):
        text = ADR.read_text(encoding="utf-8")
        self.assertIn("Two identical rows plus one different row block the entire key", text)
        self.assertIn("Semantic-identical and conflicting duplicates remain blocked", text)
        self.assertIn("raw storage retains every row", text)

    def test_forbidden_shortcuts_and_membership_changes_are_rejected(self):
        text = ADR.read_text(encoding="utf-8")
        for marker in (
            "absolute-valued",
            "Generic `drop_duplicates`",
            "keep-first",
            "symbol/date logic",
            "replacement member",
            "monthly Top 15",
            "prior 90 complete UTC days",
            "365 complete history days",
        ):
            self.assertIn(marker, text)

    def test_tampered_mandatory_section_fails(self):
        text = ADR.read_text(encoding="utf-8").replace("## A9: Contract Hash Bindings", "## Removed")
        self.assertIn("missing mandatory section: A9", verify_adr_text(text))


if __name__ == "__main__":
    unittest.main()
