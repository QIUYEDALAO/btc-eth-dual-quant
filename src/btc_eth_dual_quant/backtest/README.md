# Offline Validation Modules

The self-managed M1A trend engine in this package is deprecated and frozen as
a historical failed-validation reproduction. New single-leg strategy logic,
data downloads, backtests, and research diagnostics belong in
`freqtrade_lab/user_data/strategies/` and the pinned Freqtrade runtime.

Python remains active here only for strict event-time/lookahead validation and
offline spot-long plus perpetual-short accounting that Freqtrade cannot model
as one native portfolio. These modules must never become paper/live execution,
order routing, simulated matching, or `execution/live`.
