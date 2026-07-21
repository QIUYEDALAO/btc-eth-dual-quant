from __future__ import annotations
import copy,json,unittest
from scripts.u14_design_authorization_check import AUDIT,DECISION,EXPECTED_HASH,U13_DECISION,U13_RESULT,validate
class U14DesignAuthorizationTests(unittest.TestCase):
    def setUp(self):
        load=lambda p:json.loads(p.read_text());self.decision=load(DECISION);self.u13=load(U13_RESULT);self.prior=load(U13_DECISION);self.audit=load(AUDIT)
    def check(self,decision=None,u13=None):return validate(decision or self.decision,u13 or self.u13,self.prior,self.audit)
    def test_exact_narrow_decision(self):self.assertEqual(self.decision["content_hash"],EXPECTED_HASH);self.assertEqual(self.check(),[])
    def test_prior_result_or_isolation_tamper_fails(self):
        changed=copy.deepcopy(self.u13);changed["second_run_executed"]=True;self.assertTrue(self.check(u13=changed))
        changed=copy.deepcopy(self.decision);changed["bindings"]["u13_run_content_hash"]="0"*64;self.assertTrue(self.check(changed))
    def test_only_design_is_authorized(self):self.assertEqual([k for k,v in self.decision["authorizations"].items() if v],["u14_hypothesis_design"])
    def test_escalation_fails(self):
        for key in ("public_data_read","event_scan","returns","strategy_rule_selection","backtesting","oos","api_trading","execution_live","m2"):
            changed=copy.deepcopy(self.decision);changed["authorizations"][key]=True;self.assertTrue(self.check(changed),key)
    def test_generated_time_excluded(self):
        changed=copy.deepcopy(self.decision);changed["generated_utc"]="2030";self.assertEqual(self.check(changed),[])
if __name__=="__main__":unittest.main()
