# Freqtrade-First BTC/ETH End-to-End Implementation Plan

## Execution Policy

Execute stages sequentially. Each stage uses its own branch and PR, updates all
project context files, passes local validation and GitHub checks, and is merged
before the next stage begins. P5-P8 remain blocked.

## P0 Governance

Branch: `codex/strategy-failure-diagnostics`, PR #14.

1. Add the master roadmap, this implementation plan, and
   `PROJECT_EXECUTION_CHECKLIST.md`.
2. Link the roadmap from project state, ledger, next action, report index, and
   agent instructions.
3. Rename PR #14 to include the end-to-end roadmap.
4. Run project validation, push, wait for all checks, and squash merge.

Exit: context and checklist agree, the worktree is clean, and PR #14 is merged.

## P1 M1C Design

Branch: `codex/m1c-btc-eth-rotation-design`.

1. Write the decision-complete M1C strategy specification from the fixed
   rules in the roadmap.
2. Verify from pinned Freqtrade interfaces that informative-pair ranking,
   maximum-one-position behavior, 50% stake, and exit-before-entry rotation
   are expressible.
3. Add fixture-level capability tests without implementing the strategy.
4. Record `design_pass` or `blocked_framework_capability`.
5. Validate, create PR, wait for checks, and merge only on `design_pass`.

Exit: no strategy rule or Freqtrade behavior is left undecided.

## P2 Freqtrade Implementation

Branch: `codex/m1c-btc-eth-rotation-validation`.

1. Add `BTCETHRelativeStrengthRotation` under the Freqtrade strategy tree.
2. Add a public research config with no credentials and no trade command.
3. Add download, list-data, base backtest, cost-x2 backtest,
   lookahead-analysis, and recursive-analysis entrypoints through the existing
   guarded research wrapper.
4. Add Python time-semantics audit helpers only; do not calculate a second
   complete strategy equity curve.
5. Add unit tests for indicators, weekly decision timing, cross-pair ranking,
   tie behavior, cash state, single-position constraint, stake cap, emergency
   stop, and rotation ordering.

Exit: behavior tests and all repository validation pass; no numerical strategy
approval is claimed.

## P3 Historical Validation

Continue on the P2 validation branch and PR unless code changes are required
after review; otherwise open a dedicated report-only branch.

1. Download public BTC/ETH daily spot data through Freqtrade.
2. Generate M0/Freqtrade provenance for the exact used range.
3. Run base and cost-x2 full-period backtests.
4. Run sealed final-30% OOS backtests and four chronological robustness
   segments on the first 70%.
5. Run lookahead and recursive analyses.
6. Export trades and generate
   `reports/m1/M1C_BTC_ETH_ROTATION_BACKTEST_REPORT.md` with complete trades,
   yearly results, IS/OOS, costs, delete-best-three, segment results, and every
   gate.
7. Set final status to `failed_validation` if any gate fails; otherwise set
   `under_review`.

Exit: truthful numerical report committed without raw Freqtrade runtime data.

## P4 Independent Audit

Branch: `codex/m1c-independent-audit`.

1. Validate the exported Freqtrade trade schema and data provenance.
2. Independently recompute signal availability, next-open fills, UTC ranking,
   fees, and per-trade PnL from fixtures and ignored local artifacts.
3. Compare exact timestamps and enforce absolute numerical error `<= 1e-8`.
4. Generate `reports/m1/M1C_INDEPENDENT_AUDIT_REPORT.md`.
5. Combine numerical and M0 audit gates into the final M1C research status.

Exit: `failed_validation`, `passed_numerical_data_audit_blocked`, or
`under_review`; never automatic M2 approval.

## P5-P8 Deferred Tasks

- P5: M2 risk/monitoring/kill-switch ADR.
- P6: separately approved 90-day Freqtrade dry-run.
- P7: separately approved limited-capital automation.
- P8: operations, drift monitoring, incident rollback, and scaling.

All remain `blocked_not_authorized` until a future explicit approval.

## Required Validation Per PR

```bash
bash scripts/project_validate.sh
git diff --check
git status
```

Also run the phase-specific validator, secret scan, no-trading scan,
execution/live scan, and tracked-artifact scan. Do not commit `.env`, keys,
raw data, DuckDB, logs, sqlite, backtest result archives, or private reports.
