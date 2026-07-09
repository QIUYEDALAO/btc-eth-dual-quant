# M1A Revalidation Notice

- Evidence status: superseded_pending_revalidation
- Strategy decision: failed_validation remains active
- Trading approval: none

The historical M1A report is retained unchanged for audit history. Code review
identified that the equal-weight portfolio aligned component equity curves by
list position rather than UTC timestamp, and the delete-best-three stress
deducted removed profit before the affected trades occurred.

Those numerical claims must not be used for a future strategy approval. The
M1A `failed_validation` decision remains valid because the independent OOS
Sharpe and combined trade-count gates also failed. The self-managed M1A engine
is frozen and no longer serves as the primary single-leg backtest engine.

No result here approves M2, paper trading, live trading, or API trading
permissions.
