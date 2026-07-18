from __future__ import annotations
import copy,unittest
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u16_cross_sectional_data_qualification import CONFIG,synthetic_rows
from scripts.u16_cross_sectional_data_qualification_check import RESULT,validate
from btc_eth_dual_quant.data.u16_correlation_breakdown import evaluate_stream
class U16QualificationTests(unittest.TestCase):
    def setUp(self):self.c=load_json(CONFIG);self.r=load_json(RESULT)
    def test_exact(self):self.assertEqual(validate(self.c,self.r),[])
    def test_time_excluded(self):
        x=copy.deepcopy(self.c);x["generated_utc"]="2030";self.assertEqual(validate(x,self.r),[])
    def test_ceiling_or_permission_tamper(self):
        x=copy.deepcopy(self.r);x["counts"]["maximum_independent_theoretical_24h_episodes"]=399;self.assertTrue(validate(self.c,x))
        x=copy.deepcopy(self.r);x["authorizations"]["strategy"]=True;self.assertTrue(validate(self.c,x))
    def test_isolation_or_complexity_tamper(self):
        x=copy.deepcopy(self.r);x["isolation"]["correlation_rows_generated"]=1;self.assertTrue(validate(self.c,x))
        x=copy.deepcopy(self.r);x["complexity_benchmark"]["passes"][0]["elapsed_seconds"]="30.1";self.assertTrue(validate(self.c,x))
    def test_synthetic_core_deterministic(self):self.assertEqual(evaluate_stream(synthetic_rows(1500)),evaluate_stream(synthetic_rows(1500)))
if __name__=="__main__":unittest.main()
