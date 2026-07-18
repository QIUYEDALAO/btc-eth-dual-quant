# U-09 Cross-Sectional Design Authorization Decision

- Status: `authorized_for_one_independent_outcome_blind_hypothesis_design_only`
- Decision content hash: `2d643678e00575c93dad0331fff089fd620b214f658ca8d174dfe9bbcc06e477`
- U-08 status: `failed_feasibility`; OOS opened: `false`
- U-08 frozen run: `f6fbcdee846b855883a5e356ea49e6a98901bfcc6a9dbd5a2cbb07ebed9eca3e`
- ADR-0015 audit summary: `e26c9a084767e0f3f29a479552d14d24ac27d0a0fff426f953c811bac3d606c4`
- Qualified V4 artifact set: `8784b564e8ce21c88b54045b3236021a16344998356a7a15a332188a441348c3`

## Decision

U-09 may create exactly one outcome-blind economic hypothesis for the
point-in-time liquid spot cross-section. Its mechanism must be economically
independent of U-04 through U-08 and must document causal timing,
non-duplication, failure regimes and future validation boundaries.

The five prior candidates' event directions, measured paths and failed Gate
values may not be inverted, relabeled or otherwise used to choose U-09. No
additional event, path or return outcome was read for this decision.

This decision authorizes only hypothesis design. It does not authorize event
scanning, signals, returns, fixed rules, Freqtrade code, backtesting, OOS,
API/trading, `execution/live` or M2. A separately frozen and independently
reviewed protocol is required before any event scan.
