#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json
from scripts.u21_cross_sectional_data_qualification import CONFIG,canonical_hash
RESULT=ROOT/"reports/m1/evidence/u21_cross_sectional_data_qualification_v1.json";EXPECTED_CONTRACT="7e159601a935a90d4ac156bb64f2fa379abca5bedb4471570e43aef348d9ee5c";EXPECTED_RESULT="33e53b7fd32c6610349f99bb01cf71143ab9837289198266fd1b25f6e7147a1b"
def validate(config,result):
    f=[]
    if config.get("content_hash")!=EXPECTED_CONTRACT or canonical_hash(config)!=EXPECTED_CONTRACT:f.append("contract identity")
    identity={k:v for k,v in result.items() if k!="qualification_content_hash"}
    if result.get("qualification_content_hash")!=EXPECTED_RESULT or identity_hash(identity)!=EXPECTED_RESULT:f.append("result identity")
    failure=result.get("failure",{})
    if result.get("status")!="failed_pre_result_complexity" or failure.get("stage")!="first_synthetic_million_row_complexity_pass" or failure.get("benchmark_passes_completed")!=0 or failure.get("retry_executed") is not False:f.append("failure status")
    isolation=result.get("isolation",{})
    if any(v not in (0,False) for v in isolation.values()):f.append("isolation")
    if any(result.get("authorizations",{}).values()):f.append("authorization")
    if result.get("candidate_closed") is not True or result.get("network_accessed") is not False or result.get("production_evidence_mutated") is not False:f.append("scope")
    return f
def main():
    f=validate(load_json(CONFIG),load_json(RESULT));print("u21_cross_sectional_data_qualification_check "+("PASS failed_pre_result_complexity" if not f else "FAIL")+f" hash={EXPECTED_RESULT}");return bool(f)
if __name__=="__main__":raise SystemExit(main())
