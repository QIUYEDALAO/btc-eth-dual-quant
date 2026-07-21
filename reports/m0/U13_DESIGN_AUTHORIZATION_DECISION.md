# U-13 Cross-Sectional Design Authorization Decision

- Status: `authorized_for_one_independent_outcome_blind_hypothesis_design_only`
- Decision content hash: `8900ada4819a2d951fd26ab6a1d61e18e0e43de939207787c63e05f925866ce6`
- U-12 status/run: `failed_feasibility` / `b42a539c555e37b8b3871910bf5fc21397db3ea01044dee3bbfe3bf7902e7995`
- U-12 OOS opened / second run: `false / false`
- ADR-0015 audit summary: `e26c9a084767e0f3f29a479552d14d24ac27d0a0fff426f953c811bac3d606c4`

U-13 may create exactly one outcome-blind economic hypothesis for the
point-in-time liquid spot cross-section. Its mechanism must be economically
independent of U-04 through U-12 and document causal timing, non-duplication,
failure regimes and future validation boundaries.

No prior event sign, path, failed Gate, concentration, censor pattern or defect
may select U-13. No failed candidate may be repaired, retried, inverted,
relabeled or repackaged.

Only hypothesis design is authorized. Public-data reads, event scanning,
signals, returns, fixed rules, Freqtrade code, backtesting, OOS, API/trading,
`execution/live` and M2 remain false.
