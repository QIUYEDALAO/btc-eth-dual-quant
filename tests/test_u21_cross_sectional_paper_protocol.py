from __future__ import annotations

import copy
import json
import unittest

from scripts.u21_cross_sectional_paper_protocol_check import CONTENT_HASH, PROTOCOL, validate_protocol


class U21ProtocolTests(unittest.TestCase):
    def setUp(self): self.protocol = json.loads(PROTOCOL.read_text())

    def test_exact(self):
        self.assertEqual(self.protocol["content_hash"], CONTENT_HASH)
        self.assertEqual(validate_protocol(self.protocol), [])

    def test_generated_time_excluded(self):
        changed = copy.deepcopy(self.protocol); changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate_protocol(changed), [])

    def test_authority_history_or_estimator_tamper(self):
        changed = copy.deepcopy(self.protocol); changed["authority_bindings"]["u20_run_content_hash"] = "0" * 64
        self.assertTrue(validate_protocol(changed))
        changed = copy.deepcopy(self.protocol); changed["history_contract"]["history_hours"] = 335
        self.assertTrue(validate_protocol(changed))
        changed = copy.deepcopy(self.protocol); changed["systematic_cokurtosis_contract"]["minimum_cokurtosis_per_half"] = "1.40"
        self.assertTrue(validate_protocol(changed))

    def test_cluster_gate_or_permission_tamper(self):
        changed = copy.deepcopy(self.protocol); changed["episode_clustering"]["connected_window_hours"] = 12
        self.assertTrue(validate_protocol(changed))
        changed = copy.deepcopy(self.protocol); changed["paper_gates"]["complete_is_independent_episodes_minimum"] = 89
        self.assertTrue(validate_protocol(changed))
        for key in ("data_qualification_complexity_and_preflight", "return_common_adjustment_cokurtosis_scan", "event_scan", "formal_returns", "oos", "m2"):
            changed = copy.deepcopy(self.protocol); changed["authorizations"][key] = True
            self.assertTrue(validate_protocol(changed), key)


if __name__ == "__main__": unittest.main()
