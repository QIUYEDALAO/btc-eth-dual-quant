# U-04 Cross-Sectional Design Authorization Decision

- Decision: `authorized_for_one_preregistered_hypothesis_design_only`
- Decision content hash: `84d9b499329169719a880af80b1e2e7f0d5d5cbbc6c62a6aa762cd738aa04e89`
- ADR-0015 audit: `pass`; manifests: `19/19`; critical/high: `0 / 0`
- Audit summary: `e26c9a084767e0f3f29a479552d14d24ac27d0a0fff426f953c811bac3d606c4`
- Qualified artifact set: `8784b564e8ce21c88b54045b3236021a16344998356a7a15a332188a441348c3`

## Decision

U-04 may create exactly one outcome-blind, preregistered economic hypothesis
for the point-in-time liquid spot cross-section. The design must state its
mechanism, causal timing, non-duplication, failure regimes and future validation
boundaries without reading event outcomes or selecting thresholds.

This decision does not authorize event scanning, signals, returns, strategy
rules, Freqtrade code, backtesting, OOS access, API/trading, `execution/live`
or M2. A separate protocol must be frozen before any event scan. If a future
position could intersect a lifecycle event, fixed-rule work remains blocked
until a separately reviewed delisting/execution policy exists.
