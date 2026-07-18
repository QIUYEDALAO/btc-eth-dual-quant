from __future__ import annotations
import copy,json,unittest
from scripts.u14_cross_sectional_paper_protocol_check import EXPECTED_HASH,PROTOCOL,REPORT,validate
class U14PaperProtocolTests(unittest.TestCase):
    def setUp(self):self.d=json.loads(PROTOCOL.read_text());self.report=REPORT.read_text()
    def test_exact_protocol(self):self.assertEqual(self.d["content_hash"],EXPECTED_HASH);self.assertEqual(validate(self.d,self.report),[])
    def test_generated_time_excluded(self):
        x=copy.deepcopy(self.d);x["generated_utc"]="2030";self.assertEqual(validate(x,self.report),[])
    def test_auction_event_or_benchmark_tamper_fails(self):
        for section,key in (("completed_auction_contract","close_location"),("event_identity","candidate_close_location_minimum"),("pre_result_complexity_benchmark","maximum_elapsed_seconds")):
            x=copy.deepcopy(self.d);x[section][key]=0;self.assertTrue(validate(x,self.report),key)
    def test_gate_or_permission_escalation_fails(self):
        x=copy.deepcopy(self.d);x["paper_gates"]["complete_is_independent_episodes_minimum"]=89;self.assertTrue(validate(x,self.report))
        for key in ("data_qualification_complexity_and_preflight","event_scan","formal_returns","backtesting","oos","api_trading","execution_live","m2"):
            x=copy.deepcopy(self.d);x["authorizations"][key]=True;self.assertTrue(validate(x,self.report),key)
if __name__=="__main__":unittest.main()
