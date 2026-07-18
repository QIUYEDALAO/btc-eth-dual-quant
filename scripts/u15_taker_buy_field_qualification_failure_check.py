#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,zipfile
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];EVIDENCE=ROOT/"reports/m1/evidence/u15_taker_buy_field_qualification_failure_v1.json";EXPECTED="83eb8ac2ec1726884f9b3f37bcfe0c13620bca06e98e7539a0e79466d8d63c28"
def canonical_hash(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate(d:Mapping[str,Any],raw_root:Path|None=None)->list[str]:
    f=[];identity={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}}
    if d.get("content_hash")!=EXPECTED or canonical_hash(identity)!=EXPECTED:f.append("failure evidence identity changed")
    failure=d.get("failure",{})
    if d.get("status")!="failed_pre_result_field_qualification" or failure.get("gate")!="official_field_contract.required_numeric_invariants.quote_asset_volume_strictly_positive" or failure.get("quote_asset_volume")!="0.00000000":f.append("field failure changed")
    accounting=d.get("execution_accounting",{})
    zeros=("taker_state_rows_generated","candidate_rows_generated","event_rows_generated","path_rows_generated","return_rows_generated","oos_values_decoded")
    if accounting.get("field_scan_stopped_at_first_failure") is not True or accounting.get("three_order_field_scan_completed") is not False or accounting.get("complexity_benchmark_completed") is not False or any(accounting.get(k)!=0 for k in zeros):f.append("fail-closed accounting changed")
    decision=d.get("decision",{})
    if decision.get("candidate_closed") is not True or any(v is not False for k,v in decision.items() if k!="candidate_closed"):f.append("decision authorization changed")
    if raw_root is not None:
        p=raw_root/failure["archive_relative_path"]
        if hashlib.sha256(p.read_bytes()).hexdigest()!=failure["archive_sha256"]:f.append("archive identity changed")
        with zipfile.ZipFile(p) as z:
            found=None
            for line in z.open(z.infolist()[0]):
                if line.startswith(f"{failure['open_time_ms']},".encode()):found=line.rstrip(b"\r\n");break
        if found is None or hashlib.sha256(found).hexdigest()!=failure["raw_line_sha256"]:f.append("raw row identity changed")
    return f
def main()->int:
    f=validate(json.loads(EVIDENCE.read_text()),ROOT/"storage/raw/liquid_universe")
    if f:print("u15_taker_buy_field_qualification_failure_check FAIL");[print(f"- {x}") for x in f];return 1
    print(f"u15_taker_buy_field_qualification_failure_check PASS hash={EXPECTED}");return 0
if __name__=="__main__":raise SystemExit(main())
