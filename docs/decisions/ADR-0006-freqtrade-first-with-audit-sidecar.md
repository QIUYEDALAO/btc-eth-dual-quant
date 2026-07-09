# ADR-0006 Freqtrade-First With Audit Sidecar

- Status: Accepted
- Date: 2026-07-10

## Context

The repository currently contains both self-managed offline backtest engines
and a Freqtrade feasibility lab. Maintaining two complete single-leg strategy
and backtest stacks creates duplicated behavior and conflicting metric risk.
The M1B review also confirmed that Freqtrade does not natively represent one
coordinated spot-long plus perpetual-short portfolio.

## Decision

Freqtrade is the primary framework for single-leg strategy research, public
data download, backtesting, WebUI, and any future separately approved
automation.

Python remains responsible only for:

- M0 data registry, lineage, immutable archive, query, and quality evidence;
- independent event-time and lookahead validation;
- offline spot-long plus perpetual-short portfolio accounting that Freqtrade
  cannot natively provide.

The existing self-managed M1A engine is frozen as a historical reproduction
artifact. Two-leg automation remains prohibited unless a future decision
explicitly approves an external coordinator design and a later execution phase.

## Consequences

- M0 remains the data audit authority; Freqtrade data is reproducible cache.
- New single-leg strategies are implemented only in Freqtrade.
- Historical M1A/M1B reports are preserved, with superseding notices for
  methodology defects.
- The Freqtrade image is pinned by release and digest.
- No strategy is eligible for M2 as a result of this architecture decision.

## Prohibited Interpretations

- Freqtrade feasibility does not approve a strategy.
- A Freqtrade strategy result does not approve M2 or live trading.
- Two independent Freqtrade bots do not provide atomic two-leg coordination.
- Offline two-leg accounting must not become execution, paper trading, or a
  simulated matching engine.
