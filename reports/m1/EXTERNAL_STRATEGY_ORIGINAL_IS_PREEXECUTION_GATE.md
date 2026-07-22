# External Strategy Original-IS Pre-execution Gate

## Outcome

PR #119 reviewed head `380b50392b3a225bbaf7f0ff4f24041b8fb22666`
passed exact-head GitHub run `29881020014` and ordinary-merged as
`7b6a0601588f4387f8816cf6b49bdf5bf94a18f3`. The completed 92-boundary
authority review Gate is therefore closed and ADR-0017 permits original IS.

No original-IS performance command was started. The offline execution
preflight is contract-clean but environment-blocked because `VPS_HOST` is not
configured and no explicit SSH identity file was supplied. This is a hard
stop before SSH, Docker, Freqtrade or market/result decoding.

## New fail-closed layer

- Post-runtime authority:
  `config/external_strategy_original_is_authority_v1.json`, canonical hash
  `32922386a3984ef96e24ed64e96771e81860b2fbf269c3baf5a46739775bf2ae`.
  It binds ADR-0017/0018, all immutable pre-runtime contracts, six exact
  runtime candidates, six causal PASS results, PR #119 review/Gate/merge and
  the completed 92/92 boundary authority.
- Active-interval isolation:
  `src/btc_eth_dual_quant/audit/external_strategy_isolation.py`, byte SHA-256
  `b4f51df33e8feeb77043ed4ab2291e35e0f8c71d1a118fa970cbef6156b162ba`.
  Every admission interval starts a new indicator age; completed 5m/15m/1h/4h
  candles and startup warmup are derived only inside that interval. Boundary
  rows remain an exact-key execution-side lookup and cannot enter OHLCV or
  indicator history.
- Atomic result evidence:
  `src/btc_eth_dual_quant/audit/external_strategy_trial_bundle.py`, byte
  SHA-256
  `5612ac8b02dc81c8c9e9b13ef0163d039faa6b17fc179da623f7921ea71d234f`.
  Base/CostX2/StressA/StressB × trades/equity/metrics are published as one
  same-filesystem atomic directory. Pre-rename failure creates a terminal
  no-performance incident; post-rename recovery cannot invoke the executor.
- Append-only selection state:
  `reports/m1/evidence/external_strategy_is_state/selection_state_v1.json`
  remains at selection trial count zero and OOS `false/false/0/0`. This
  runtime overlay leaves the ADR-0016 pre-runtime root, candidate freeze,
  unified protocol, DSR reference and global historical ledger byte-exact.
- Runtime trial accounting no longer requires final DSR to be rewritten into
  each old result. Base/CostX2 Sharpe sequences are derived from hash-bound
  daily-MTM equity; final DSR is recomputed once at final selection under
  ADR-0017. StressA/B never enter the DSR trial sequence.

## Validation

`bash scripts/external_strategy_original_is_validate.sh` passes 22/22 focused
tests plus normal and optimized-Python authority/trial checkers. Negative
coverage includes coordinated rehash attempts, OOS permission drift, runtime
hash drift, candidate order drift, inactive-interval state carry, missing or
forward-searched boundary rows, OOS rows, path traversal, result reuse,
partial four-scenario materialization, crash recovery, trial count/sequence
drift, invalid UTC, final-DSR rewriting, duplicate originals and failed-original
rescue.

The unified local acceptance also passes compileall, the complete 1,380-test
suite, `project_validate.sh` (17/17), the historical external-route suite
(25/25), the U-04 through U-24 archive replay (21/21), secret/no-trading/
`execution/live` scans, `git diff --check`, and the selective PR Gate against
`main@7b6a0601588f4387f8816cf6b49bdf5bf94a18f3`.

The exact offline readiness command was:

```text
python3 scripts/external_strategy_original_is_preflight.py --require-environment
```

- exit code: `2` (environment hard stop)
- stdout SHA-256:
  `09abdc57efdab17faad5373252624b56a44cf62f1c0077449a156e2178f33073`
- stderr SHA-256:
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- committed boundary snapshot count: `92`
- SSH connection attempts: `0`
- Docker/Freqtrade starts: `0`
- market/result/OOS rows decoded by preflight: `0/0/0`

## Resume condition

Resume original IS only after both `VPS_HOST` and an explicit SSH identity path
are supplied. The next candidate remains `Supertrend`; no candidate result or
selection trial exists. OOS, dry-run, API/private endpoints, paper/live,
orders, `execution/live` and M2 remain prohibited.
