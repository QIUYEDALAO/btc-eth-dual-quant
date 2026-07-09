# M1B Revalidation Notice

- Evidence status: invalidated_pending_event_time_revalidation
- Strategy decision: failed_validation remains active
- Trading approval: none

The historical M1B numerical report is retained unchanged for audit history.
Code review found that funding-settlement decisions could use the close of a
1-day bar that had not closed at the settlement timestamp. The entry-triggering
funding event was also included as income even though the modeled position did
not exist before that settlement.

Historical total return, Sharpe, OOS Sharpe, drawdown, cycle PnL, and the
`No lookahead: pass` claim are invalid for future approval decisions until a
1-hour event-time revalidation is completed. The existing M1B
`failed_validation` decision remains active and cannot be upgraded by this
notice.

No result here approves M2, paper trading, live trading, two-leg execution, or
API trading permissions.
