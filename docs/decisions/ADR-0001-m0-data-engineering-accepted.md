# ADR-0001 M0 Data Engineering Accepted

- Status: Accepted
- Date: 2026-07-09

## Context

M0 implemented read-only data engineering for BTC/ETH public and sanitized
private-smoke status. It explicitly excluded execution/live, order placement,
cancel order, simulated matching, and trading-permission API calls.

## Decision

M0 data engineering is accepted. The acceptance record is
`reports/m0/M0_FINAL_ACCEPTANCE.md`, with tag
`m0-data-run-accepted-v0.1.4`.

## Consequences

- Future work may use M0 data and reports as validation inputs.
- Future stages must preserve append-only raw-data rules and read-only safety.
- M1 work remains offline validation only unless a later explicit stage changes it.

## Prohibited Misinterpretations

- M0 acceptance does not approve live trading.
- M0 acceptance does not approve paper trading with real API.
- M0 acceptance does not approve execution/live modules.
- M0 acceptance does not approve order placement, cancellation, or trading permissions.
