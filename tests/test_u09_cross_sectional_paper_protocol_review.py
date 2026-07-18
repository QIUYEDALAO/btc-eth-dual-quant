from __future__ import annotations
import copy,json,unittest
from scripts.u09_cross_sectional_paper_protocol_review_check import E,REPORT,validate
class U09ProtocolReviewTests(unittest.TestCase):
 def setUp(self):self.d=json.loads(E.read_text());self.t=REPORT.read_text()
 def test_exact_review(self):self.assertEqual(validate(self.d,self.t),[])
 def test_time_excluded(self):d=copy.deepcopy(self.d);d["generated_utc"]="2030";self.assertEqual(validate(d,self.t),[])
 def test_target_or_verdict_tamper_fails(self):
  for k,v in (("target_commit","0"*40),("remaining_high_findings",1),("target_modified",True)):
   d=copy.deepcopy(self.d);d[k]=v;self.assertTrue(validate(d,self.t),k)
 def test_permission_escalation_fails(self):
  d=copy.deepcopy(self.d);d["authorizations"]["event_scan"]=True;self.assertTrue(validate(d,self.t))
if __name__=="__main__":unittest.main()
