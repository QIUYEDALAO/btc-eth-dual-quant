from __future__ import annotations
import copy, unittest
from scripts.u07_cross_sectional_paper_protocol_review_check import REVIEW_PATH,load,validate,validate_report
class U07PaperProtocolReviewTests(unittest.TestCase):
 def setUp(self):self.r=load(REVIEW_PATH)
 def test_repository_review_approves_exact_target(self):self.assertEqual(validate(self.r),[]);self.assertEqual(validate_report(),[])
 def test_generated_time_excluded(self):c=copy.deepcopy(self.r);c["generated_utc"]="2030";self.assertEqual(validate(c,False),[])
 def test_target_file_or_dimension_tamper_fails(self):
  c=copy.deepcopy(self.r);c["target"]["head_commit"]="0"*40;self.assertTrue(validate(c,False))
  c=copy.deepcopy(self.r);c["review_dimensions"].pop();self.assertTrue(validate(c,False))
 def test_severity_mutation_or_permission_escalation_fails(self):
  c=copy.deepcopy(self.r);c["remaining_high_findings"]=1;self.assertTrue(validate(c,False))
  for k,v in self.r["authorizations"].items():
   if not v:c=copy.deepcopy(self.r);c["authorizations"][k]=True;self.assertTrue(validate(c,False),k)
 def test_target_mutation_claim_fails(self):c=copy.deepcopy(self.r);c["target_modified_by_review"]=True;self.assertTrue(validate(c,False))
if __name__=="__main__":unittest.main()
