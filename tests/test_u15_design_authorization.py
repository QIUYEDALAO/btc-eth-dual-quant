import copy,json,unittest
from scripts.u15_design_authorization_check import DECISION,RUN,PRIOR,AUDIT,validate
class T(unittest.TestCase):
 def setUp(self):
  load=lambda p:json.loads(p.read_text());self.d,self.r,self.p,self.a=map(load,(DECISION,RUN,PRIOR,AUDIT))
 def test_exact(self):self.assertEqual(validate(self.d,self.r,self.p,self.a),[])
 def test_time_excluded(self):d=copy.deepcopy(self.d);d["generated_utc"]="2030";self.assertEqual(validate(d,self.r,self.p,self.a),[])
 def test_escalation(self):d=copy.deepcopy(self.d);d["authorizations"]["event_scan"]=True;self.assertTrue(validate(d,self.r,self.p,self.a))
 def test_prior_tamper(self):r=copy.deepcopy(self.r);r["run_content_hash"]="0"*64;self.assertTrue(validate(self.d,r,self.p,self.a))
