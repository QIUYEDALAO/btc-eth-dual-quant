from __future__ import annotations
import copy,unittest
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u16_cross_sectional_paper_observation_check import RUN,validate
class U16ObservationTests(unittest.TestCase):
    def setUp(self):self.r=load_json(RUN)
    def test_exact(self):self.assertEqual(validate(self.r),[])
    def test_result_or_order_tamper(self):
        x=copy.deepcopy(self.r);x["metrics"]["complete_is_independent_episodes"]=170;self.assertTrue(validate(x))
        x=copy.deepcopy(self.r);x["orders"][1]["content_identity_hash"]="0"*64;self.assertTrue(validate(x))
    def test_failed_gate_or_permission_tamper(self):
        x=copy.deepcopy(self.r);x["paper_gate_checks"]["median_24h_relative_information_persistence"]=True;self.assertTrue(validate(x))
        x=copy.deepcopy(self.r);x["authorizations"]["strategy"]=True;self.assertTrue(validate(x))
    def test_oos_or_second_run_tamper(self):
        x=copy.deepcopy(self.r);x["oos_opened"]=True;self.assertTrue(validate(x))
        x=copy.deepcopy(self.r);x["second_run_executed"]=True;self.assertTrue(validate(x))
if __name__=="__main__":unittest.main()
