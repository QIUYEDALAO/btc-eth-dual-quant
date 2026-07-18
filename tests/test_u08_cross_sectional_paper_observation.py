from __future__ import annotations
import copy,unittest
from decimal import Decimal
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u08_cross_sectional_paper_observation import cluster_events,evaluate_gates,ordered,select_events
from scripts.u08_cross_sectional_paper_observation_check import E,HASHES,REPORT,validate
class U08ObservationTests(unittest.TestCase):
 def setUp(self):self.p=git_json("a516efb32f2058b603918365a6eeaef0fe509361","config/u08_cross_sectional_paper_protocol_v1.json")
 def rows(self):
  prior=[{"symbol":f"S{i:02d}","rank":i+1} for i in range(15)];current=[{"symbol":f"S{i:02d}","rank":i+1} for i in range(13)]+[{"symbol":"NEWB","rank":14},{"symbol":"NEWA","rank":15}];return {"2020-01":prior,"2020-02":current}
 def test_genesis_excluded_and_lowest_rank_wins(self):
  events,a=select_events(self.rows(),0,10**15,"p","q");self.assertEqual(len(events),1);self.assertEqual(events[0]["symbol"],"NEWB");self.assertEqual(a["genesis_months_excluded"],1);self.assertEqual(a["simultaneous_entries_discarded"],1);self.assertEqual(events[0]["reference_open_time_ms"]-events[0]["decision_time_ms"],300000)
 def test_empty_paths_fail_without_gate_mutation(self):
  m,c=evaluate_gates([],self.p,0);self.assertFalse(all(c.values()));self.assertEqual(m["complete_is_independent_episodes"],0);self.assertEqual(self.p["paper_gates"]["complete_is_independent_episodes_minimum"],36)
 def test_all_traversal_orders_accept_episode_key(self):
  rows=[{"decision_time_ms":1,"event_id":"a"},{"decision_time_ms":2,"event_id":"b"}]
  episodes=cluster_events(rows)
  for order in ("normal","reverse","deterministic_shuffled"):self.assertEqual(len(ordered(episodes,order,key=lambda x:int(x["decision_time_ms"]))),len(episodes))
 def test_committed_failed_result_exact_and_tamper_fails(self):
  s=load_json(E/"run_manifest.json");m={n:load_json(E/f"{n}.json") for n in HASHES};t=REPORT.read_text();self.assertEqual(validate(s,m,t),[]);x=copy.deepcopy(s);x["authorizations"]["backtesting"]=True;self.assertTrue(validate(x,m,t));x=copy.deepcopy(s);x["metrics"]["complete_is_independent_episodes"]+=1;self.assertTrue(validate(x,m,t))
if __name__=="__main__":unittest.main()
