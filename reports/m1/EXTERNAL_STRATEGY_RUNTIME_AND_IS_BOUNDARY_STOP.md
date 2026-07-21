# External Strategy Runtime and IS Boundary Stop

## Decision

The pinned runtime and six-candidate synthetic causal stage passed, but the
original-IS stage is blocked before any performance run. The frozen source
authority contains no real 5m archive at any of the 92 point-in-time
membership exit boundaries inside IS. A position that remains open at one of
those boundaries therefore cannot be exited at the exact boundary open without
using an unfrozen source, a synthetic/last price, a forward search, or future
membership information. Every such workaround violates the frozen contract.

Status: `blocked_data_authority_missing_membership_exit_open`.

## Completed work

- PR #113 merged as `d657994b69289d8330acca90f5c1ed301863a3ce`.
- PR #112 merged as `d119593d069a0ec5f0851802cb8ab0df514e3a18`.
- ADR-0017 merged as `1e8a87682835544b23c82e4aab1d0072e274d59a`;
  machine identity `8a4b1d6d859c683bf3a61fd55784083bc04c8169a9cd1cab2362273177b48cdd`.
- Pinned VPS runtime passed under runtime identity
  `a88f0c591bc40d6acdaa3bb8e4fafe5b0dcda398f076f8f265a339caffb9eed1`.
- The exact image is Freqtrade 2026.6 at
  `sha256:d451af021d5e08b70580c0eea5848534e9846b57391b34821c0a5814416397e6`.
- Container and dependency identities are `6e8e5414...8fb56` and
  `665256bb...fb7f64`; runtime used no network, secrets, private endpoint or
  trading process.
- Supertrend, Strategy001, UniversalMACD, Bandtastic, Diamond and Heracles all
  loaded. Observed external parameter-file and config-override counts are zero.
- All six passed original/adapter golden equality, deterministic input order,
  completed-candle/next-open probes, Freqtrade lookahead analysis and recursive
  analysis. Causal summary: `473dd739...a107`, PASS `6/6` versus minimum `5`.

## Data preflight and hard stop

The IS-only materializer verified 855 frozen archives and built 224 derived
files for 56 symbols from 7,393,658 decoded IS 5m rows. Its deterministic
identity is `628bec95...9def`; OOS rows decoded are zero.

The subsequent membership-exit preflight enumerated every active-to-inactive
transition before `2024-09-11T00:00:00Z`:

- required membership exit boundaries: 92;
- boundaries with a frozen next-month 5m archive: 0;
- boundaries without a frozen execution archive: 92.

Machine evidence is
`reports/m1/evidence/external_strategy_runtime/is_boundary_qualification.json`
under `e9844902eaa7234a5476a080e937cfbf51f70913cb9ff1b903b907cad08280fa`.
It binds every symbol, last active month, boundary timestamp and required
archive path, and rejects tampering of the counts, transitions, IS authority or
OOS counters.

This is a data-authority hard stop explicitly allowed by ADR-0017. It is not a
strategy-performance failure and may not be bypassed by changing the six
candidates or their order.

## Result status

- Original IS trials: 0.
- Modified IS trials: 0.
- Selection trial count: 0.
- Base/CostX2 final DSR: not computed because no trial exists.
- Hard-Gate matrix: not materialized.
- Selected candidate: null, not evaluated.
- OOS: authorized/opened/runs/rows decoded = `false/false/0/0`.
- dry-run bot, API/private endpoint, paper/live, order placement,
  `execution/live`, M2: false.

## Required next decision

Do not run IS. A future task must separately authorize and freeze an auditable
membership-exit price authority (or revise the holding/universe contract) before
this route can resume. That decision would change the frozen data/execution
authority and is outside the automatic runtime authorization granted by
ADR-0017. OOS remains sealed regardless of that future decision.
