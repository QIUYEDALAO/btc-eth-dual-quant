#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json
from scripts.u16_cross_sectional_data_qualification import CONFIG,canonical_hash
RESULT=ROOT/"reports/m1/evidence/u16_cross_sectional_data_qualification_v1.json";EXPECTED_CONTRACT="b66fdd6de5443cf3139d93cf2f8c81c5b2f6914fa4c7b3c8cb65fe4acf1ad2a4";EXPECTED_RESULT="5dc4850a1d940d05581774a1270ec6c9cdc4d5f8702a5614a81a01928842e949"
def validate(config:Mapping[str,Any],result:Mapping[str,Any])->list[str]:
    f=[]
    if config.get("content_hash")!=EXPECTED_CONTRACT or canonical_hash(config)!=EXPECTED_CONTRACT:f.append("contract identity changed")
    identity={k:v for k,v in result.items() if k!="qualification_content_hash"}
    if result.get("qualification_content_hash")!=EXPECTED_RESULT or identity_hash(identity)!=EXPECTED_RESULT:f.append("result identity changed")
    counts=result.get("counts",{})
    if result.get("status")!="pass" or counts.get("archive_count")!=27736 or counts.get("manifests_exact")!=19:f.append("source qualification changed")
    if counts.get("eligible_structural_decisions")!=9016 or counts.get("maximum_independent_theoretical_24h_episodes")!=1331:f.append("structural ceiling changed")
    for key in ("source_orders","same_reader_orders"):
        rows=result.get(key,[])
        if len(rows)!=3 or len({x.get("content_identity_hash") for x in rows})!=1:f.append(f"{key} changed")
    bench=result.get("complexity_benchmark",{});passes=bench.get("passes",[])
    if bench.get("status")!="pass" or len(passes)!=3 or bench.get("market_outcomes_read")!=0 or len({x.get("output_hash") for x in passes})!=1:f.append("complexity identity changed")
    if any(x.get("fixture_rows")!=1000000 or float(x.get("elapsed_seconds",31))>30 or float(x.get("peak_rss_mib",1025))>1024 for x in passes):f.append("complexity Gate changed")
    isolation=result.get("isolation",{});zeros=("oos_ohlcv_values_decoded","price_fields_decoded_during_preflight","common_path_rows_generated","correlation_rows_generated","candidate_rows_generated","event_rows_generated","path_rows_generated","return_rows_generated")
    if isolation.get("oos_opened") is not False or any(isolation.get(k)!=0 for k in zeros):f.append("isolation changed")
    if [k for k,v in result.get("authorizations",{}).items() if v] != ["one_sealed_is_paper_observation"]:f.append("authorization changed")
    return f
def main()->int:
    f=validate(load_json(CONFIG),load_json(RESULT))
    if f:print("u16_cross_sectional_data_qualification_check FAIL");[print(f"- {x}") for x in f];return 1
    print(f"u16_cross_sectional_data_qualification_check PASS hash={EXPECTED_RESULT} ceiling=1331 complexity=3/3");return 0
if __name__=="__main__":raise SystemExit(main())
