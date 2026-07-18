from __future__ import annotations
import copy,unittest
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u22_cross_sectional_data_qualification import CONFIG
from scripts.u22_cross_sectional_data_qualification_check import RESULT,validate
class U22QualificationTests(unittest.TestCase):
 def setUp(self):self.config=load_json(CONFIG);self.result=load_json(RESULT)
 def test_exact(self):self.assertEqual(validate(self.config,self.result),[])
 def test_generated_time_excluded(self):
  x=copy.deepcopy(self.config);x["generated_utc"]="2030-01-01T00:00:00Z";self.assertEqual(validate(x,self.result),[])
 def test_ceiling_isolation_or_permission_tamper(self):
  x=copy.deepcopy(self.result);x["counts"]["maximum_independent_theoretical_24h_episodes"]=399;self.assertTrue(validate(self.config,x))
  x=copy.deepcopy(self.result);x["isolation"]["dispersion_rows_generated"]=1;self.assertTrue(validate(self.config,x))
  x=copy.deepcopy(self.result);x["authorizations"]["strategy"]=True;self.assertTrue(validate(self.config,x))
if __name__=="__main__":unittest.main()
