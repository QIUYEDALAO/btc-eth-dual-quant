# U-03F Liquid Universe V4 Independent Audit Report

- Verdict: failed_audit
- Range: 2020-01 through 2026-06
- Source freeze: `c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c`
- Production artifact set: `4cfca060b423f4071c831c9ce52556a3a66837fb7326f689245253e13165fde6`
- Independent artifact set: `c7c8e564db713c9268fcd907f8b28cf3f5f595fa08d0755d96c40d91fe237236`
- Months compared: 78
- Membership rows compared: 1170
- Critical findings: 1
- High findings: 7
- Production evidence mutated: no
- Network accessed: no
- Strategy/events/signals/returns/OOS accessed: no
- U-04 authorized: no
- M2 authorized: no

## Audit Coverage

- Frozen source archives read: 27736
- Production manifests compared: 15
- Exact production manifests: 10
- Mismatched production manifests: 5
- Independent gap records: 241
- Independent synchronized global windows: 16
- Independent symbol-month quarantines: 2

## Independent Runs

- normal: artifact_set=`c7c8e564db713c9268fcd907f8b28cf3f5f595fa08d0755d96c40d91fe237236`; source=`bb129fd08b03e9426e457f2885f0b8feff1922847f16d9e6923c78667f4ddc84`; membership=`aa1fcd7e7967e75589284a61281b78a3f558e3d751322d0593f9b0b5d43471d2`; grid=`4563a736a010dbed927f840bd6316833dae26b86dfd9bcd226687e6a00418fba`; lifecycle=`e2f1db91f39a96fdd898affe3d0bb2d99972bd78c0d9b1c01ad075514a544736`; panel=`06e40d1de13b3abd6c4581dde377e43c998c07fda7f6da4f523df4e45e1eebb7`
- reverse: artifact_set=`c7c8e564db713c9268fcd907f8b28cf3f5f595fa08d0755d96c40d91fe237236`; source=`bb129fd08b03e9426e457f2885f0b8feff1922847f16d9e6923c78667f4ddc84`; membership=`aa1fcd7e7967e75589284a61281b78a3f558e3d751322d0593f9b0b5d43471d2`; grid=`4563a736a010dbed927f840bd6316833dae26b86dfd9bcd226687e6a00418fba`; lifecycle=`e2f1db91f39a96fdd898affe3d0bb2d99972bd78c0d9b1c01ad075514a544736`; panel=`06e40d1de13b3abd6c4581dde377e43c998c07fda7f6da4f523df4e45e1eebb7`
- shuffled: artifact_set=`c7c8e564db713c9268fcd907f8b28cf3f5f595fa08d0755d96c40d91fe237236`; source=`bb129fd08b03e9426e457f2885f0b8feff1922847f16d9e6923c78667f4ddc84`; membership=`aa1fcd7e7967e75589284a61281b78a3f558e3d751322d0593f9b0b5d43471d2`; grid=`4563a736a010dbed927f840bd6316833dae26b86dfd9bcd226687e6a00418fba`; lifecycle=`e2f1db91f39a96fdd898affe3d0bb2d99972bd78c0d9b1c01ad075514a544736`; panel=`06e40d1de13b3abd6c4581dde377e43c998c07fda7f6da4f523df4e45e1eebb7`

## Production Comparison

