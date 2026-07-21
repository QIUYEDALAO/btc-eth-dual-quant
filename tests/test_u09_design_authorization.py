from __future__ import annotations
import copy,json,unittest
from scripts.u09_design_authorization_check import AUDIT,DECISION,EXPECTED_HASH,RESULTS,validate
class U09DesignAuthorizationTests(unittest.TestCase):
 def setUp(self):
  load=lambda p:json.loads(p.read_text());self.d=load(DECISION);self.r=[load(p) for p in RESULTS];self.a=load(AUDIT)
 def test_exact_narrow_decision(self):self.assertEqual(self.d["content_hash"],EXPECTED_HASH);self.assertEqual(validate(self.d,self.r,self.a),[])
 def test_all_prior_results_and_oos_seals_are_bound(self):
  for i in range(5):
   changed=copy.deepcopy(self.r);changed[i]["oos_opened"]=True;self.assertTrue(validate(self.d,changed,self.a))
   changed=copy.deepcopy(self.r);changed[i]["run_content_hash"]="0"*64;self.assertTrue(validate(self.d,changed,self.a))
 def test_only_design_is_authorized(self):self.assertEqual([k for k,v in self.d["authorizations"].items() if v],["u09_hypothesis_design"])
 def test_escalation_fails(self):
  for key in ("event_scan","returns","strategy_rule_selection","backtesting","oos","api_trading","execution_live","m2"):
   changed=copy.deepcopy(self.d);changed["authorizations"][key]=True;self.assertTrue(validate(changed,self.r,self.a),key)
 def test_authorities_fail_on_tamper(self):
  changed=copy.deepcopy(self.d);changed["bindings"]["source_freeze_hash"]="0"*64;self.assertTrue(validate(changed,self.r,self.a))
  changed=copy.deepcopy(self.a);changed["manifests_exact"]=18;self.assertTrue(validate(self.d,self.r,changed))
 def test_time_excluded_from_identity(self):
  changed=copy.deepcopy(self.d);changed["generated_utc"]="2030-01-01T00:00:00Z";self.assertEqual(validate(changed,self.r,self.a),[])
if __name__=="__main__":unittest.main()
