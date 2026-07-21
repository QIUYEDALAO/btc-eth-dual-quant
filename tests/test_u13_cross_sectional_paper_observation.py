from __future__ import annotations
import copy, subprocess, sys, unittest
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u04_cross_sectional_paper_observation import ONE_DAY_MS
from scripts.u13_cross_sectional_paper_observation import cluster_events
from scripts.u13_cross_sectional_paper_observation_check import EVIDENCE, EXPECTED_MANIFESTS, RUN, validate


class U13PaperObservationCoreTests(unittest.TestCase):
    def test_connected_24h_cluster_uses_all_candidates(self):
        rows=[{"decision_time_ms":0,"symbol":"A","event_id":"a"},{"decision_time_ms":ONE_DAY_MS,"symbol":"B","event_id":"b"},{"decision_time_ms":2*ONE_DAY_MS,"symbol":"C","event_id":"c"},{"decision_time_ms":4*ONE_DAY_MS,"symbol":"D","event_id":"d"}]
        self.assertEqual([row["symbol"] for row in cluster_events(rows)],["A","D"])
    def test_frozen_failed_result_and_tamper_detection(self):
        run=load_json(RUN); manifests={name:load_json(EVIDENCE/f"{name}.json") for name in EXPECTED_MANIFESTS}; self.assertEqual(validate(run,manifests),[])
        changed=copy.deepcopy(run); changed["metrics"]["complete_is_independent_episodes"]=90; self.assertTrue(validate(changed,manifests))
        changed=copy.deepcopy(run); changed["authorizations"]["paper_result_independent_review"]=True; self.assertTrue(validate(changed,manifests))
    def test_second_result_run_is_locked(self):
        completed=subprocess.run([sys.executable,"scripts/u13_cross_sectional_paper_observation.py"],cwd=EVIDENCE.parents[3],text=True,capture_output=True,check=False)
        self.assertEqual(completed.returncode,2); self.assertIn("second result-bearing run is prohibited",completed.stderr)


if __name__ == "__main__": unittest.main()
