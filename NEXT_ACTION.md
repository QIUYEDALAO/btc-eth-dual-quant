# Next Action

## Immediate Task

PR #76 merged the generic V3 row-conflict implementation at `b3496fe`. The
fixed public cold build then verified the registered BTT/AXS source checksums,
admitted all five BTT daily corrections and collapsed the registered AXS exact
duplicate, but discovered one new unregistered official row conflict.

`KLAYUSDT` 2024-10-30 has the same zero-volume row in the official monthly and
daily 1d archives, with `close_time` earlier than `open_time`. Both archives
pass current official checksum verification. ADR-0013 therefore requires a new
independent adjudication and a versioned registry update before any V3 rerun.
Warm and worker builds were not run after the cold fail-closed stop. U-03F and
U-04 remain unauthorized.

U-04 remains unauthorized. No strategy is eligible for M2. Freqtrade
backtesting, strategies, events, returns, OOS, APIs and trading remain blocked.

## Current Decision

U-03D passed and merged in PR #70 at `5ab69e2`. U-03E then rebuilt the V2
public evidence twice with different concurrency and identical outputs:

- Artifact-set hash: `b7c89f2465f570db0687ed20f81a84d570e8746eb0be95c2767429733c0bdfb7`.
- Deterministic mismatches: 0.
- Historical symbols / months / membership rows: 676 / 78 / 1,170.
- Gap records / unresolved gaps: 227 / 0.
- Excluded-category members / synthetic fills / replacements: 0 / 0 / 0.
- Processing blockers: 3.

The adjudicated blockers are official-source evidence, not ingestion failures:

- BTTUSDT 2019-01 monthly ZIP contains one negative `base_volume`; the official
  daily ZIP and both public REST hosts agree on the positive row.
- BTTUSDT 2019-02 monthly ZIP contains four negative `base_volume` rows; the
  official daily ZIPs and both public REST hosts agree on positive rows.
- AXSUSDT 2026-02 monthly and daily ZIPs both contain two byte-identical
  2026-02-10 rows; both public REST hosts return one matching row.

The relevant files passed official checksum verification. The V2 result is
therefore `blocked`, as required by ADR-0012. V1 remains superseded historical
evidence; it cannot override the machine result.

The historical V1/V2 comparison covers all 78 months: 6 months changed, with 7
additions, 7 removals and 33 rank changes. This comparison is diagnostic only
and was not an input to V2 qualification.

M1H-03 is complete. Public funding-data qualification passed, then the one
frozen sealed-IS paper observation failed feasibility without changing the
protocol or opening OOS.

- Independent market episodes: 131.
- Projected full / sealed-OOS episodes: 187 / 56.
- Combined median 24h close displacement: 0.0714% versus 1.80% required.
- BTCUSDT / ETHUSDT median 24h close displacement: 0.0731% / 0.0132%.
- Maximum single-year episode share: 48.09% versus 45% allowed.
- Median 24h MFE: 2.3108%, disclosed as path evidence only and not a Gate override.

M1H is `failed_feasibility`; PR #65 merged the truthful stop record at
`57c2b1c`. M1H fixed rules, strategy implementation, backtesting and OOS
opening are blocked. M1E, M1G and M1H have exhausted the frozen ADR-0010
BTC/ETH two-asset candidate queue.

## Allowed Next Work

1. Merge the truthful blocked V3 qualification evidence after CI succeeds.
2. Independently adjudicate only the checksum-bound KLAYUSDT 2024-10-30
   monthly/daily row under ADR-0013 without changing rankings or outcomes.
3. If and only if a reviewed registry revision is adopted, rerun the frozen
   cold/warm/worker range from scratch. Do not run U-03F before a merged pass.

U-03E is closed as a truthful blocked milestone, not an active implementation
task. U-03F may run only after a future U-03E pass under valid source evidence.
Cross-sectional hypothesis design
requires U-03F pass plus a separate task; it is not an allowed workaround for
the current blocker.

## Prohibited

- Freqtrade-first remains the architecture for any future single-leg research.
- No strategy is eligible for M2.
- Do not enter M2.
- Do not change the M1H percentile, 365-day window, horizons, interval policy, clustering or Gates.
- Do not add a fourth BTC/ETH indicator candidate or reuse this sealed IS outcome for parameter selection.
- Do not rescue M1B, M1G or M1H through a broader symbol list.
- Do not write M1H fixed rules, strategy code, Freqtrade implementation or a backtest.
- Do not open OOS or increment the DSR opened-trial count.
- Do not access API keys, private data, private smoke, dry-run/live, orders, cancellation, matching, wallets, trading permissions or `execution/live`.
- Do not commit raw, DuckDB, Freqtrade runtime data, logs, SQLite, `.env` or private payloads.
- M2 remains blocked and no strategy is approved for trading.
