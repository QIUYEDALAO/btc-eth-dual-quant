from __future__ import annotations
import copy,unittest
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u10_cross_sectional_data_qualification import CONFIG,canonical_hash,verify_ceiling
from scripts.u10_cross_sectional_data_qualification_check import E,REPORT,validate
class U10QualificationTests(unittest.TestCase):
 def test_contract_and_ceiling(self):
  d=load_json(CONFIG);self.assertEqual(canonical_hash(d),d["content_hash"]);self.assertEqual(verify_ceiling(d)["maximum_independent_constant_membership_episodes"],418);self.assertFalse(d["authorizations"]["event_scan"])
 def test_result_tamper_fails(self):
  d=load_json(E);t=REPORT.read_text();self.assertEqual(validate(d,t),[]);x=copy.deepcopy(d);x["counts"]["maximum_independent_constant_membership_episodes"]=89;self.assertTrue(validate(x,t));x=copy.deepcopy(d);x["authorizations"]["strategy"]=True;self.assertTrue(validate(x,t))
 def test_time_excluded(self):d=load_json(CONFIG);x=copy.deepcopy(d);x["generated_utc"]="2030";self.assertEqual(canonical_hash(x),d["content_hash"])
if __name__=="__main__":unittest.main()
