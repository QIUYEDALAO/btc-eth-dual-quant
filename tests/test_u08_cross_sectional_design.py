from __future__ import annotations
import copy,unittest
from scripts.u08_cross_sectional_design_check import CONTENT_HASH,SCOPE,load,validate_scope
class U08DesignTests(unittest.TestCase):
 def setUp(self):self.d=load(SCOPE)
 def test_exact_design(self):self.assertEqual(self.d["content_hash"],CONTENT_HASH);self.assertEqual(validate_scope(self.d),[])
 def test_time_excluded(self):d=copy.deepcopy(self.d);d["generated_utc"]="2030";self.assertEqual(validate_scope(d),[])
 def test_permission_escalation_fails(self):
  for k in ("event_scan","returns","fixed_rule_contract","backtesting","oos","api_trading","execution_live","m2"):
   d=copy.deepcopy(self.d);d["authorizations"][k]=True;self.assertTrue(validate_scope(d),k)
 def test_removing_invariant_or_failure_fails(self):
  d=copy.deepcopy(self.d);d["causal_and_membership_invariants"].pop("prior_complete_ranking_inputs_only");self.assertTrue(validate_scope(d))
  d=copy.deepcopy(self.d);d["economic_hypothesis"]["failure_regimes"].pop();self.assertTrue(validate_scope(d))
if __name__=="__main__":unittest.main()
