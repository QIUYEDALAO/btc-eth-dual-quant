from __future__ import annotations
import copy,json,unittest
from scripts.u16_cross_sectional_paper_protocol_review_check import REVIEW,EXPECTED,validate
class U16ReviewTests(unittest.TestCase):
    def setUp(self):self.r=json.loads(REVIEW.read_text())
    def test_exact(self):self.assertEqual(self.r["review_content_hash"],EXPECTED);self.assertEqual(validate(self.r,True),[])
    def test_time_excluded(self):
        x=copy.deepcopy(self.r);x["generated_utc"]="2030";self.assertEqual(validate(x),[])
    def test_target_or_dimension_tamper(self):
        x=copy.deepcopy(self.r);x["target"]["head_sha"]="0"*40;self.assertTrue(validate(x))
        x=copy.deepcopy(self.r);x["review_dimensions"]["future_membership_used_only_for_episode_right_censor_not_event_selection"]="fail";self.assertTrue(validate(x))
    def test_escalation(self):
        x=copy.deepcopy(self.r);x["authorization_after_review"]["event_scan"]=True;self.assertTrue(validate(x))
if __name__=="__main__":unittest.main()
