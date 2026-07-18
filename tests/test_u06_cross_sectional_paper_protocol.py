from __future__ import annotations
import copy
import json
import unittest
from scripts.u06_cross_sectional_paper_protocol_check import EXPECTED_HASH, PROTOCOL_PATH, validate, validate_report


class U06CrossSectionalPaperProtocolTests(unittest.TestCase):
    def setUp(self): self.p = json.loads(PROTOCOL_PATH.read_text())
    def test_repository_protocol_is_exact_and_result_blind(self): self.assertEqual(self.p["content_hash"], EXPECTED_HASH); self.assertEqual(validate(self.p), []); self.assertEqual(validate_report(), [])
    def test_generated_time_is_excluded(self): changed=copy.deepcopy(self.p); changed["generated_utc"]="2030-01-01T00:00:00Z"; self.assertEqual(validate(changed), [])
    def test_parameter_or_gate_tamper_fails(self):
        for section,key,value in (("volume_share_event","share_ratio_minimum","1.5"),("volume_share_event","baseline_days",20),("episode_clustering","connected_window_hours",24),("paper_gates","combined_median_24h_relative_repricing_minimum","0")):
            changed=copy.deepcopy(self.p); changed[section][key]=value; self.assertTrue(validate(changed), key)
    def test_authority_or_permission_escalation_fails(self):
        changed=copy.deepcopy(self.p); changed["authority_bindings"]["source_freeze_hash"]="0"*64; self.assertTrue(validate(changed))
        for key in ("data_qualification","event_scan","formal_returns","backtesting","oos","api_trading","m2"):
            changed=copy.deepcopy(self.p); changed["authorizations"][key]=True; self.assertTrue(validate(changed), key)
    def test_membership_reference_and_oos_guards_fail_closed(self):
        changed=copy.deepcopy(self.p); changed["point_in_time_universe"]["replacement_member_allowed"]=True; self.assertTrue(validate(changed))
        changed=copy.deepcopy(self.p); changed["observation_contract"]["search_later_if_reference_missing"]=True; self.assertTrue(validate(changed))
        changed=copy.deepcopy(self.p); changed["projection"]["may_read_oos_events_prices_or_counts"]=True; self.assertTrue(validate(changed))

if __name__ == "__main__": unittest.main()
