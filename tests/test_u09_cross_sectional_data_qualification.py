from __future__ import annotations
import copy,unittest
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u09_cross_sectional_data_qualification import CONFIG,content_hash,verify_schedule
from scripts.u09_cross_sectional_data_qualification_check import E,REPORT,validate
class U09QualificationTests(unittest.TestCase):
 def test_contract_shape_hash_and_schedule(self):
  d=load_json(CONFIG);self.assertEqual(content_hash(d),d["content_hash"]);self.assertEqual(verify_schedule(d),{"is_anchors_before_boundary":123,"is_primary_complete_anchors":122});self.assertFalse(d["authorizations"]["event_scan"])
 def test_committed_result_exact_and_tamper_fails(self):
  d=load_json(E);text=REPORT.read_text();self.assertEqual(validate(d,text),[]);x=copy.deepcopy(d);x["counts"]["is_primary_complete_anchors"]-=1;self.assertTrue(validate(x,text));x=copy.deepcopy(d);x["authorizations"]["strategy"]=True;self.assertTrue(validate(x,text))
 def test_generation_time_excluded_from_contract_hash(self):
  d=load_json(CONFIG);x=copy.deepcopy(d);x["generated_utc"]="2030";self.assertEqual(content_hash(x),d["content_hash"])
if __name__=="__main__":unittest.main()
