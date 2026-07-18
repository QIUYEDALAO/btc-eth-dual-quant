# U-07 Cross-Sectional Market-Stress Relative-Strength Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Candidate: `U07-CROSS-SECTIONAL-MARKET-STRESS-RELATIVE-STRENGTH-CONTINUATION`
- Protocol content hash: `d62dd323a01507eeb5a78afe646cec196e417faeddd7d84129b2bd8834250195`
- Public data read or event scan executed: no
- Path or return result accessed: no
- OOS opened: no

## Frozen event

Use completed UTC-aligned 4h observations for every exact active member, with
at least ten members and no missing, duplicate, nonmember, quarantined or
lifecycle-ambiguous row. Market stress requires the cross-sectional median
simple return to be at most `-2.50%` and broad selling under the integer rule
`negative × 5 >= active × 4`.

Within that same completed cross-section, the unique candidate must retain at
least `-0.50%` absolute 4h return and exceed the common median by at least
`+2.00%`. Ties use relative residual, simple return and symbol order. All
candidates within a connected 48h window form one episode; only the first is
retained.

## Observation and Gates

The reference is the strict next expected 5m open, with no later search. Fixed
event-time peers exclude the candidate. Candidate absolute displacement, peer
median displacement, relative continuation, MFE, MAE and recovery time are
observed through 1h, 2h, 4h, 8h, 12h, 24h and 48h; incomplete peer or lifecycle
paths are right-censored.

Paper feasibility requires at least 60 complete IS episodes, projected 80 full
and 20 sealed-OOS episodes, broad calendar/symbol distribution,
Median 24h relative continuation of at least `+1.80%`, median 24h candidate absolute close
displacement of at least `+1.80%`, at least 60% positive relative continuation,
and zero qualification, quarantine, lifecycle or order mismatch.

No fill, position, exit, equity or formal strategy return is created. Base,
Cost×2, Stress A and Stress B references remain `0.30%`, `0.60%`, `0.80%` and
`1.10%` roundtrip.

Only an exact-head independent review may follow. Data qualification, events,
paths, returns, strategy code, backtesting, OOS, trading and M2 remain false.
