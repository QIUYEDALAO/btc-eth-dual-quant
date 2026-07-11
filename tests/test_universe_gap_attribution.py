import unittest
from datetime import datetime, timedelta, timezone
from btc_eth_dual_quant.data.universe_gap_attribution import GapRecord, classify_missing_slots, gate

POLICY={"synchronous_outage_minimum_symbols":2,"synchronous_outage_minimum_fraction":0.8}
T=datetime(2024,1,1,tzinfo=timezone.utc)

class GapAttributionTests(unittest.TestCase):
    def test_unexplained_gap_cannot_pass(self):
        r=GapRecord('A','2024-01',T,1,5,'symbol_specific','unknown','blocked_unresolved')
        self.assertEqual(gate([r],[])[0],'blocked_unresolved')
    def test_global_outage_can_quarantine(self):
        records=classify_missing_slots(symbol='A',month='2024-01',missing={T},missing_by_slot={T:{'A','B','C','D'}},member_count=5,evidence_source='official ZIP peers',policy=POLICY)
        self.assertEqual(records[0].classification,'binance_global_event'); self.assertEqual(gate(records,[])[0],'pass_with_quarantine')
    def test_single_asset_gap_is_isolated_not_replaced(self):
        records=classify_missing_slots(symbol='A',month='2024-01',missing={T},missing_by_slot={T:{'A'}},member_count=5,evidence_source='official ZIP',policy=POLICY)
        self.assertEqual(records[0].qualification_decision,'quarantine_isolate_symbol_month_without_replacement')
    def test_processing_error_blocks(self): self.assertEqual(gate([],['parser'])[0],'blocked_processing_error')
    def test_consecutive_slots_group_deterministically(self):
        missing={T,T+timedelta(minutes=5)}; slot={x:{'A'} for x in missing}
        self.assertEqual(classify_missing_slots(symbol='A',month='2024-01',missing=missing,missing_by_slot=slot,member_count=5,evidence_source='zip',policy=POLICY)[0].missing_count,2)
if __name__=='__main__': unittest.main()
