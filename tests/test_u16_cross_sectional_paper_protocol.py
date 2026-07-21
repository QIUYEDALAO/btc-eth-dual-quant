from __future__ import annotations
import copy,json,unittest
from scripts.u16_cross_sectional_paper_protocol_check import CONTENT_HASH,PROTOCOL,validate_protocol
class U16ProtocolTests(unittest.TestCase):
    def setUp(self):self.p=json.loads(PROTOCOL.read_text())
    def test_exact(self):self.assertEqual(self.p["content_hash"],CONTENT_HASH);self.assertEqual(validate_protocol(self.p),[])
    def test_time_excluded(self):
        x=copy.deepcopy(self.p);x["generated_utc"]="2030";self.assertEqual(validate_protocol(x),[])
    def test_history_or_threshold_tamper(self):
        x=copy.deepcopy(self.p);x["history_contract"]["recent_hours"]=11;self.assertTrue(validate_protocol(x))
        x=copy.deepcopy(self.p);x["correlation_contract"]["recent_correlation_maximum"]="0.20";self.assertTrue(validate_protocol(x))
    def test_terminal_spike_or_gate_tamper(self):
        x=copy.deepcopy(self.p);x["positive_displacement_contract"]["terminal_hour_relative_contribution_maximum_fraction"]="1.00";self.assertTrue(validate_protocol(x))
        x=copy.deepcopy(self.p);x["paper_gates"]["complete_is_independent_episodes_minimum"]=89;self.assertTrue(validate_protocol(x))
    def test_permission_escalation(self):
        for key in ("data_qualification_complexity_and_preflight","event_scan","formal_returns","oos","m2"):
            x=copy.deepcopy(self.p);x["authorizations"][key]=True;self.assertTrue(validate_protocol(x),key)
if __name__=="__main__":unittest.main()
