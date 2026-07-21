from __future__ import annotations
import copy,unittest
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u22_cross_sectional_paper_observation_check import RUN,validate
class U22ObservationTests(unittest.TestCase):
 def setUp(self):self.run=load_json(RUN)
 def test_exact(self):self.assertEqual(validate(self.run),[])
 def test_result_or_second_run_tamper(self):
  x=copy.deepcopy(self.run);x["metrics"]["complete_is_independent_episodes"]=199;self.assertTrue(validate(x))
  x=copy.deepcopy(self.run);x["second_run_executed"]=True;self.assertTrue(validate(x))
 def test_oos_or_authorization_tamper(self):
  x=copy.deepcopy(self.run);x["oos_opened"]=True;self.assertTrue(validate(x))
  x=copy.deepcopy(self.run);x["authorizations"]["strategy"]=True;self.assertTrue(validate(x))
if __name__=="__main__":unittest.main()
