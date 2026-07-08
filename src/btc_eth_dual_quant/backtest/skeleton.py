"""Minimal M0 backtest skeleton for time-semantics checks.

This is not an execution engine. It only encodes the rule that a decision made
after bar N may be scheduled no earlier than bar N+1 open.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketBar:
    open_time_ms: int
    close_time_ms: int
    open: str
    high: str
    low: str
    close: str


@dataclass(frozen=True)
class ScheduledDecision:
    decision_time_ms: int
    earliest_effective_time_ms: int
    reason: str


class LookaheadBiasError(ValueError):
    pass


def assert_feature_available(feature_time_ms: int, decision_time_ms: int) -> None:
    if feature_time_ms > decision_time_ms:
        raise LookaheadBiasError(
            f"feature timestamp {feature_time_ms} is after decision timestamp {decision_time_ms}"
        )


def schedule_next_open(bars: list[MarketBar], decision_bar_index: int, reason: str) -> ScheduledDecision:
    if decision_bar_index < 0 or decision_bar_index >= len(bars):
        raise IndexError("decision_bar_index out of range")
    next_index = decision_bar_index + 1
    if next_index >= len(bars):
        raise LookaheadBiasError("cannot schedule a decision on the final bar without a next open")
    decision_bar = bars[decision_bar_index]
    next_bar = bars[next_index]
    if next_bar.open_time_ms <= decision_bar.close_time_ms:
        raise LookaheadBiasError("next bar open must be after current bar close")
    return ScheduledDecision(
        decision_time_ms=decision_bar.close_time_ms,
        earliest_effective_time_ms=next_bar.open_time_ms,
        reason=reason,
    )
