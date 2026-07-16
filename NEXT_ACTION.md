# Next Action

## Immediate Task

The U-03F V4 repair and requalification protocol is frozen on
`codex/u03f-v4-repair-requalification-protocol`, based on GitHub main
`513d321b69750d6c8bb47bddbf006d4caac04828`. Its machine content hash is
`9b771317d8257b397addefc262a1ffd48ded57ec1d79542372fe3c95cf8180c1`.
No production repair or public rerun has occurred.

The protocol maps the merged one critical and seven high findings into three
repair requirements and six mandatory fault tests. It freezes integer-only UTC
conversion, exact 5m open/close interval validation, propagation through grid,
source, panel, summary and diff artifacts, and atomic qualification-report/run-
manifest binding. It also freezes the exact-head review, fixed `2020-01`
through `2026-06` requalification and new 15/15 independent-audit Gates.

The immediate Gate is local validation, PR review and CI merge for the protocol
only. Production implementation must not begin before protocol merge. Any
historical evidence hash drift, source-freeze drift, Gate reduction or
authorization expansion stops the chain.

V4 remains `audit_blocked` / `revalidation_required`; U-04 remains
unauthorized.

## Historical Failed Audit

U-03F is closed as `failed_audit`. PR #95 merged the truthful evidence at
`36b81649fbdaf4f54aea7027f3e9325b0ea80de0` after 106/106 GitHub Actions
passed. The green checks prove evidence self-consistency; they do not change the
audit verdict.

Only 10 of 15 production manifests match exactly. The expected-grid, source,
qualified-panel, qualification-summary and V3/V4-diff artifacts differ. The
first minimal grid counterexample is ADAUSDT 2020-02 (`8270` production rows
versus `8269` independently valid rows). The independent parser rejects invalid
5m interval boundaries that the production authority path does not validate.
The production qualification-report hash recorded in the run manifest also
differs from the committed report hash.

V4 is now `audit_blocked` and `revalidation_required`. Its prior deterministic
public requalification remains immutable historical evidence, but it is no
longer research-admission authority. U-04 remains unauthorized.

The next task, if separately started, may only repair the independently found
integer-time, 5m row-validity and report-binding defects, then repeat fixed-range
requalification and independent audit. This closeout does not implement that
repair.

The audit-result PR may prove evidence self-consistency in CI even though the
audit verdict is failure. A green CI result must not be described as a V4 audit
pass.

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

1. Merge the frozen repair/requalification protocol after every local and
   GitHub check passes.
2. Implement only the frozen repair, then require exact-head independent
   approval with zero critical/high findings before merge.
3. Repeat the fixed-range public requalification and a new independent audit
   without lowering any Gate.
4. Preserve V1/V2/V3/V4 prior runs as historical evidence; none is an alternative active
   qualification authority.
5. Keep U-04, hypothesis/strategy work, returns, OOS and M2 blocked.

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
