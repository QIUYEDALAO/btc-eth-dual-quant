# U-12 Outcome-Blind Recurring Calendar-Flow Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Candidate: `U12-CROSS-SECTIONAL-RECURRING-CALENDAR-FLOW-SEASONALITY`
- Protocol content hash: `a8cfc0b74e82bdf455bae5dda7a620bc5c0c53f1022d39494800f1053dd80b8a`
- OOS opened: `false`

The only calendar family is the ensuing UTC day's weekday. At each completed
UTC day boundary, each current active asset is evaluated from the preceding 52
completed occurrences of that same weekday, split chronologically 26/26. Each
historical occurrence first removes the exact then-active-member median daily
log return. A candidate needs at least 40 full and 18/18 half observations,
full median residual at least 0.60%, both half medians at least 0.30%, and a
current-active cross-sectional top-quartile full median. One deterministic
representative is retained per decision time; all events use 24h connected
clustering.

Observation begins only at the first expected 5m open strictly after the UTC
day-boundary decision. The protocol records 1/2/4/8/12/24h absolute and peer-
relative paths, MFE, MAE and recovery timing without fills, positions, equity
or formal strategy returns. The primary 24h Gates retain the 1.80% relative and
absolute medians, 60% positive relative fraction and the existing sample and
concentration standards.

Before any event or path scan, frozen-source qualification must run the same
archive/membership/lifecycle/mask/daily-assembly scope as the future observer
and prove previous-boundary closes across every month transition, all expected
5m slots, same-weekday history availability and three-order identity. It must
generate zero common-component, event, path or return rows and decode zero OOS
OHLCV values. Any mismatch stops before results.

No public data or outcome was read to select this protocol. Only exact-head
independent review is authorized next. Data qualification, events, returns,
strategy, backtesting, OOS, API/trading, `execution/live` and M2 remain false.
