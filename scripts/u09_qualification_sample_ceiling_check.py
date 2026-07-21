#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from datetime import datetime,timedelta
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];E=ROOT/"reports/m1/evidence/u09_qualification_sample_ceiling_correction_v1.json";REPORT=ROOT/"reports/m1/U09_QUALIFICATION_SAMPLE_CEILING_CORRECTION.md";EXPECTED="c6902525fd4163b0cf929242dc0b88404422421f03745385f615c9dafb3f4479"
def h(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def recompute(d:Mapping[str,Any])->tuple[int,dict[str,int]]:
 c=d["calendar_inputs"];x=datetime.fromisoformat(c["first_anchor"].replace("Z","+00:00"));end=datetime.fromisoformat(c["is_end_exclusive"].replace("Z","+00:00"));step=timedelta(hours=c["anchor_interval_hours"]);offset=timedelta(minutes=c["reference_offset_minutes"]);horizon=timedelta(hours=c["primary_horizon_hours"]);valid=[]
 while x+horizon<=end:
  ref=x+offset;last=ref+horizon-timedelta(minutes=5)
  if (ref.year,ref.month)==(last.year,last.month):valid.append(x)
  x+=step
 years={str(y):sum(x.year==y for x in valid) for y in sorted({x.year for x in valid})};return len(valid),years
def validate(d:Mapping[str,Any],text:str)->list[str]:
 f=[];i={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}}
 if d.get("content_hash")!=EXPECTED or h(i)!=EXPECTED:f.append("correction identity changed")
 n,years=recompute(d);c=d.get("counts",{})
 if n!=66 or c.get("maximum_constant_membership_primary_episodes")!=n or c.get("maximum_by_year")!=years or c.get("frozen_minimum_complete_is_episodes")!=80 or c.get("shortfall")!=14:f.append("sample ceiling changed")
 if d.get("status")!="failed_pre_observation_sample_ceiling":f.append("status changed")
 decision=d.get("decision",{})
 if not all(decision.get(k) is True for k in ("qualification_pass_superseded","candidate_closed","next_independent_candidate_decision_only")) or any(decision.get(k) is True for k in ("paper_observation_authorized","protocol_change_authorized","gate_reduction_authorized")):f.append("decision authorization changed")
 isolation=d.get("isolation",{})
 if isolation.get("oos_opened") is not False or isolation.get("second_result_bearing_run_executed") is not False or any(isolation.get(k)!=0 for k in ("price_rows_read_for_correction","event_rows_generated","path_rows_generated","return_rows_generated")):f.append("isolation changed")
 for m in ("Status: `failed_pre_observation_sample_ceiling`","at most 66","minimum is 80"):
  if m not in text:f.append(f"report marker missing: {m}")
 return f
def main()->int:
 d=json.loads(E.read_text());f=validate(d,REPORT.read_text())
 if f:print("u09_qualification_sample_ceiling_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u09_qualification_sample_ceiling_check PASS hash={EXPECTED} max=66 gate=80");return 0
if __name__=="__main__":raise SystemExit(main())
