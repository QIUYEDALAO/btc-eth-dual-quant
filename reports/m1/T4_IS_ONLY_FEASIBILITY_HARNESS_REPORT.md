# T4 IS-Only Feasibility Harness Report

- Status: pass
- Generated UTC: 2026-07-10T16:10:08+00:00
- Scope: reusable IS-only event feasibility tooling foundation
- Candidate evaluated: no
- Candidate events selected: no
- Candidate returns computed: no
- OOS returns accessed: no
- Strategy code implemented: no
- API key used: no
- Live/paper/execution implemented: no

## Trial-Ledger Lock

- Candidate identity checked: `M1D-15M-DISCRETE-DISLOCATION`
- Hypothesis SHA256: `fdccf79b213f87fc9ee1cb74daf42f67e7ba63fba6de9990851c2eec9e11e1a7`
- Ledger status required: `declared_unopened`
- `oos_opened` required: `false`
- A changed hypothesis, wrong hash, duplicate ID, or opened OOS is rejected before analysis.

## Fixed Observation Semantics

- Caller supplies preregistered event timestamps; the harness does not detect events or generate signals.
- Event evidence is a completed 15m bar; observation entry is the next contiguous 15m open.
- Fixed horizons: `1,2,4,8,12,24` completed 15m bars.
- Horizon return uses the corresponding completed bar close.
- Missing, duplicate, unordered, off-grid, same-bar, or cross-IS observations are rejected or right-censored.

## Fixed Cost Scenarios

| Scenario | Per-side cost | Round-trip approximation |
|---|---:|---:|
| base | 0.15% | 0.30% |
| cost_x2 | 0.30% | 0.60% |
| event_stress_a | 0.40% | 0.80% |
| event_stress_b | 0.55% | 1.10% |

Net return is `(exit * (1 - cost)) / (entry * (1 + cost)) - 1`; callers cannot override the four scenarios.

## Diagnostic Coverage

- Horizon sample count, mean, median, win rate, sample standard deviation, P5/P95, and Cost x2 net margin.
- MAE, MFE, worst observed path, 24-hour connected clusters, and rolling 24-hour/7-day/30-day event counts.
- Monthly/annualizable frequency inputs, interval-union occupancy, overlap count, concurrency, and longest sleep.
- Full/OOS sample projections use only IS event rate and calendar length; no OOS prices or returns are accepted by the API.

## Local Golden Structure Smoke

| Symbol | 15m rows | First open ms | Last open ms | Canonical SHA256 |
|---|---:|---:|---:|---|
| BTCUSDT | 96384 | 1696118400000 | 1782863100000 | `a0971abb14ba977686704543e7357da28d23b09ebe20316b814b7ef97bb03525` |
| ETHUSDT | 96384 | 1696118400000 | 1782863100000 | `18e93883c777df65c9bf4c8a88b17a3778fe0a5f901fdf1da2c2ceb893e632b7` |

The smoke reads ignored T2 golden 15m files only to validate ordering, continuity, OHLC legality, row count, and deterministic hash. Detailed evidence remains under ignored `storage/logs/`.

## Calendar Sample Budget

| Item | Value | Gate |
|---|---:|---|
| Formal full-history days | 1004 | diagnostic |
| IS days (first 70%) | 702 | diagnostic |
| Sealed OOS days (last 30%) | 302 | fail |
| Required OOS days | 540 | fixed |
| OOS calendar shortage | 238 | blocked |
| Required full-history days at 30% OOS | 1800 | fixed |
| Earliest projected full-history end | 2028-09-03 | informational |

T4 can pass as tooling foundation, but the current T5 OOS calendar gate necessarily fails. T5 must run the sample-budget precheck first and stop without lowering the 540-day requirement.

## Gate

| Check | Status |
|---|---|
| Trial-ledger identity and SHA256 locked | pass |
| OOS remains unopened | pass |
| Next-open and right-censor semantics implemented | pass |
| Fixed horizons and fixed costs implemented | pass |
| Frequency, clustering, path-risk, occupancy, and budget diagnostics implemented | pass |
| Local T2 golden 15m structural smoke | pass |
| Candidate evaluated | no |
| Current 540-day OOS calendar requirement | fail |

- T4 harness foundation: pass
- T5 precheck authorized after T4 merge: yes
- T5 calendar gate currently pass: no
- M1D feasibility authorized: no; T5 sample-budget precheck must run first
- M1D strategy code authorized: no
- M2 authorized: no

T4 passing does not establish candidate feasibility, strategy profitability, or M2 eligibility.
