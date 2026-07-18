# U-06 Cross-Sectional Design Authorization Decision

- Status: `authorized_for_one_independent_outcome_blind_hypothesis_design_only`
- Decision content hash: `596eacbcf2caec7dd1da27bb66ee8bb5859c5b6992c067f22d40e5305cb74662`
- U-05 status: `failed_feasibility`; OOS opened: `false`
- U-05 frozen run: `874cdac32b63535f4b5636420dc55719e8dc795a66e5eca2be96f88ca3737e4a`
- ADR-0015 audit summary: `e26c9a084767e0f3f29a479552d14d24ac27d0a0fff426f953c811bac3d606c4`
- Qualified V4 artifact set: `8784b564e8ce21c88b54045b3236021a16344998356a7a15a332188a441348c3`

## Decision

U-06 may create exactly one outcome-blind economic hypothesis for the
point-in-time liquid spot cross-section. The mechanism must have an economic
rationale independent of U-04 and U-05 and must document causal timing,
non-duplication, failure regimes and future validation boundaries.

The observed U-04/U-05 event directions, measured paths and failed Gate values
may not be inverted, relabeled or otherwise used to choose U-06. No additional
event, path or return outcome was read for this decision.

This decision authorizes only hypothesis design. It does not authorize event
scanning, signals, returns, fixed rules, Freqtrade code, backtesting, OOS,
API/trading, `execution/live` or M2. A separately frozen and independently
reviewed protocol is required before any event scan.
