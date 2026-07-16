from __future__ import annotations

import unittest

from scripts import u03f_v4_repair_requalification_result_check as result


class RepairRequalificationResultTests(unittest.TestCase):
    def test_repository_result_is_exact_and_fail_closed(self) -> None:
        self.assertEqual(result.validate(), [])

    def test_result_identity_and_stop_are_frozen(self) -> None:
        self.assertEqual(result.BLOCKER_COUNT, 119)
        self.assertEqual(
            result.RUN_CONTENT_HASH,
            "0792ec7b52dbabb6057f0c238d963ed774c1e9e838b42cb21a03bc7e334f68cf",
        )
        self.assertEqual(
            result.COLD_ARTIFACT_SET_HASH,
            "b7cac049c6ab339f52fc29c7f31d275db09b3a4c47e2f62b38175cea219b2f83",
        )

    def test_history_and_all_six_contexts_are_bound(self) -> None:
        self.assertEqual(len(result.IMMUTABLE_HISTORICAL_EVIDENCE), 4)
        self.assertEqual(len(result.CONTEXT_MARKERS), 6)


if __name__ == "__main__":
    unittest.main()
