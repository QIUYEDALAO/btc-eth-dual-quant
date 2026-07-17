# Next Action

## Immediate Task

PR #107 independently approved the exact ADR-0015 Draft head with zero
critical/high findings and merged unchanged at
`1573abf2bef7d02df6c3b0624ee25cd3557ff2c6`. Its exact review head is
`f3cf2131798f8bf3bd319b21480dca196517f3fe`, and review content hash is
`893d056ec07ebc0697521a96a1533cb43265ebc2fa9484862fcdf39d8c5285a3`.

The immediate task is the separate `ADR-0015-ADOPT` governance stage. It binds
the exact Draft, review, protocol, diagnostic, run-manifest and source-freeze
identities under adoption content hash
`d9b220657d3867941f4f42fd112339c4058e7bc734aa9db72a5b7f81ac78fc19`.
The reviewed policy semantic body hash is
`c3d5f605ec26161f1bedc6961ac6f326d00582f9c3dcaa9de68c226961a34149`.

The Draft binds PR #102's frozen protocol and PR #103's exact diagnostic
evidence. It proposes a generic new policy family only for hash-bound official
5m active-member rows whose open time is grid aligned, whose non-time fields
all pass, and whose sole defect is the close boundary. A candidate requires at
least two invalid active members and at least 80% of the active membership at
one open time.

The underlying immutable diagnostic remains exactly 119 physical invalid rows
in eight synchronous windows; this Draft neither rewrites nor reclassifies
those historical source rows.

An accepted policy event quarantines the full active-member slot,
including any valid minority, while preserving every physical source row
unchanged. Off-grid rows, other malformed fields, missing/duplicate/non-member
rows, authority ambiguity and any source/hash/order drift remain hard blockers.
No date/symbol exception registry, raw repair, source replacement, fill,
substitute member or direct V2 gap-policy reuse is permitted.

## ADR-0015 Conditional Adoption

The adoption authorizes only the next generic policy implementation, synthetic
fixtures, fault injection and a later exact-head independent implementation
review. The implementation must not run public data. Fixed-range
requalification, a new audit protocol, a new audit, U-04, strategy/OOS,
API/trading and M2 remain unauthorized.

The adoption PR must preserve the exact reviewed policy semantics and the
unchanged all-false docs-only Draft model. Any target, model, evidence,
authorization or dependency drift fails closed.

## ADR-0015 Independent Policy Review

PR #107 merged the exact-head independent review with verdict `approve`, zero
critical findings and zero high findings. That review remains frozen historical
evidence: approval alone did not adopt the policy, and its exact bindings are
prerequisites for this separate conditional adoption.

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

1. Preserve PR #89, PR #95 and PR #100 evidence and the frozen source byte for
   byte; none is an alternative active qualification authority.
2. Validate and merge only the ADR-0015 conditional-adoption governance PR
   after its exact semantic/evidence bindings, repository validation and
   selective CI pass.
3. After adoption merge, start only a separate generic policy implementation
   using synthetic fixtures and fault injection; run no public data.
4. Require an exact-head independent implementation review before any
   fixed-range public requalification. Keep audit, U-04, hypothesis/strategy,
   returns, OOS and M2 blocked.

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

## U-03F Repair Exact-Head Review

PR #98 exact head `27e6436c0a4b00ca7c8055bc763d533fcbcc9743`
passed 110/110 checks and remained unchanged through merge. PR #99 independently
approved it with zero remaining critical/high findings and passed 112/112 checks
after rebasing onto the implementation merge. Both PRs are merged.

That approval authorized only the fixed repair requalification. PR #100 merged
its truthful cold-blocked evidence after 114/114 checks. The resulting 119
source-row errors terminate and close the chain before a new audit. U-04 and all
downstream work remain unauthorized.
