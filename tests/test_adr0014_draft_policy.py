from pathlib import Path
import unittest

from scripts.adr0014_draft_policy_check import verify_adr_text


ROOT = Path(__file__).resolve().parents[1]
ADR = ROOT / "docs/decisions/ADR-0014-official-lifecycle-boundary-placeholder-policy.md"


class ADR0014DraftPolicyTests(unittest.TestCase):
    def test_complete_draft_passes(self):
        self.assertEqual(verify_adr_text(ADR.read_text(encoding="utf-8")), [])

    def test_draft_is_not_adopted_or_implemented(self):
        text = ADR.read_text(encoding="utf-8")
        for marker in (
            "Status: Proposed draft; not adopted",
            "Policy adopted: false",
            "Policy implemented: false",
            "Contract modified: false",
            "Registry modified: false",
            "V3/V4 requalification run: false",
            "U-03F: false",
            "U-04: false",
            "Strategy code: false",
            "Event scan: false",
            "Returns/backtesting: false",
            "OOS: false",
            "API/trading: false",
            "M2: false",
        ):
            self.assertIn(marker, text)

    def test_missing_eligibility_condition_fails_closed(self):
        text = ADR.read_text(encoding="utf-8").replace(
            "close_time equals official cessation_time minus exactly 1 millisecond",
            "close_time boundary removed",
        )
        self.assertIn(
            "missing eligibility condition: close_time equals official cessation_time minus exactly 1 millisecond",
            verify_adr_text(text),
        )

    def test_adoption_or_downstream_authorization_fails(self):
        text = ADR.read_text(encoding="utf-8").replace(
            "Policy adopted: false", "Policy adopted: true"
        )
        self.assertIn("forbidden authorization: Policy adopted: true", verify_adr_text(text))

    def test_missing_shortcut_prohibition_fails(self):
        text = ADR.read_text(encoding="utf-8").replace(
            "Do not replace the archive row with REST data.",
            "REST shortcut removed.",
        )
        self.assertIn(
            "missing prohibited shortcut: Do not replace the archive row with REST data.",
            verify_adr_text(text),
        )

    def test_klay_evidence_hash_is_frozen(self):
        text = ADR.read_text(encoding="utf-8").replace(
            "6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a",
            "0" * 64,
        )
        self.assertIn("KLAY adjudication evidence hash missing or changed", verify_adr_text(text))


if __name__ == "__main__":
    unittest.main()
