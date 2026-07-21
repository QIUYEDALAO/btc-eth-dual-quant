#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json
from scripts.u22_cross_sectional_data_qualification import CONFIG,canonical_hash
RESULT=ROOT/"reports/m1/evidence/u22_cross_sectional_data_qualification_v1.json";EXPECTED_CONTRACT="59cf9567c06b73418404202063407f716056c80d584993b2b50a4b5b75482875";EXPECTED_RESULT="9b009c6b940e338cc77f8f3ea9e8dd473689c739d6c247ad0ba078c3f40a2334"
def validate(config:Mapping[str,Any],result:Mapping[str,Any])->list[str]:
 f=[]
 if config.get("content_hash")!=EXPECTED_CONTRACT or canonical_hash(config)!=EXPECTED_CONTRACT:f.append("contract identity")
 identity={k:v for k,v in result.items() if k!="qualification_content_hash"}
 if result.get("qualification_content_hash")!=EXPECTED_RESULT or identity_hash(identity)!=EXPECTED_RESULT:f.append("result identity")
 c=result.get("counts",{})
 if result.get("status")!="pass" or c.get("archive_count")!=27736 or c.get("manifests_exact")!=19 or c.get("eligible_structural_decisions")!=37401 or c.get("maximum_independent_theoretical_24h_episodes")!=1514 or c.get("maximum_independent_theoretical_24h_episodes",0)<400:f.append("qualification/ceiling")
 for key in ("source_orders","same_reader_orders"):
  rows=result.get(key,[])
  if len(rows)!=3 or len({r.get("content_identity_hash") for r in rows})!=1:f.append(key)
 b=result.get("pre_freeze_complexity",{})
 if b!={"status":"verified_pass","passes":3,"rerun_during_qualification":False,"market_outcomes_read":0}:f.append("complexity")
 iso=result.get("isolation",{});zero=("oos_ohlcv_values_decoded","price_fields_decoded_during_preflight","return_rows_generated","dispersion_rows_generated","leader_rows_generated","event_rows_generated","path_rows_generated","formal_return_rows_generated")
 if iso.get("oos_opened") is not False or any(iso.get(k)!=0 for k in zero):f.append("isolation")
 if [k for k,v in result.get("authorizations",{}).items() if v] != ["one_sealed_is_paper_observation"]:f.append("authorization")
 if result.get("network_accessed") is not False or result.get("production_evidence_mutated") is not False:f.append("scope")
 return f
def main()->int:
 f=validate(load_json(CONFIG),load_json(RESULT));print("u22_cross_sectional_data_qualification_check "+("PASS" if not f else "FAIL")+f" hash={EXPECTED_RESULT} ceiling=1514");return bool(f)
if __name__=="__main__":raise SystemExit(main())
