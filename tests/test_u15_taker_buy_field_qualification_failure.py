from __future__ import annotations
import copy,json,unittest
from scripts.u15_taker_buy_field_qualification_failure_check import EVIDENCE,EXPECTED,validate
class U15FieldFailureTests(unittest.TestCase):
    def setUp(self):self.evidence=json.loads(EVIDENCE.read_text())
    def test_exact_failure(self):self.assertEqual(self.evidence["content_hash"],EXPECTED);self.assertEqual(validate(self.evidence),[])
    def test_generated_time_excluded(self):
        x=copy.deepcopy(self.evidence);x["generated_utc"]="2030";self.assertEqual(validate(x),[])
    def test_row_or_gate_tamper_fails(self):
        x=copy.deepcopy(self.evidence);x["failure"]["quote_asset_volume"]="1";self.assertTrue(validate(x))
        x=copy.deepcopy(self.evidence);x["failure"]["raw_line_sha256"]="0"*64;self.assertTrue(validate(x))
    def test_result_access_or_permission_tamper_fails(self):
        x=copy.deepcopy(self.evidence);x["execution_accounting"]["event_rows_generated"]=1;self.assertTrue(validate(x))
        x=copy.deepcopy(self.evidence);x["decision"]["paper_observation_authorized"]=True;self.assertTrue(validate(x))
if __name__=="__main__":unittest.main()
