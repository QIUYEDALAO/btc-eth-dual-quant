# Liquid Spot Universe V4 Implementation Status

- Status: `implementation_pass_fixture_only_public_requalification_not_run`
- Scope: generic lifecycle availability implementation and deterministic fixtures only
- Base main: `0f5f76f86973316ac66b8e3f9d6e65419b310ec9`
- Real public requalification run: no
- V4 active qualification authority: no
- V3 blocked evidence preserved: yes
- Independent implementation review required before merge: yes
- U-03F authorized: no
- U-04 authorized: no
- Strategy, events, signals, returns, backtesting, OOS, API/trading, execution/live and M2 authorized: no

## Machine Authority

- ADR-0011 universe policy: `5e05543cc7019fe7aaa6c90ebf78fb26adf084e33cb78aeccf6089202a1b94df`
- V4 contract: `816a354a1fe20ebab4c162ecaefbde47a90d61567f40873e2b477a983d06ee83`
- Lifecycle policy: `7dc02e719f6e41839a1aff8002befd117b2daa7b426edeed9ebb4bd42c303977`
- Lifecycle event registry: `a78c52b183e0270c713dbb9965bd42b1035759b7b2182e49a3416cd8ae73904d`
- Adopted ADR-0014: `2de88986f6123a0d0ddaa2756b6c665a2fc0d3960f24dba1966bd51332becad9`
- Reviewed semantic body: `5c2113edbb7a69b52c1e78e3a6c3f223dac36d21769a9e1c5b815894945f8e99`
- Policy model: `bce56a1070ef0690b13cba492bf9619a456af2618be94eb2ecbe03ea7e709d97`
- Fault matrix: `90beb680e568ab5bc045556ef728e34cd2827d5bf6005ebb524b6e38ed6a199f`
- MC conformance: `303e4d28ea27575ed7fa46e9d9da459e5c237a0390f36f9c9de9cfcd7c9821d2`
- KLAY adjudication evidence: `6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a`
- V3 contract preserved: `f41f5fedf6002487c9d576a39927ade4409d55e1bc0442aa097e6b2ed054b3ed`
- V3 row registry preserved: `570b66e32c3a7ac910ba5ef6688eff966304e65a9519f4f8a902b60fbe4957a4`
- V3 blocked cold artifact set preserved: `f661d7abd99adc4067d354afba0c5421e7d1f33c54f768b89c8011ec01eab4f3`

## Implemented Semantics

- ADR-0013 row conflict resolution remains the existing V3 engine.
- ADR-0014 lifecycle claims are dispatched separately; policy overlap fails closed.
- Lifecycle epochs use inclusive starts and exclusive ends with integer UTC epoch arithmetic.
- Availability masking precedes expected-grid and gap construction.
- Partial lifecycle days cannot enter 90-day ranking or 365-day history windows.
- Post-boundary absence is not a gap; pre-boundary missing data remains blocking.
- Monthly membership remains fixed while timestamped active count may decline.
- Successor metadata is provenance only and creates no automatic epoch or inherited history.
- Runtime modules contain no symbol/date special case and read no Markdown.
- Data policy does not infer exit, settlement, stale price, replacement, cash or return semantics.

## Fixture Evidence

- Frozen fault cases mapped: 37/37
- V4 manifest types generated: 13/13
- Targeted V4 tests: pass
- Full unit suite: 517 tests OK
- Contract/policy/registry checker: pass
- Public rows downloaded: 0
- Public qualification artifacts generated: 0
- Synthetic fills: 0
- Replacement members: 0

## Gate

The implementation is ready only for an independent exact-head implementation review. It is not merged authority and cannot run the fixed-range public requalification until that review returns `approve`, the target head remains unchanged, the implementation merges, and governance closeout completes.
