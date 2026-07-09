# Project Execution Checklist

This is the canonical task-status view for the Freqtrade-first BTC/ETH system.
Statuses are `pending`, `in_progress`, `completed`, `blocked`, or
`not_authorized`.

| Task ID | Phase | Status | Dependency | Branch / PR | Output | Acceptance gate | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0-01 | P0 governance | completed | none | `codex/strategy-failure-diagnostics` / #14 | End-to-end roadmap spec | Approved plan recorded | none |
| P0-02 | P0 governance | completed | P0-01 | `codex/strategy-failure-diagnostics` / #14 | Implementation plan | P0-P8 dependencies and rollback fixed | none |
| P0-03 | P0 governance | completed | P0-02 | `codex/strategy-failure-diagnostics` / #14 | This checklist | Required columns and statuses present | none |
| P0-04 | P0 governance | completed | P0-03 | `codex/strategy-failure-diagnostics` / #14 | Five context files updated | Context check pass | none |
| P0-05 | P0 governance | completed | P0-04 | `codex/strategy-failure-diagnostics` / #14 | Merged governance PR | Local and GitHub checks pass | none |
| P1-01 | P1 design | completed | P0-05 | `codex/m1c-btc-eth-rotation-design` | Fixed M1C specification and machine-readable contract | No ambiguous rule or parameter | none |
| P1-02 | P1 design | completed | P1-01 | same P1 PR | Pinned Freqtrade capability evidence | Unique winner and rotation ordering proven | P2 runtime fixture still required |
| P1-03 | P1 design | in_progress | P1-02 | same P1 PR | Design decision | `design_pass` plus PR/CI review required | P1 PR not merged |
| P2-01 | P2 implementation | pending | P1-03 | `codex/m1c-btc-eth-rotation-validation` | Freqtrade strategy and public config | Behavior tests pass | P1 not passed |
| P2-02 | P2 implementation | pending | P2-01 | same P2 PR | Guarded research commands | No trade/live command | P2 not started |
| P2-03 | P2 implementation | pending | P2-02 | same P2 PR | Time-semantics tests | Next-open and UTC ranking pass | P2 not started |
| P3-01 | P3 validation | pending | P2-03 | P2 PR or report branch | Public Freqtrade data and provenance | Exact used range has no unexplained gap | P2 not passed |
| P3-02 | P3 validation | pending | P3-01 | same validation PR | Base/cost-x2, OOS, segment results | Every fixed numerical gate evaluated | P3 not started |
| P3-03 | P3 validation | pending | P3-02 | same validation PR | M1C backtest report | Truthful `under_review` or `failed_validation` | P3 not started |
| P4-01 | P4 audit | pending | P3-03 | `codex/m1c-independent-audit` | Independent timing and PnL audit | Timestamp exact, error <= 1e-8 | P3 not complete |
| P4-02 | P4 audit | pending | P4-01 | same P4 PR | Final M1C research status | M0 and numerical gates combined | P4 not started |
| P5-01 | P5 M2 design | not_authorized | P4-02 plus explicit approval | future branch | M2 ADR | Separate approval | M2 prohibited |
| P6-01 | P6 dry-run | not_authorized | P5-01 plus explicit approval | future branch | 90-day dry-run report | 12 weekly decisions and no live orders | dry-run prohibited |
| P7-01 | P7 limited live | not_authorized | P6-01 plus explicit approval | future branch | Limited-capital acceptance | Hard risk controls and separate approval | live prohibited |
| P8-01 | P8 operations | not_authorized | P7-01 | future branch | Operations and scaling loop | Continuous audit | live prohibited |

## Current Gate

- Authorized work: P0-P4.
- Active task: P1-03.
- M1A status: `failed_validation`.
- M1B status: `failed_validation`.
- M0 audit status: `audit_revalidation_required`.
- M2 status: blocked.
- Trading approval: none.
