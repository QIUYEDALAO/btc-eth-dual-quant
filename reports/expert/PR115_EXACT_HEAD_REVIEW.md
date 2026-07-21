# PR #115 Exact-Head Independent Review

## Target

- Repository: `QIUYEDALAO/btc-eth-dual-quant`
- PR: `#115`
- Exact head: `60e49ee7cb6812593098c2f13049b921e5b3b4b5`
- Base at review: `1e8a87682835544b23c82e4aab1d0072e274d59a`
- GitHub selective validation: success

## Verdict

`approve`; critical findings `0`; high findings `0`.

The reviewed head truthfully freezes the pre-performance hard stop. Pinned
Freqtrade 2026.6 runtime identity and all six candidate causal validations pass,
while all 92 point-in-time membership exits lack a frozen exact-boundary 5m
archive. IS and selection trials remain zero and OOS remains false/false/0/0.

The stop is a data-authority failure, not a strategy-performance result. The
reviewed checker reconstructs the fixed boundary set from hash-bound authority
and rejects synthetic/last price, forward search, unfrozen sources,
future-membership lookahead and current-member backfill.

PR #115 was merged without changing the reviewed head as merge commit
`e19962f50b091b5c1fea363d20ee078fcd69cc37`.

## Narrow Follow-On Authorization

One result-blind, IS-only boundary-price authority may be designed, acquired
from official public sources, validated and frozen for exactly the 92
`(symbol, membership_end_exclusive)` boundaries bound by
`e9844902eaa7234a5476a080e937cfbf51f70913cb9ff1b903b907cad08280fa`.

It must use exact boundary rows, preserve zero OOS decode, remain a forced-exit
lookup separate from candidate OHLCV/indicator history, freeze reset/rewarm
semantics across inactive intervals, pass 92/92 with deterministic and tamper
tests, and receive separate exact-head review and merge before original IS.

The reviewer-provided machine-decision canonical content hash is
`82acac46ce4e81cdab071635d986b17dfe1996091e4aa55cba3de5007b49cea4`.

## Non-Blocking Hardening

- Materialization must explicitly require `eligibility_status == "qualified"`.
- Future boundary and IS evidence must record the complete command string as
  well as exit code and stdout/stderr hashes.

No original IS, OOS, dry-run, API/private endpoint, paper/live, order placement,
`execution/live` or M2 authority is granted by this review.
