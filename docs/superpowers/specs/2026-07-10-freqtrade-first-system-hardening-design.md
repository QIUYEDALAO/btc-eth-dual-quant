# Freqtrade-First System Hardening Design

## Status

- Decision: approved
- Phase: post-M1B architecture hardening
- Trading approval: none

## Objective

Make Freqtrade the single framework for single-leg strategy research, public
data download, backtesting, WebUI, and any future separately approved
automation. Keep Python only for M0 data governance, independent event-time
validation, and offline accounting that Freqtrade cannot natively provide for a
spot-long plus perpetual-short portfolio.

This design does not approve M2, live trading, paper trading with real API
credentials, order placement, cancellation, simulated matching, or
`execution/live`.

## Ownership Boundaries

| Capability | Owner |
| --- | --- |
| Single-leg strategy implementation | Freqtrade |
| Public research-data download and cache | Freqtrade |
| Single-leg backtesting and WebUI | Freqtrade |
| Canonical data lineage and quality evidence | M0 Python |
| Append-only raw archive and DuckDB query layer | M0 Python |
| Lookahead and next-open semantic assertions | Independent Python verifier |
| Spot-long plus perpetual-short accounting | Offline Python research module |
| Two-leg automated execution | Prohibited in this phase |

M0 data is the audit authority. Freqtrade runtime data is reproducible cache and
must remain ignored by git. A strategy result may use Freqtrade data only when a
sanitized provenance record ties its symbol, timeframe, time range, row count,
hash, and gap status back to an M0-audited source range.

## Freqtrade Contract

- Pin the official image to release `2026.6` and an immutable image digest.
- Record the resolved version and digest without server or credential data.
- Allowed research commands are `download-data`, `list-data`, `backtesting`,
  `lookahead-analysis`, `recursive-analysis`, `show-config`, and `webserver`.
- Do not provide a repository command for the Freqtrade trading runner.
- Keep WebUI bound to `127.0.0.1`.
- Freeze the existing M1A strategy and self-managed M1A engine as historical
  failed-validation reproduction artifacts. New single-leg strategies belong
  only in the Freqtrade strategy directory.

## M0 Audit Corrections

Funding interval candidates must represent complete settlement periods. A
single `premiumIndex` snapshot contains only the time remaining until the next
settlement and cannot establish a period. Full-period inference order is:

1. `fundingInfo.fundingIntervalHours`;
2. cadence across multiple `premiumIndex.nextFundingTime` values, or a bounded
   next-funding timestamp paired with a historical settlement;
3. adjacent historical `fundingRate.fundingTime` values.

Conflicts use the shorter valid full-period candidate and emit a warning.
Historical events retain their own inferred interval instead of sharing one
global mode.

ZIP/REST comparison is required for every enabled K-line family. The audit
sample covers the first available segment, a middle segment, the most recent
complete month, and every flagged anomaly. A missing comparison blocks the M0
audit gate unless a documented upstream-retention limitation makes overlap
impossible.

## M1B Event-Time Contract

Funding information at settlement time `T` becomes available at `T`. An entry
decision may fill only at the first 1-hour bar open strictly after `T`; the
funding payment at `T` is not earned. If already held at `T`, that settlement is
included before an exit decision fills at the first later 1-hour open.

Valuation may use only bars with `close_time <= valuation_time`. Funding income
is `short_contract_quantity * settlement_mark_price * funding_rate`, with the
short receiving positive funding. Entry and exit fees use actual leg notionals,
and slippage is applied to all four leg fills. A position without a legal final
exit is incomplete and does not count toward the complete-cycle gate.

The OOS split remains time based. Carry-in positions are reported separately
and do not count as OOS complete cycles. Existing thresholds, cost stress, and
failed-validation decisions are not relaxed.

## Evidence Policy

Historical reports remain immutable. When a methodology defect is found, add a
superseding notice and a new revalidation report. The old M1A and M1B strategy
decisions remain `failed_validation`, while affected numerical claims are not
eligible for future approval decisions.

M0 remains accepted as read-only infrastructure, with audit status
`revalidation_required` until the funding-interval and ZIP/REST corrections
pass. No existing acceptance is interpreted as trading approval.

## Delivery Sequence

1. Architecture governance and evidence notices.
2. M0 audit correctness hardening.
3. Freqtrade primary-framework pinning and provenance.
4. M1B event-time revalidation.

Each delivery uses an independent branch and PR, updates project context files,
passes its local and GitHub validations, and introduces no private or runtime
artifacts.
