# M1H Execution Representability Review

- Status: constraint_pass_no_exit_selected
- Scope: pre-implementation representability constraints only
- Exit family selected: no
- Freqtrade remains single-leg return authority: yes
- External single-leg strategy engine authorized: no
- Same-bar ambiguity dependency allowed: no
- Optimistic gap dependency allowed: no
- Zero-mismatch fixture required before implementation: yes
- Strategy code authorized: no
- Backtest executed: no
- OOS opened: no

## Constraint

M1G demonstrated that a plausible Freqtrade lifecycle can diverge from a
conservative target, stop and gap contract. M1H therefore cannot advance a
future exit family that depends on candle-path ambiguity, same-bar double
touches, better-than-conservative gaps or a second Python strategy engine.

Before fixed-rule implementation, a separate capability review must identify
one exit family and prove deterministic zero-mismatch fixtures under the pinned
Freqtrade runtime and the conservative audit semantics. Failure blocks
implementation; it does not authorize a custom single-leg backtester.

This review freezes the representability Gate but deliberately selects no exit.

## Paper Protocol Annex

The 1h/2h/4h/8h/12h/24h windows in the M1H paper protocol are market-reaction
observations, not holding periods or exits. MFE, close displacement, MAE and
recovery time are path diagnostics and cannot be converted into an optimistic
lifecycle by this protocol.

Any later lifecycle requires a new capability review before strategy code. It
must reject same-bar optimistic ordering and favorable gap assumptions and
must pass deterministic zero-mismatch fixtures. No current paper Gate can
override that future review.
