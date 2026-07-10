from __future__ import annotations

import unittest

from btc_eth_dual_quant.data.source_owner_package import build_package, render_report


def diagnostic(month: str, timestamp: int) -> dict:
    return {
        "symbol": "BTCUSDT", "month": month, "timeframe": "1h", "open_time": timestamp,
        "differing_fields": ["volume"], "classification": "higher_timeframe_flow_revision_confirmed_by_rest",
        "rest_matches_official": True, "rest_matches_derived": False,
        "derived_sha256": "a" * 64, "official_sha256": "b" * 64, "rest_sha256": "c" * 64,
    }


class SourceOwnerPackageTests(unittest.TestCase):
    def evidence(self) -> dict:
        return {
            "diagnostics": [diagnostic("2020-12", 1), diagnostic("2021-01", 2)],
            "archive_refetch": [{"unchanged": True}, {"unchanged": True}],
            "contract_resolved": False, "api_key_used": False,
        }

    def test_existing_issue_rows_are_excluded_from_supplement(self) -> None:
        package = build_package(self.evidence(), generated_utc="2026-07-11T00:00:00Z")
        self.assertEqual(package["existing_issue_overlap_rows"], 1)
        self.assertEqual(package["supplemental_rows"], 1)
        self.assertEqual(package["rows"][0]["month"], "2021-01")

    def test_package_is_sanitized_and_not_submitted(self) -> None:
        package = build_package(self.evidence(), generated_utc="2026-07-11T00:00:00Z")
        self.assertFalse(package["external_submission_performed"])
        self.assertFalse(package["api_key_used"])
        self.assertFalse(package["raw_payload_included"])
        self.assertEqual(package["status"], "ready_not_submitted")

    def test_render_includes_routing_and_guardrails(self) -> None:
        text = render_report(build_package(self.evidence(), generated_utc="2026-07-11T00:00:00Z"))
        self.assertIn("issue #475", text)
        self.assertIn("External submission performed: no", text)
        self.assertIn("M1E contract resolved: no", text)
        self.assertIn("Posting requires an explicit user decision", text)

    def test_resolved_or_nonpublic_evidence_is_rejected(self) -> None:
        resolved = self.evidence() | {"contract_resolved": True}
        with self.assertRaises(ValueError):
            build_package(resolved)
        private = self.evidence() | {"api_key_used": True}
        with self.assertRaises(ValueError):
            build_package(private)


if __name__ == "__main__":
    unittest.main()
