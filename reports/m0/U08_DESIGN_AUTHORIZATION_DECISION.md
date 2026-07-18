# U-08 Cross-Sectional Design Authorization Decision

- Status: `authorized_for_one_independent_outcome_blind_hypothesis_design_only`
- Decision content hash: `813267f29fd2f019b7d856d95a5eaaa7927a3f072327cc643e6a1ecd51af1cf9`
- U-07 status: `failed_feasibility`; OOS opened: `false`
- U-07 frozen run: `8c637a3f13dad4410beb446094af011582ab2cde0ac449e32d044cbaa709352c`
- ADR-0015 audit summary: `e26c9a084767e0f3f29a479552d14d24ac27d0a0fff426f953c811bac3d606c4`
- Qualified V4 artifact set: `8784b564e8ce21c88b54045b3236021a16344998356a7a15a332188a441348c3`

## Decision

U-08 may create exactly one outcome-blind economic hypothesis for the
point-in-time liquid spot cross-section. Its mechanism must be economically
independent of U-04 through U-07 and must document causal timing,
non-duplication, failure regimes and future validation boundaries.

The prior candidates' event directions, measured paths and failed Gate values
may not be inverted, relabeled or otherwise used to choose U-08. No additional
event, path or return outcome was read for this decision.

This decision authorizes only hypothesis design. It does not authorize event
scanning, signals, returns, fixed rules, Freqtrade code, backtesting, OOS,
API/trading, `execution/live` or M2. A separately frozen and independently
reviewed protocol is required before any event scan.
