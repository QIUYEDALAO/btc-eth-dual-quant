# Next Action

## Immediate Task

The fixture-only U-03F independent auditor is implemented on
`codex/u03f-v4-independent-auditor`. It imports no production builder and has
not run the full public audit. Freeze its exact head and obtain a separate
independent implementation review from the protocol-merged main. Do not merge
the implementation before an `approve` verdict with zero critical/high.

The checker identifies six float-timestamp candidates in the production V4
authority path. They are not repaired here and must be adjudicated by the real
audit's frozen integer-time Gate. U-04 remains unauthorized.

The U-03F independent-audit protocol is frozen before results on
`codex/u03f-v4-independent-audit-protocol`. It binds main `1b602649...`, the
fixed V4 source and machine evidence, all 15 manifest identities, exact and
semantic comparison Gates, and a completely false downstream authorization
matrix. The protocol must pass review and merge before any auditor code or
full audit run starts.

After protocol merge, the only permitted work is the fixture-only independent
auditor implementation described by the frozen protocol. The real `2020-01`
through `2026-06` audit remains unauthorized until that implementation receives
an independent exact-head approval and merges. U-04 remains separately gated.

The fixed `2020-01` through `2026-06` V4 public requalification passed and
merged in PR #89 at `77cb0969980978e65f3560f38f50924c73dfee6e`.
V4 is now the active liquid-universe qualification authority.

The only authorized next task is U-03F: an independent audit of the merged V4
machine evidence. U-03F is authorized but not started. Do not begin it from
this governance-closeout branch.

- Source freeze: `c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c`.
- Cold/warm/worker artifact set: `4cfca060b423f4071c831c9ce52556a3a66837fb7326f689245253e13165fde6`.
- Run manifest: `f55f2829be39445a8489a0863ee5e013c481351d64797251bd79bc199376b127`.
- Result: 78 months and 1,170 membership rows; all blocking counters are zero.

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

1. Create a separate U-03F independent-audit task from the closeout-merged main.
2. Audit membership, lifecycle availability, expected grid, gaps, quarantine,
   active-universe and qualified-panel evidence without changing V4 artifacts.
3. Preserve V1/V2/V3 as historical evidence; V3 remains blocked and is not an
   alternative qualification authority.
4. Keep U-04, hypothesis/strategy work, returns, OOS and M2 blocked unless
   U-03F independently passes and a later separate task authorizes U-04.

U-03E V2 and V3 remain truthful blocked historical milestones. V4 supersedes
their admission authority through a separately adopted lifecycle policy and
the merged deterministic public requalification. Cross-sectional hypothesis
design still requires U-03F pass plus a separate task.

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
