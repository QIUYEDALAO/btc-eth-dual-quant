from __future__ import annotations
import copy,json,unittest
from scripts.u10_design_authorization_check import AUDIT,CORRECTION,DECISION,EXPECTED_HASH,RESULTS,validate
class U10DesignAuthorizationTests(unittest.TestCase):
 def setUp(self):
  load=lambda p:json.loads(p.read_text());self.d=load(DECISION);self.c=load(CORRECTION);self.r=[load(p) for p in RESULTS];self.a=load(AUDIT)
 def test_exact_narrow_decision(self):self.assertEqual(self.d["content_hash"],EXPECTED_HASH);self.assertEqual(validate(self.d,self.c,self.r,self.a),[])
 def test_prior_evidence_tamper_fails(self):
  c=copy.deepcopy(self.c);c["content_hash"]="0"*64;self.assertTrue(validate(self.d,c,self.r,self.a))
  for i in range(5):
   r=copy.deepcopy(self.r);r[i]["oos_opened"]=True;self.assertTrue(validate(self.d,self.c,r,self.a))
 def test_only_design_is_authorized(self):self.assertEqual([k for k,v in self.d["authorizations"].items() if v],["u10_hypothesis_design"])
 def test_escalation_fails(self):
  for key in ("event_scan","returns","strategy_rule_selection","backtesting","oos","api_trading","execution_live","m2"):
   d=copy.deepcopy(self.d);d["authorizations"][key]=True;self.assertTrue(validate(d,self.c,self.r,self.a),key)
 def test_time_excluded(self):d=copy.deepcopy(self.d);d["generated_utc"]="2030";self.assertEqual(validate(d,self.c,self.r,self.a),[])
if __name__=="__main__":unittest.main()
