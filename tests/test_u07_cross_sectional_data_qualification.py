from __future__ import annotations
import copy,json,unittest
from scripts.u04_cross_sectional_data_qualification import QualificationFailure,content_hash
from scripts.u05_cross_sectional_data_qualification import verify_four_hour_authority
from scripts.u07_cross_sectional_data_qualification import CONFIG
from scripts.u07_cross_sectional_data_qualification_check import RESULT,validate
class U07DataQualificationTests(unittest.TestCase):
 def setUp(self):self.c=json.loads(CONFIG.read_text())
 def test_contract_and_four_hour_authority_are_exact(self):self.assertEqual(content_hash(self.c),self.c["content_hash"]);counts=verify_four_hour_authority(self.c);self.assertEqual(counts["expected_4h_member_blocks"],213570);self.assertEqual(counts["constituent_1h_rows"],854280)
 def test_signal_contract_tamper_fails(self):
  for k,v in (("constituent_bars_per_signal",3),("signal_timeframe","1h"),("later_block_substitution_allowed",True)):
   c=copy.deepcopy(self.c);c["signal_grid_contract"][k]=v
   with self.assertRaises(QualificationFailure):verify_four_hour_authority(c)
 def test_generation_time_does_not_change_contract_hash(self):c=copy.deepcopy(self.c);c["generated_utc"]="2030";self.assertEqual(content_hash(c),self.c["content_hash"])
 def test_committed_result_is_exact_and_isolated(self):
  r=json.loads(RESULT.read_text());self.assertEqual(validate(self.c,r,"Status: `pass` 27,736/27,736 19/19 OOS OHLC values decoded: `0` one sealed-IS Paper observation No strategy, backtest"),[])
  changed=copy.deepcopy(r);changed["isolation"]["oos_ohlc_values_decoded"]=1;self.assertTrue(validate(self.c,changed,""))
if __name__=="__main__":unittest.main()
