from __future__ import annotations
import copy,unittest
from scripts.u10_cross_sectional_paper_protocol_check import EXPECTED,load,validate
class U10ProtocolTests(unittest.TestCase):
 def setUp(self):self.d=load()
 def test_exact_protocol(self):self.assertEqual(self.d["content_hash"],EXPECTED);self.assertEqual(validate(self.d),[])
 def test_generated_time_excluded(self):d=copy.deepcopy(self.d);d["generated_utc"]="2030";self.assertEqual(validate(d),[])
 def test_event_or_ceiling_tamper_fails(self):
  d=copy.deepcopy(self.d);d["event_identity"]["relative_trend_days"]=3;self.assertTrue(validate(d))
  d=copy.deepcopy(self.d);d["pre_result_sample_ceiling"]["minimum_theoretical_constant_membership_72h_episodes"]=80;self.assertTrue(validate(d))
 def test_gate_or_reference_tamper_fails(self):
  d=copy.deepcopy(self.d);d["paper_gates"]["complete_is_independent_episodes_minimum"]=1;self.assertTrue(validate(d))
  d=copy.deepcopy(self.d);d["observation_contract"]["search_later_if_reference_missing"]=True;self.assertTrue(validate(d))
 def test_permission_escalation_fails(self):
  for k in ("event_scan","formal_returns","fixed_rule_contract","backtesting","oos","api_trading","execution_live","m2"):
   d=copy.deepcopy(self.d);d["authorizations"][k]=True;self.assertTrue(validate(d),k)
if __name__=="__main__":unittest.main()
