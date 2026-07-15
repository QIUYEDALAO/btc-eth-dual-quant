# Next Action

## Immediate Task

Record and review the truthful U-03E `blocked_data_conflict` evidence from
PR #71 on `codex/liquid-universe-v2-requalification`. The fixed 2020-01 through 2026-06
cold and warm builds are deterministic, but checksum-verified official source
rows violate the frozen V2 contract.

Do not start U-03F. The only permitted follow-up is source-owner/public-archive
evidence work or a separate ADR that explicitly changes the data policy. Silent
deduplication, dropping negative-volume rows, changing rankings or using the V1
Markdown report as qualification input is prohibited.

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

The three blockers are official-source evidence, not ingestion failures:

- BTTUSDT 2019-01 daily ZIP contains negative base volume.
- BTTUSDT 2019-02 daily ZIP contains negative base volume.
- AXSUSDT 2026-02 monthly daily ZIP contains a duplicate 2026-02-10 row.

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

1. Preserve and merge the deterministic U-03E blocked evidence.
2. Seek official/source-owner clarification or corrected public archives for
   the exact three blockers.
3. If the project intentionally wants a different duplicate/invalid-volume
   policy, create a new ADR and rerun U-03E from scratch under a new contract
   version.

U-03F may run only after a future U-03E pass. Cross-sectional hypothesis design
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
