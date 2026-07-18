from __future__ import annotations

import copy
import json
import unittest

from scripts.u18_cross_sectional_paper_protocol_check import CONTENT_HASH, PROTOCOL, validate_protocol


class U18ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads(PROTOCOL.read_text())

    def test_exact(self):
        self.assertEqual(self.protocol["content_hash"], CONTENT_HASH)
        self.assertEqual(validate_protocol(self.protocol), [])

    def test_generated_time_excluded(self):
        protocol = copy.deepcopy(self.protocol)
        protocol["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate_protocol(protocol), [])

    def test_history_or_tail_tamper(self):
        protocol = copy.deepcopy(self.protocol)
        protocol["history_contract"]["history_hours"] = 167
        self.assertTrue(validate_protocol(protocol))
        protocol = copy.deepcopy(self.protocol)
        protocol["downside_tail_contract"]["minimum_downside_tail_energy_share_per_half"] = "0.20"
        self.assertTrue(validate_protocol(protocol))

    def test_cluster_gate_or_permission_tamper(self):
        protocol = copy.deepcopy(self.protocol)
        protocol["episode_clustering"]["connected_window_hours"] = 12
        self.assertTrue(validate_protocol(protocol))
        protocol = copy.deepcopy(self.protocol)
        protocol["paper_gates"]["complete_is_independent_episodes_minimum"] = 89
        self.assertTrue(validate_protocol(protocol))
        for key in ("data_qualification_complexity_and_preflight", "event_scan", "formal_returns", "oos", "m2"):
            protocol = copy.deepcopy(self.protocol)
            protocol["authorizations"][key] = True
            self.assertTrue(validate_protocol(protocol), key)


if __name__ == "__main__":
    unittest.main()
