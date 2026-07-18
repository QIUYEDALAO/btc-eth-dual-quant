from __future__ import annotations
import copy,unittest
from scripts.u09_cross_sectional_paper_protocol_check import EXPECTED,load,validate
class U09ProtocolTests(unittest.TestCase):
 def setUp(self):self.d=load()
 def test_exact_protocol(self):self.assertEqual(self.d["content_hash"],EXPECTED);self.assertEqual(validate(self.d),[])
 def test_generated_time_excluded(self):d=copy.deepcopy(self.d);d["generated_utc"]="2030";self.assertEqual(validate(d),[])
 def test_schedule_and_event_tamper_fails(self):
  d=copy.deepcopy(self.d);d["decision_schedule"]["anchor_interval_hours"]=168;self.assertTrue(validate(d))
  d=copy.deepcopy(self.d);d["quality_event"]["replacement_member_allowed"]=True;self.assertTrue(validate(d))
 def test_causal_and_gate_tamper_fails(self):
  d=copy.deepcopy(self.d);d["observation_contract"]["search_later_if_reference_missing"]=True;self.assertTrue(validate(d))
  d=copy.deepcopy(self.d);d["paper_gates"]["complete_is_independent_episodes_minimum"]=1;self.assertTrue(validate(d))
 def test_permission_escalation_fails(self):
  for k in ("event_scan","formal_returns","fixed_rule_contract","backtesting","oos","api_trading","execution_live","m2"):
   d=copy.deepcopy(self.d);d["authorizations"][k]=True;self.assertTrue(validate(d),k)
if __name__=="__main__":unittest.main()
