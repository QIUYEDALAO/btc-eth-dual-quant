#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];PATH=ROOT/"config/u09_cross_sectional_paper_protocol_v1.json";EXPECTED="874b93ce7c300c14663147041d351efae7dd22a4a20ab76d837474ca6b2584ae"
def load():return json.loads(PATH.read_text())
def h(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate(d:Mapping[str,Any])->list[str]:
 f=[];identity={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}}
 if d.get("content_hash")!=EXPECTED or h(identity)!=EXPECTED:f.append("protocol identity changed")
 if d.get("candidate_id")!="U09-CROSS-SECTIONAL-IDIOSYNCRATIC-VOLATILITY-QUALITY-PERSISTENCE" or d.get("design_content_hash")!="4830e361b66cd434e54a5ed284d0ad1e85c1e9270d3542dacf3efec5f4eee6f2":f.append("candidate binding changed")
 schedule=d.get("decision_schedule",{})
 if schedule.get("first_anchor")!="2020-01-06T00:00:00Z" or schedule.get("anchor_interval_hours")!=336 or schedule.get("overlapping_primary_observation_windows") is not False:f.append("decision schedule changed")
 event=d.get("quality_event",{});expected={"estimation_hours":168,"half_window_hours":84,"minimum_active_members_each_hour":10,"minimum_cohort_members":1,"current_membership_backfill_allowed":False,"replacement_member_allowed":False,"outcome_or_future_price_used_for_selection":False}
 if any(event.get(k)!=v for k,v in expected.items()):f.append("quality event identity changed")
 obs=d.get("observation_contract",{})
 if obs.get("reference")!="first_expected_5m_open_strictly_after_anchor" or obs.get("search_later_if_reference_missing") is not False or obs.get("horizon_hours")!=[24,72,168,336] or obs.get("formal_strategy_return") is not False:f.append("causal observation contract changed")
 g=d.get("paper_gates",{});expected_g={"complete_is_independent_episodes_minimum":80,"projected_full_independent_episodes_minimum":110,"projected_sealed_oos_independent_episodes_minimum":30,"combined_median_336h_relative_quality_persistence_minimum":"0.0180","combined_median_336h_cohort_absolute_close_displacement_minimum":"0.0180","fraction_complete_episodes_with_positive_336h_relative_quality_persistence_minimum":"0.60","qualification_quarantine_lifecycle_or_order_mismatches_maximum":0}
 if any(g.get(k)!=v for k,v in expected_g.items()):f.append("Paper Gates changed")
 if d.get("scope",{}).get("oos_opened") is not False or d.get("projection",{}).get("may_read_oos_events_prices_or_counts") is not False:f.append("OOS seal changed")
 if [k for k,v in d.get("authorizations",{}).items() if v] != ["paper_protocol_frozen","exact_head_independent_review"]:f.append("authorization matrix changed")
 forbidden={"target","stop","position_cap","take_profit","sharpe","drawdown","equity_curve","strategy_rules"}
 if set(d).intersection(forbidden):f.append("premature strategy or performance field")
 return f
def main()->int:
 f=validate(load())
 if f:print("u09_cross_sectional_paper_protocol_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u09_cross_sectional_paper_protocol_check PASS hash={EXPECTED}");return 0
if __name__=="__main__":raise SystemExit(main())
