from __future__ import annotations
import copy,unittest
from btc_eth_dual_quant.data.u21_systematic_cokurtosis import evaluate_decision,evaluate_stream,half_cokurtosis
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u21_cross_sectional_data_qualification import COMMON_HALF,CONFIG,HIGH_HISTORY,NEUTRAL_HISTORY,synthetic_rows
from scripts.u21_cross_sectional_data_qualification_check import RESULT,validate
class U21QualificationTests(unittest.TestCase):
    def setUp(self):self.config=load_json(CONFIG);self.result=load_json(RESULT)
    def test_exact(self):self.assertEqual(validate(self.config,self.result),[])
    def test_generated_time_excluded(self):
        x=copy.deepcopy(self.config);x["generated_utc"]="2030-01-01T00:00:00Z";self.assertEqual(validate(x,self.result),[])
    def test_retry_result_or_permission_tamper(self):
        x=copy.deepcopy(self.result);x["failure"]["retry_executed"]=True;self.assertTrue(validate(self.config,x))
        x=copy.deepcopy(self.result);x["isolation"]["return_rows_generated"]=1;self.assertTrue(validate(self.config,x))
        x=copy.deepcopy(self.result);x["authorizations"]["one_sealed_is_paper_observation"]=True;self.assertTrue(validate(self.config,x))
    def test_cokurtosis_fixture_and_ordering(self):
        self.assertGreaterEqual(half_cokurtosis(HIGH_HISTORY[:168],COMMON_HALF),1.5);self.assertAlmostEqual(half_cokurtosis(NEUTRAL_HISTORY[:168],COMMON_HALF),1.0)
        event=evaluate_decision(list(synthetic_rows(15)));self.assertEqual(event["symbol"],"S00USDT")
        self.assertEqual(evaluate_stream(synthetic_rows(1500)),evaluate_stream(synthetic_rows(1500)))
if __name__=="__main__":unittest.main()
