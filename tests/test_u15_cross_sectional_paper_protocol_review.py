from __future__ import annotations
import copy,json,unittest
from scripts.u15_cross_sectional_paper_protocol_review_check import REVIEW,REVIEW_HASH,validate_review
class U15ProtocolReviewTests(unittest.TestCase):
    def setUp(self):self.review=json.loads(REVIEW.read_text())
    def test_exact_review_and_target(self):self.assertEqual(self.review["review_content_hash"],REVIEW_HASH);self.assertEqual(validate_review(self.review,True),[])
    def test_generated_time_excluded(self):
        x=copy.deepcopy(self.review);x["generated_utc"]="2030";self.assertEqual(validate_review(x),[])
    def test_target_or_verdict_tamper_fails(self):
        x=copy.deepcopy(self.review);x["target"]["head_sha"]="0"*40;self.assertTrue(validate_review(x))
        x=copy.deepcopy(self.review);x["high_findings"]=1;self.assertTrue(validate_review(x))
    def test_dimension_or_permission_tamper_fails(self):
        x=copy.deepcopy(self.review);x["review_dimensions"]["official_taker_buy_field_semantics"]="fail";self.assertTrue(validate_review(x))
        x=copy.deepcopy(self.review);x["authorization_after_review"]["event_scan"]=True;self.assertTrue(validate_review(x))
if __name__=="__main__":unittest.main()
