from __future__ import annotations

import copy
import unittest

from scripts.u12_cross_sectional_paper_protocol_check import EXPECTED, load, validate


class U12PaperProtocolTests(unittest.TestCase):
    def setUp(self):
        self.document = load()

    def test_exact_protocol(self):
        self.assertEqual(self.document["content_hash"], EXPECTED)
        self.assertEqual(validate(self.document), [])

    def test_generated_time_excluded(self):
        changed = copy.deepcopy(self.document)
        changed["generated_utc"] = "2030"
        self.assertEqual(validate(changed), [])

    def test_calendar_estimator_or_preflight_tamper_fails(self):
        changed = copy.deepcopy(self.document)
        changed["calendar_state_contract"]["alternative_calendar_family_or_granularity"] = True
        self.assertTrue(validate(changed))
        changed = copy.deepcopy(self.document)
        changed["estimator_contract"]["prior_same_weekday_opportunities"] = 26
        self.assertTrue(validate(changed))
        changed = copy.deepcopy(self.document)
        changed["implementation_data_scope_preflight"]["verifies_previous_boundary_close_for_every_requested_daily_interval_including_month_transitions"] = False
        self.assertTrue(validate(changed))

    def test_gate_or_reference_tamper_fails(self):
        changed = copy.deepcopy(self.document)
        changed["paper_gates"]["complete_is_independent_episodes_minimum"] = 1
        self.assertTrue(validate(changed))
        changed = copy.deepcopy(self.document)
        changed["observation_contract"]["search_later_if_reference_missing"] = True
        self.assertTrue(validate(changed))

    def test_permission_escalation_fails(self):
        for key in ("data_qualification_and_preflight", "common_component_scan", "event_scan", "formal_returns", "fixed_rule_contract", "backtesting", "oos", "api_trading", "execution_live", "m2"):
            changed = copy.deepcopy(self.document)
            changed["authorizations"][key] = True
            self.assertTrue(validate(changed), key)


if __name__ == "__main__":
    unittest.main()
