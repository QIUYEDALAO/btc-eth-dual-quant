from __future__ import annotations
import copy,json,unittest
from scripts.u09_qualification_sample_ceiling_check import E,REPORT,recompute,validate
class U09SampleCeilingTests(unittest.TestCase):
 def setUp(self):self.d=json.loads(E.read_text());self.t=REPORT.read_text()
 def test_exact_failed_preflight(self):self.assertEqual(recompute(self.d)[0],66);self.assertEqual(validate(self.d,self.t),[])
 def test_gate_or_calendar_tamper_fails(self):
  d=copy.deepcopy(self.d);d["counts"]["frozen_minimum_complete_is_episodes"]=66;self.assertTrue(validate(d,self.t))
  d=copy.deepcopy(self.d);d["calendar_inputs"]["anchor_interval_hours"]=168;self.assertTrue(validate(d,self.t))
 def test_permission_escalation_fails(self):
  d=copy.deepcopy(self.d);d["decision"]["paper_observation_authorized"]=True;self.assertTrue(validate(d,self.t))
 def test_time_excluded(self):d=copy.deepcopy(self.d);d["generated_utc"]="2030";self.assertEqual(validate(d,self.t),[])
if __name__=="__main__":unittest.main()
