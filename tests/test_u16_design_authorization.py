import copy,json,unittest
from scripts.u16_design_authorization_check import DECISION,FAILURE,PRIOR,AUDIT,validate
class U16AuthorizationTests(unittest.TestCase):
    def setUp(self):
        load=lambda p:json.loads(p.read_text());self.d,self.f,self.p,self.a=map(load,(DECISION,FAILURE,PRIOR,AUDIT))
    def test_exact(self):self.assertEqual(validate(self.d,self.f,self.p,self.a),[])
    def test_time_excluded(self):
        d=copy.deepcopy(self.d);d["generated_utc"]="2030";self.assertEqual(validate(d,self.f,self.p,self.a),[])
    def test_escalation(self):
        d=copy.deepcopy(self.d);d["authorizations"]["event_scan"]=True;self.assertTrue(validate(d,self.f,self.p,self.a))
    def test_failure_or_repair_tamper(self):
        f=copy.deepcopy(self.f);f["content_hash"]="0"*64;self.assertTrue(validate(self.d,f,self.p,self.a))
        d=copy.deepcopy(self.d);d["decision"]["u15_field_contract_repair_relaxation_or_repackaging_prohibited"]=False;self.assertTrue(validate(d,self.f,self.p,self.a))
if __name__=="__main__":unittest.main()
