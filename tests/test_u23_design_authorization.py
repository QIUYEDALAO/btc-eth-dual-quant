import copy,json,unittest
from scripts.u23_design_authorization_check import AUDIT,DECISION,FAILURE,PRIOR,validate
class U23AuthorizationTests(unittest.TestCase):
 def setUp(self):
  load=lambda p:json.loads(p.read_text());self.d,self.f,self.p,self.a=map(load,(DECISION,FAILURE,PRIOR,AUDIT))
 def test_exact(self):self.assertEqual(validate(self.d,self.f,self.p,self.a),[])
 def test_generated_time_excluded(self):
  x=copy.deepcopy(self.d);x["generated_utc"]="2030-01-01T00:00:00Z";self.assertEqual(validate(x,self.f,self.p,self.a),[])
 def test_result_or_authority_tamper(self):
  x=copy.deepcopy(self.f);x["run_content_hash"]="0"*64;self.assertTrue(validate(self.d,x,self.p,self.a))
  x=copy.deepcopy(self.a);x["audit_summary_hash"]="0"*64;self.assertTrue(validate(self.d,self.f,self.p,x))
 def test_inversion_or_escalation_tamper(self):
  x=copy.deepcopy(self.d);x["decision"]["u22_negative_result_inversion_repair_relabeling_or_repackaging_prohibited"]=False;self.assertTrue(validate(x,self.f,self.p,self.a))
  x=copy.deepcopy(self.d);x["authorizations"]["event_scan"]=True;self.assertTrue(validate(x,self.f,self.p,self.a))
if __name__=="__main__":unittest.main()
