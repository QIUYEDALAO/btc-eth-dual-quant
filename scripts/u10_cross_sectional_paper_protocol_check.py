#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];PATH=ROOT/"config/u10_cross_sectional_paper_protocol_v1.json";EXPECTED="be205bf40dcab624667b97e43bc158ea2473fe15de2ce9846a6bb198575fa43b"
def load():return json.loads(PATH.read_text())
def h(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate(d:Mapping[str,Any])->list[str]:
 f=[];identity={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}}
 if d.get("content_hash")!=EXPECTED or h(identity)!=EXPECTED:f.append("protocol identity changed")
 if d.get("candidate_id")!="U10-CROSS-SECTIONAL-VOLUME-CONFIRMED-RELATIVE-TREND-CONTINUATION" or d.get("design_content_hash")!="af9ac64043adacad08ef834567ff976b26723fb1468d1a7a0d43e6fa5eaa40e5":f.append("candidate binding changed")
 e=d.get("event_identity",{});expected={"relative_trend_days":7,"recent_volume_share_days":3,"baseline_volume_share_days":21,"required_completed_history_days":28,"representatives_per_decision_time":1,"current_membership_backfill_allowed":False,"replacement_member_allowed":False,"outcome_or_future_price_used_for_selection":False}
 if any(e.get(k)!=v for k,v in expected.items()):f.append("event identity changed")
 if e.get("relative_trend_gate")!="at_least_0.0300_and_in_highest_ceil_eligible_count_divided_by_four" or e.get("volume_share_ratio_gate")!="at_least_1.25_and_in_highest_ceil_eligible_count_divided_by_four":f.append("joint thresholds changed")
 ceiling=d.get("pre_result_sample_ceiling",{})
 if ceiling.get("minimum_theoretical_constant_membership_72h_episodes")!=400 or ceiling.get("frozen_complete_is_episode_gate")!=90 or ceiling.get("must_pass_before_any_event_or_path_scan") is not True:f.append("pre-result sample ceiling changed")
 obs=d.get("observation_contract",{})
 if obs.get("reference")!="first_expected_5m_open_strictly_after_completed_decision_day" or obs.get("search_later_if_reference_missing") is not False or obs.get("horizon_hours")!=[1,2,4,8,12,24,48,72] or obs.get("formal_strategy_return") is not False:f.append("causal observation contract changed")
 g=d.get("paper_gates",{});expected_g={"complete_is_independent_episodes_minimum":90,"projected_full_independent_episodes_minimum":120,"projected_sealed_oos_independent_episodes_minimum":30,"combined_median_72h_relative_continuation_minimum":"0.0180","combined_median_72h_candidate_absolute_close_displacement_minimum":"0.0180","fraction_complete_episodes_with_positive_72h_relative_continuation_minimum":"0.60","qualification_quarantine_lifecycle_or_order_mismatches_maximum":0}
 if any(g.get(k)!=v for k,v in expected_g.items()):f.append("Paper Gates changed")
 if d.get("scope",{}).get("oos_opened") is not False or d.get("projection",{}).get("may_read_oos_events_prices_or_counts") is not False:f.append("OOS seal changed")
 if [k for k,v in d.get("authorizations",{}).items() if v] != ["paper_protocol_frozen","exact_head_independent_review"]:f.append("authorization matrix changed")
 return f
def main()->int:
 f=validate(load())
 if f:print("u10_cross_sectional_paper_protocol_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u10_cross_sectional_paper_protocol_check PASS hash={EXPECTED}");return 0
if __name__=="__main__":raise SystemExit(main())
