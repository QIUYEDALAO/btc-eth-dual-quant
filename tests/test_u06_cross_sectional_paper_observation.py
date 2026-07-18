from __future__ import annotations
import unittest
import copy
from decimal import Decimal
from scripts.u04_cross_sectional_paper_observation import ONE_DAY_MS
from scripts.u06_cross_sectional_paper_observation import cluster_events,evaluate_gates,select_events
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u06_cross_sectional_paper_observation_check import E,HASHES,REPORT,validate
class U06PaperObservationTests(unittest.TestCase):
 def setUp(self):self.protocol=git_json("1bb59f1ac9d9e0fd5bacc8c55e572b9a1fbce8cd","config/u06_cross_sectional_paper_protocol_v1.json")
 def fixture(self,current_quote=Decimal("40"),candidate_return=Decimal("0")):
  symbols=tuple(f"S{i:02d}" for i in range(10));daily={s:{} for s in symbols}
  for day in range(31):
   for s in symbols:
    q=current_quote if day==30 and s=="S00" else Decimal("10");o=Decimal("100");c=o*(1+candidate_return) if day==30 and s=="S00" else o;daily[s][day*ONE_DAY_MS]={"open":o,"close":c,"quote":q}
  return daily,{"1970-01":symbols}
 def test_event_accepts_volume_share_absorption_and_is_deterministic(self):
  d,m=self.fixture();events,a=select_events(d,m,30*ONE_DAY_MS,31*ONE_DAY_MS,"p","q");self.assertEqual(len(events),1);self.assertEqual(events[0]["symbol"],"S00");self.assertEqual(a["days_evaluated"],1)
 def test_share_absolute_volume_and_muted_price_gates_reject(self):
  for q,r in ((Decimal("15"),Decimal("0")),(Decimal("40"),Decimal("0.02"))):
   d,m=self.fixture(q,r);events,_=select_events(d,m,30*ONE_DAY_MS,31*ONE_DAY_MS,"p","q");self.assertEqual(events,[])
 def test_72h_connected_cluster_keeps_first(self):
  events=[{"decision_time_ms":h*3600000,"event_id":str(i)} for i,h in enumerate((0,72,144,217))];self.assertEqual([x["event_id"] for x in cluster_events(events)],["0","3"])
 def test_empty_paths_fail_frozen_gates_without_mutation(self):
  metrics,checks=evaluate_gates([],self.protocol,0);self.assertEqual(metrics["complete_is_independent_episodes"],0);self.assertFalse(all(checks.values()));self.assertEqual(self.protocol["volume_share_event"]["baseline_days"],30)
 def test_committed_failed_result_is_exact_and_tamper_fails(self):
  s=load_json(E/"run_manifest.json");m={n:load_json(E/f"{n}.json") for n in HASHES};text=REPORT.read_text();self.assertEqual(validate(s,m,text),[]);c=copy.deepcopy(s);c["authorizations"]["backtesting"]=True;self.assertTrue(validate(c,m,text));c=copy.deepcopy(s);c["metrics"]["complete_is_independent_episodes"]+=1;self.assertTrue(validate(c,m,text))
if __name__=="__main__":unittest.main()
