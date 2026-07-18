# Next Action

## Immediate Task

Complete an independent exact-head review of the frozen U-04 paper protocol.

- Candidate: `U04-CROSS-SECTIONAL-RESIDUAL-REVERSAL`.
- Protocol: `U04-02-CROSS-SECTIONAL-RESIDUAL-REVERSAL-PAPER-V1`.
- Protocol hash:
  `7b0e462dd9d4f51de1419005bb8701b859f4d2be6148121c1e68cdd0089629d6`.
- Design hash:
  `b384e6484180a0ec358125fbb0338d7376b860372ab065fe7043667931f178b8`.
- Hypothesis hash:
  `85e9fc11e8f6b69597fecdb6a40485611eb24163a20cea4534e81d0f08e5ec7a`.
- Qualified artifact set:
  `8784b564e8ce21c88b54045b3236021a16344998356a7a15a332188a441348c3`.

The review must bind the exact target commit, protocol bytes/content hash and
all source, membership, lifecycle and invalid-interval authorities. It must
independently examine causal timing, complete active membership, the median/MAD
estimator, dual event threshold, deterministic tie-breaking, 24h episode
clustering, next-expected-5m reference, right censoring, paper Gates, leakage
controls and authorization matrix.

Approval requires every dimension to pass and remaining critical/high findings
to equal `0 / 0`. The review must not modify the target. A passing review may
authorize only a separate data-qualification task; it may not run the protocol.

## Current Frozen Decision

- Completed 1h member log returns; exact point-in-time active cross-section.
- Common component: cross-sectional median; robust scale: `1.4826 × MAD`.
- Event: standardized residual at most `-3.0` and relative simple return at
  most `-1.80%`.
- One deterministic candidate per timestamp; global connected 24h episodes.
- Reference: first expected 5m open strictly after the completed decision.
- IS: `2020-01-01` through `2024-09-11` exclusive; OOS remains sealed through
  `2026-07-01` exclusive.
- Candidate events evaluated: no; paths/returns computed: no; OOS opened: no.

## ADR-0015 Implementation Exact-Head Review

Historical review marker: exact implementation review remains `approve` with
zero critical/high findings under review hash `9a073643...e5af1`.

## ADR-0015 Independent Policy Review

Historical review marker: policy review remains `approve` under review hash
`893d056e...85a3`; U-04 protocol work does not change policy semantics.

## U-03F Repair Exact-Head Review

Historical review marker: the former repair review and its later blocked cold
run remain immutable. ADR-0015 requalification separately quarantined 119 physical
invalid rows plus the valid-minority slot.

## Prohibited

- No strategy is eligible for M2. Do not enter M2.
- Freqtrade-first remains mandatory for any later single-leg implementation.
- Do not read or qualify public market data in the protocol review.
- Do not scan events, observe paths, calculate returns or inspect OOS.
- Do not change the target protocol, parameter, threshold, Gate or authority.
- Do not select fixed rules, implement Freqtrade strategy code or backtest.
- No API keys, dry-run/live trading, `execution/live`, order operations or M2.
- Continue local Git only; do not push, create a PR or run GitHub Actions.
