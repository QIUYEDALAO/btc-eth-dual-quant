from __future__ import annotations
import copy,json,unittest
from scripts.u15_cross_sectional_paper_protocol_check import CONTENT_HASH,PROTOCOL,validate_protocol
class U15ProtocolTests(unittest.TestCase):
    def setUp(self):self.protocol=json.loads(PROTOCOL.read_text())
    def test_exact_protocol(self):self.assertEqual(self.protocol["content_hash"],CONTENT_HASH);self.assertEqual(validate_protocol(self.protocol),[])
    def test_generated_time_excluded(self):
        x=copy.deepcopy(self.protocol);x["generated_utc"]="2030";self.assertEqual(validate_protocol(x),[])
    def test_field_semantics_tamper_fails(self):
        x=copy.deepcopy(self.protocol);x["official_field_contract"]["primary_aggressive_buy_field"]="volume";self.assertTrue(validate_protocol(x))
        x=copy.deepcopy(self.protocol);x["official_field_contract"]["infer_from_total_volume_price_or_trade_count_allowed"]=True;self.assertTrue(validate_protocol(x))
    def test_parameter_or_gate_tamper_fails(self):
        x=copy.deepcopy(self.protocol);x["event_identity"]["candidate_taker_buy_share_minimum"]="0.5900";self.assertTrue(validate_protocol(x))
        x=copy.deepcopy(self.protocol);x["paper_gates"]["complete_is_independent_episodes_minimum"]=89;self.assertTrue(validate_protocol(x))
    def test_permission_escalation_fails(self):
        for key in ("data_field_qualification_complexity_and_preflight","event_scan","formal_returns","oos","m2"):
            x=copy.deepcopy(self.protocol);x["authorizations"][key]=True;self.assertTrue(validate_protocol(x),key)
    def test_oos_or_causal_timing_tamper_fails(self):
        x=copy.deepcopy(self.protocol);x["scope"]["oos_opened"]=True;self.assertTrue(validate_protocol(x))
        x=copy.deepcopy(self.protocol);x["observation_contract"]["search_later_if_reference_missing"]=True;self.assertTrue(validate_protocol(x))
if __name__=="__main__":unittest.main()
