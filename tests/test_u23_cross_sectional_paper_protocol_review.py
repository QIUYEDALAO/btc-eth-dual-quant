from __future__ import annotations
import copy,json,unittest
from scripts.u23_cross_sectional_paper_protocol_review_check import EXPECTED, REVIEW, validate

class U23ReviewTests(unittest.TestCase):
    def setUp(self): self.review=json.loads(REVIEW.read_text())
    def test_exact(self): self.assertEqual(self.review["review_content_hash"],EXPECTED); self.assertEqual(validate(self.review,True),[])
    def test_generated_time_excluded(self):
        x=copy.deepcopy(self.review); x["generated_utc"]="2030-01-01T00:00:00Z"; self.assertEqual(validate(x),[])
    def test_target_blob_or_dimension_tamper(self):
        x=copy.deepcopy(self.review); x["target"]["head_sha"]="0"*40; self.assertTrue(validate(x))
        x=copy.deepcopy(self.review); x["target"]["files"]["src/btc_eth_dual_quant/data/u23_range_expansion.py"]="0"*64; self.assertTrue(validate(x,True))
        x=copy.deepcopy(self.review); x["review_dimensions"]["pre_freeze_synthetic_feasibility_and_exact_core_binding"]="fail"; self.assertTrue(validate(x))
    def test_verdict_or_escalation(self):
        x=copy.deepcopy(self.review); x["high_findings"]=1; self.assertTrue(validate(x))
        for key in ("ohlc_range_return_scan","event_scan","formal_returns","oos","m2"):
            x=copy.deepcopy(self.review); x["authorization_after_review"][key]=True; self.assertTrue(validate(x))
if __name__=="__main__": unittest.main()