| Artifact | Production | Independent | Exact | Rows | Types | Mismatches | First mismatch |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| V3_V4_diff | `32a944d4dbc5232e4a4ec91187722004e4db7ed4b434fde35662351145dc8d48` | `7e2dadbeba85bca25afdb28207d8a71393c02c1d16151a84eee29913c4e0033f` | false | true | true | 2 | $.content.v4_status: 'pass' != 'blocked' |
| active_universe_manifest | `416941b6c8f50472c4ec6fe0edf5070982f508bc68d803e03b7f94995898379d` | `416941b6c8f50472c4ec6fe0edf5070982f508bc68d803e03b7f94995898379d` | true | true | true | 0 | none |
| candidate_eligibility_manifest | `2d116eb8c22419f124a6865937b3a3e5adad4c6c3fefd4f81a3f93719b389d06` | `2d116eb8c22419f124a6865937b3a3e5adad4c6c3fefd4f81a3f93719b389d06` | true | true | true | 0 | none |
| complete_day_mask | `c7c497147ce5d00081dae5c4e5dd993447507ffe596fbfea10dc28880595a95f` | `c7c497147ce5d00081dae5c4e5dd993447507ffe596fbfea10dc28880595a95f` | true | true | true | 0 | none |
| expected_grid_manifest | `38c1c703a80025307c83d5fe5bcdb1ce933ef8061bf61f96dd36d6b9ee8513ff` | `b484effe913aaa7c02b10381b50e0d74751db51f0182c9562507cd42ea1499c7` | false | true | true | 372 | $.content[2].actual_count: 8270 != 8269 |
| lifecycle_event_quarantine_manifest | `c4930bb769c70e2f26cdd2cff25c80391fa254afc0d26d5dd1eca939d27f20a4` | `c4930bb769c70e2f26cdd2cff25c80391fa254afc0d26d5dd1eca939d27f20a4` | true | true | true | 0 | none |
| lifecycle_policy_manifest | `9ba2dfdd310319475a719291c81eaf93930273732db169d997c9c8252a107f13` | `9ba2dfdd310319475a719291c81eaf93930273732db169d997c9c8252a107f13` | true | true | true | 0 | none |
| lifecycle_resolution_registry | `adccc1f752c171096e6906057225710dd58632744d80927f53f7a1e4a587fbef` | `adccc1f752c171096e6906057225710dd58632744d80927f53f7a1e4a587fbef` | true | true | true | 0 | none |
| membership_manifest | `bcd93c0a4fdc7b1ca235ff8aa62722ecd38a6b990302886a3e91318763077ec5` | `bcd93c0a4fdc7b1ca235ff8aa62722ecd38a6b990302886a3e91318763077ec5` | true | true | true | 0 | none |
| qualification_summary | `1c989a0d14ea7cbf461de6fb178f3b7238a5cd508972d518eef8610d14bd839b` | `038ede3d6a9636f74f1015c87e998b00e2f34d68c629a92540ed56f21d126eb7` | false | false | true | 127 | $.content.blockers: length 0 != 119 |
| qualified_panel_manifest | `cc5299a52f11678ddbcee895b54ca20b3eba6079d814c802823c2a2843270ab5` | `54a5b9630e9b30c1f068c9e40433066af8c1fbceb02d430504c395052f91eb64` | false | true | true | 76 | $.content[285].quarantined_1h_count: 5 != 6 |
| raw_row_quarantine_manifest | `ce97b4826e8305b7d28a27b6693dc120b5b1a8ce5a5cc8462581ace8f68bb4e3` | `ce97b4826e8305b7d28a27b6693dc120b5b1a8ce5a5cc8462581ace8f68bb4e3` | true | true | true | 0 | none |
| row_conflict_resolution_manifest | `0ed070e44351864473f13e1b127a3ab04464be13477776ec32abbedaf2beac15` | `0ed070e44351864473f13e1b127a3ab04464be13477776ec32abbedaf2beac15` | true | true | true | 0 | none |
| source_manifest | `b4dd05d6cb1375c3a6ec3781060e1179845155d3e7e91525921de5f0b9499b39` | `994b846a85f0ef8d588cc9afaed8ebfc90f43e084b6724290e89a5660ad253d1` | false | true | true | 110 | $.content[723].derived_1h_count: 739 != 738 |
| symbol_availability_manifest | `1bf3eb5bfb403fbddb12970a2ea4c53963219766a49f0737e5f113023ef39f19` | `1bf3eb5bfb403fbddb12970a2ea4c53963219766a49f0737e5f113023ef39f19` | true | true | true | 0 | none |

## Minimal Counterexamples

