# U-05 Cross-Sectional Design Authorization Decision

- Status: `authorized_for_one_independent_outcome_blind_hypothesis_design_only`
- Decision content hash: `48482a1d72b34d4925e3b0ed8ab218df202d560af7d8057c4fa8be403c46dc2c`
- U-04 status: `failed_feasibility`; OOS opened: `false`
- U-04 frozen run: `9182c9e3fb2aad6959d98ccbe18c77e411a3d5ce5adc6fdf352da76cd53eebc2`
- ADR-0015 audit summary: `e26c9a084767e0f3f29a479552d14d24ac27d0a0fff426f953c811bac3d606c4`
- Qualified V4 artifact set: `8784b564e8ce21c88b54045b3236021a16344998356a7a15a332188a441348c3`

## Decision

U-05 may create exactly one outcome-blind economic hypothesis for the
point-in-time liquid spot cross-section. The mechanism must have an economic
rationale independent of U-04 and must document causal timing,
non-duplication, failure regimes and future validation boundaries.

The observed U-04 event direction and failed recovery measurements may not be
inverted, relabeled or otherwise used to choose U-05. No additional event or
path outcomes were read for this decision.

This decision authorizes only hypothesis design. It does not authorize event
scanning, signals, returns, fixed rules, Freqtrade code, backtesting, OOS,
API/trading, `execution/live` or M2. A separately frozen and independently
reviewed protocol is required before any event scan.
