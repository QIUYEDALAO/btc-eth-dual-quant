# BTC/ETH Short-Horizon Event Quant Implementation Plan

## Execution Policy

Execute one task group per branch/PR. Update all context files in every PR.
Never begin a dependent group before the predecessor is merged and passed.
No group authorizes M2, dry-run, live, credentials, or order behavior.

## T0 Governance and Expert Evidence

Branch: `codex/short-horizon-product-governance`.

1. Commit the approved product specification and ADR-0007.
2. Commit the expert report, deterministic recompute, and daily-equity CSV.
3. Run the expert script in an isolated directory and require byte-identical CSV.
4. Add the immutable candidate trial ledger, evidence hashes, and an automated
   validator that rejects stale hashes, duplicate candidate IDs, or disabled
   governance rules.
5. Update project state, ledger, next action, report index, agent rules, and the
   canonical execution checklist.
6. Run project validation, secret/no-trading scans, push, open a PR, and merge
   only after every check passes.

Exit: approved governance is on main; no strategy or raw data is added.

## T1 Canonical Public Minute Data

1. Extend public spot ZIP acquisition for BTCUSDT and ETHUSDT 1m history.
2. Keep monthly ZIP as base, daily ZIP as omission supplement, and REST as
   deterministic sample evidence only.
3. Persist append-only source envelopes and manifests under ignored storage.
4. Calculate completeness, contiguous gaps, source hashes, and spread-proxy
   eligibility by month.
5. Freeze the liquidity-qualified research start before any strategy return.

Exit: exact range and start date are recorded; no unexplained relevant gap.

## T2 Golden Data and Quarantine

1. Produce golden 1m rows and a separate conflict/quarantine table.
2. Classify `audit_complete`, `audit_complete_with_quarantine`,
   `pending_archive`, or `blocked` per symbol/month.
3. Derive deterministic 5m and 15m rows from golden 1m.
4. Compare derived 15m rows with official 15m ZIP row by row.
5. Export Freqtrade-compatible ignored caches and provenance manifests.

Exit: derivation and official-source evidence are reproducible by hash.

## T3 Unified MTM and Policy Benchmark

1. Generalize the expert recompute to consume Freqtrade trade exports and golden
   prices instead of embedded M1C records.
2. Build strategy and policy-benchmark daily-MTM equity curves.
3. Implement Sharpe, MaxDD, Sortino, Calmar, PSR, DSR, cost attribution,
   frequency, turnover, concentration, and granularity comparisons.
4. Preserve Freqtrade summary metrics as clearly labeled diagnostics only.
5. Reproduce the expert M1C Base/Cost x2 outputs as regression fixtures.

Exit: deterministic fixtures and M1C regression pass.

## T4 Trial Ledger and Feasibility Harness

1. Validate exact hypothesis text/hash before analysis.
2. Provide IS-only event studies at 1/2/4/8/12/24 15m horizons.
3. Report frequency, clustering, edge after four cost scenarios, adverse path,
   duration, capital occupancy, and projected sample budget.
4. Never expose OOS returns or select parameters from OOS.

Exit: a reusable diagnostic harness exists; no strategy approval is claimed.

## T5 M1D IS-Only Feasibility

1. Run the registered discrete-dislocation hypothesis on IS only.
2. Evaluate the paper feasibility Gates without creating a Freqtrade strategy.
3. Publish `M1D_SHORT_HORIZON_FEASIBILITY_REPORT.md`.
4. On any failure, record `rejected_at_feasibility_stage` and stop M1D.

Exit: all paper Gates pass, or truthful rejection is merged.

## T6 Fixed M1D Design

1. Freeze event, target, expiry, risk stop, position size, conflicts, costs,
   time ranges, OOS boundary, stress periods, and all numerical Gates.
2. Store one machine-readable contract and its SHA-256.
3. Verify the pinned Freqtrade interface can express all rules deterministically.

Exit: no TBD, optional parameter, or OOS selection path remains.

## T7 Freqtrade Implementation

1. Implement only in the Freqtrade strategy directory.
2. Add credential-free download, list-data, backtest, lookahead, and recursive
   research commands for 15m with 1m/5m detail.
3. Add independent timestamp checks, not a second return engine.
4. Add static, fixture, no-live, secret, and tracked-artifact tests.

Exit: behavior and time semantics pass; no performance approval is claimed.

## T8 Formal Historical Validation

1. Run full and sealed final-30% OOS under Base and Cost x2.
2. Report Event Stress A/B without hiding negative results.
3. Run 15m coarse, 5m detail, and authoritative 1m detail.
4. Run golden and conflict-alternative data versions.
5. Generate strategy/benchmark MTM, PSR/DSR, concentration, pressure, cost,
   frequency, and complete Gate matrices.
6. Execute full minute runs locally or on the VPS; CI runs fixtures only.

Exit: any failed Gate is `failed_validation`; all-pass is only `under_review`.

## T9 Independent Audit

1. Recompute signal availability, next-open fills, detail-path exits, fees,
   equity, benchmark, and decision metrics.
2. Verify timestamp identity and numerical tolerances.
3. Verify data-variant and granularity Gate invariance.
4. Publish the independent audit and final research status.

Exit: evidence agrees. M2 still requires a future explicit ADR and approval.

## Required Validation Per PR

```bash
bash scripts/project_validate.sh
git diff --check
git status
```

Also run the phase validator, secret/no-trading scan, execution/live scan, and
tracked-artifact scan. Never commit `.env`, credentials, raw data, DuckDB,
Freqtrade caches/results, logs, sqlite, or private payloads.
