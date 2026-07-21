from __future__ import annotations
import copy,json,tempfile,unittest
from pathlib import Path
from scripts.u04_cross_sectional_data_qualification import QualificationFailure
from scripts.u06_cross_sectional_data_qualification import CONFIG,canonical_hash,verify_daily_authority
class U06DataQualificationTests(unittest.TestCase):
 def setUp(self):self.c=json.loads(CONFIG.read_text())
 def test_contract_and_daily_authority_are_exact(self):self.assertEqual(canonical_hash(self.c),self.c["content_hash"]);counts=verify_daily_authority(self.c);self.assertEqual(counts["quote_volume_authority_rows"],1170);self.assertEqual(counts["bars_per_complete_day"],288)
 def test_daily_contract_tamper_fails(self):
  for k,v in (("bars_per_complete_utc_day",24),("quote_volume_column_index",6),("later_day_or_member_substitution_allowed",True)):
   c=copy.deepcopy(self.c);c["daily_signal_contract"][k]=v
   with self.assertRaises(QualificationFailure):verify_daily_authority(c)
 def test_generation_time_does_not_change_contract_hash(self):c=copy.deepcopy(self.c);c["generated_utc"]="2030";self.assertEqual(canonical_hash(c),self.c["content_hash"])
if __name__=="__main__":unittest.main()
