from __future__ import annotations
import copy,json,unittest
from scripts.u14_cross_sectional_design_check import CONTENT_HASH,SCOPE,validate_scope
class U14DesignTests(unittest.TestCase):
    def setUp(self):self.scope=json.loads(SCOPE.read_text())
    def test_exact_design(self):self.assertEqual(self.scope["content_hash"],CONTENT_HASH);self.assertEqual(validate_scope(self.scope),[])
    def test_generated_time_excluded(self):
        x=copy.deepcopy(self.scope);x["generated_utc"]="2030";self.assertEqual(validate_scope(x),[])
    def test_permission_escalation_fails(self):
        x=copy.deepcopy(self.scope);x["authorizations"]["event_scan"]=True;self.assertTrue(validate_scope(x))
    def test_removing_invariant_or_failure_fails(self):
        x=copy.deepcopy(self.scope);x["causal_and_membership_invariants"]["completed_high_low_close_only"]=False;self.assertTrue(validate_scope(x))
        x=copy.deepcopy(self.scope);x["economic_hypothesis"]["failure_regimes"].pop();self.assertTrue(validate_scope(x))
    def test_resolving_parameter_prematurely_fails(self):
        x=copy.deepcopy(self.scope);x["unresolved_until_separate_protocol"].pop();self.assertTrue(validate_scope(x))
if __name__=="__main__":unittest.main()
