#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json
from scripts.u23_cross_sectional_data_qualification import CONFIG,canonical_hash
RESULT=ROOT/"reports/m1/evidence/u23_cross_sectional_data_qualification_v1.json";EXPECTED_CONTRACT="37c1c9b0bdbb13639aea36a1da525163ba4a8142ec1f808bc8cbe1ca0aed7909";EXPECTED_RESULT="08166fb534daf691e069f6ae743b472f0c06879dd060c58f816e4f2d5acef2c5"
def validate(config:Mapping[str,Any],result:Mapping[str,Any])->list[str]:
 f=[]
 if config.get("content_hash")!=EXPECTED_CONTRACT or canonical_hash(config)!=EXPECTED_CONTRACT:f.append("contract identity")
 identity={k:v for k,v in result.items() if k!="qualification_content_hash"}
 if result.get("qualification_content_hash")!=EXPECTED_RESULT or identity_hash(identity)!=EXPECTED_RESULT:f.append("result identity")
 c=result.get("counts",{})
 if result.get("status")!="pass" or c.get("archive_count")!=27736 or c.get("manifests_exact")!=19 or c.get("eligible_structural_decisions")!=7122 or c.get("maximum_independent_theoretical_24h_episodes")!=1031 or c.get("maximum_independent_theoretical_24h_episodes",0)<400:f.append("qualification/ceiling")
 for key in ("source_orders","same_reader_orders"):
  rows=result.get(key,[])
  if len(rows)!=3 or len({r.get("content_identity_hash") for r in rows})!=1:f.append(key)
 b=result.get("pre_freeze_complexity",{})
 if b!={"status":"verified_pass","passes":3,"rerun_during_qualification":False,"market_outcomes_read":0}:f.append("complexity")
 iso=result.get("isolation",{});zero=("oos_ohlcv_values_decoded","ohlcv_fields_decoded_during_preflight","range_rows_generated","return_rows_generated","candidate_rows_generated","event_rows_generated","path_rows_generated","formal_return_rows_generated")
 if iso.get("oos_opened") is not False or any(iso.get(k)!=0 for k in zero):f.append("isolation")
 if [k for k,v in result.get("authorizations",{}).items() if v] != ["one_sealed_is_paper_observation"]:f.append("authorization")
 if result.get("network_accessed") is not False or result.get("production_evidence_mutated") is not False:f.append("scope")
 return f
def main()->int:
 f=validate(load_json(CONFIG),load_json(RESULT));print("u23_cross_sectional_data_qualification_check "+("PASS" if not f else "FAIL")+f" hash={EXPECTED_RESULT} ceiling=1031");return bool(f)
if __name__=="__main__":raise SystemExit(main())