- V3_V4_diff: $.content.v4_status: 'pass' != 'blocked'; production=`32a944d4dbc5232e4a4ec91187722004e4db7ed4b434fde35662351145dc8d48`; independent=`7e2dadbeba85bca25afdb28207d8a71393c02c1d16151a84eee29913c4e0033f`; mismatches=2
- expected_grid_manifest: $.content[2].actual_count: 8270 != 8269; production=`38c1c703a80025307c83d5fe5bcdb1ce933ef8061bf61f96dd36d6b9ee8513ff`; independent=`b484effe913aaa7c02b10381b50e0d74751db51f0182c9562507cd42ea1499c7`; mismatches=372
- qualification_summary: $.content.blockers: length 0 != 119; production=`1c989a0d14ea7cbf461de6fb178f3b7238a5cd508972d518eef8610d14bd839b`; independent=`038ede3d6a9636f74f1015c87e998b00e2f34d68c629a92540ed56f21d126eb7`; mismatches=127
- qualified_panel_manifest: $.content[285].quarantined_1h_count: 5 != 6; production=`cc5299a52f11678ddbcee895b54ca20b3eba6079d814c802823c2a2843270ab5`; independent=`54a5b9630e9b30c1f068c9e40433066af8c1fbceb02d430504c395052f91eb64`; mismatches=76
- source_manifest: $.content[723].derived_1h_count: 739 != 738; production=`b4dd05d6cb1375c3a6ec3781060e1179845155d3e7e91525921de5f0b9499b39`; independent=`994b846a85f0ef8d588cc9afaed8ebfc90f43e084b6724290e89a5660ad253d1`; mismatches=110

## Reconciliation Summary

- Row-conflict resolution: exact
- Lifecycle policy/registry/availability: exact
- Membership: exact
- Expected grid: mismatch
- Gap/quarantine: exact
- Complete-day mask: exact
- Active universe: exact
- Qualified panel: mismatch
- KLAY lifecycle affected rows: exact through the lifecycle registry, availability and quarantine manifests

## Integer-Time Conformance

- Full-data integer recomputation executed: true
- Current-data artifact difference: true
- Policy conformance: fail
- Boundary differential: `{"current_boundary_cases":3,"current_boundary_mismatches":0,"fault_exact_milliseconds":9007199254740,"fault_float_milliseconds":9007199254741,"fault_microseconds":9007199254740999,"fault_mismatch":true}`

- src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py:line 33: float epoch reconstruction
- src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py:line 37: datetime.timestamp authority path
- src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py:line 45: datetime.timestamp authority path
- src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py:line 53: float epoch reconstruction
- scripts/liquid_universe_v4_public_run.py:line 118: float epoch reconstruction
- scripts/liquid_universe_v4_public_run.py:line 271: datetime.timestamp authority path

## Report And Run Bindings

- Qualification report exact: false
- Committed qualification report: `ad414f760655645e20c6bc20c49c0f25bf3aea1d5f47b373fc254364aab91e2a`
- Run-recorded qualification report: `dec61cf9d0cdd2a1182b5622e85cfdf9dbc6043e7342ba4f2400fa66245bc2b3`
- V3/V4 diff report exact: true

## Findings

### Critical

- independent_integer_recomputation_differs_from_production_evidence

### High

- integer_only_policy_violation:src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py:line 33: float epoch reconstruction
- integer_only_policy_violation:src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py:line 37: datetime.timestamp authority path
- integer_only_policy_violation:src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py:line 45: datetime.timestamp authority path
- integer_only_policy_violation:src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py:line 53: float epoch reconstruction
- integer_only_policy_violation:scripts/liquid_universe_v4_public_run.py:line 118: float epoch reconstruction
- integer_only_policy_violation:scripts/liquid_universe_v4_public_run.py:line 271: datetime.timestamp authority path
- run_manifest_qualification_report_hash_does_not_match_committed_report

## Decision

The audit result is evidence only. It does not modify V4 production artifacts and does not authorize U-04, strategy work, OOS, trading, or M2.
