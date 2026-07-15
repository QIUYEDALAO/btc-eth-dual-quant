from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.liquid_universe_v3_requalification import (
    assert_three_way_determinism,
    render_membership_diff_report,
    should_continue_after_cold,
)


def document(name: str, value: object) -> dict:
    return {"manifest_type": name, "content_hash": str(value), "content": value}


class V3RequalificationTests(unittest.TestCase):
    def test_blocked_cold_build_stops_before_warm_and_worker(self):
        self.assertFalse(should_continue_after_cold({"status": "blocked"}))
        self.assertTrue(should_continue_after_cold({"status": "pass"}))

    def test_cold_warm_worker_must_match_manifests_and_reports(self):
        artifacts = {"qualification_summary": document("qualification_summary", "same")}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = []
            extras = []
            for name in ("cold", "warm", "worker"):
                report = root / f"{name}.md"
                report.write_text("same\n", encoding="utf-8")
                extra = root / f"{name}.json"
                extra.write_text(json.dumps({"same": True}, sort_keys=True) + "\n", encoding="utf-8")
                reports.append(report)
                extras.append({"v1_v3_diff": extra})
            assert_three_way_determinism(
                {"cold": artifacts, "warm": artifacts, "worker": artifacts},
                {"cold": reports[0], "warm": reports[1], "worker": reports[2]},
                {"cold": extras[0], "warm": extras[1], "worker": extras[2]},
            )
            reports[2].write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "report mismatch"):
                assert_three_way_determinism(
                    {"cold": artifacts, "warm": artifacts, "worker": artifacts},
                    {"cold": reports[0], "warm": reports[1], "worker": reports[2]},
                    {"cold": extras[0], "warm": extras[1], "worker": extras[2]},
                )

    def test_diff_report_names_both_authorities_and_never_claims_strategy_output(self):
        report = render_membership_diff_report(
            {"months_compared": 1, "changed_months": 0, "membership_additions": 0,
             "membership_removals": 0, "rank_changes": 0, "details": []},
            left="V2",
            right="V3",
        )
        self.assertIn("V2/V3", report)
        self.assertIn("Strategy/events/signals/returns computed: no", report)
        self.assertIn("M2 authorized: no", report)


if __name__ == "__main__":
    unittest.main()
