# U-06 Cross-Sectional Volume-Share Absorption Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Protocol hash: `7b53860efa2a5c52d727f1d4d4694ddf39ff34517dfde6aaf4b6abe31f35f289`
- Public data read or event scan executed: no
- Path or return result accessed: no
- OOS opened: no

## Frozen event

For each completed UTC day, use the exact point-in-time active universe. A
candidate's quote-volume share must be at least 2.00 times its prior 30-day
median share, its absolute quote volume at least 1.50 times its prior median,
and its daily return must remain within ±1.00% of the peer median. Only the
largest share-ratio candidate survives each day; ties use absolute volume ratio
then symbol. Events form 72-hour connected episodes and keep the first event.

## Frozen observation

The reference is the first expected 5m open strictly after the completed day;
missing references are not searched forward. Candidate absolute displacement
and repricing relative to the fixed event-time peer basket are observed through
72h. Missing, quarantined, membership-changing or lifecycle-intersecting paths
are right-censored. No fill, position, equity or formal return is created.

## Frozen Gates

The protocol requires at least 60 complete IS episodes, projected 80 full and
20 sealed-OOS episodes, broad year/symbol distribution, and median 24h relative
repricing and absolute displacement each at least 1.80%. Authority, quarantine,
lifecycle and traversal-order mismatches must be zero.

Only an exact-head independent review may follow. Data qualification, event
scanning, paths, returns, fixed rules, Freqtrade, OOS, trading and M2 remain
unauthorized.
