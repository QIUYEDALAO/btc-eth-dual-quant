# U-11 Cross-Sectional Design Authorization Decision

- Status: `authorized_for_one_independent_outcome_blind_hypothesis_design_only`
- Decision content hash: `c5db3dc0c01bc4e1ffe381150c132742446ce4b05b3fb8c381dc03612cff274a`
- U-10 status: `failed_feasibility`; OOS opened: `false`
- U-10 run: `9972a95fe662ac65f7e0e2c0bb4d88eb9743097beb9c7c536f3507d9a316d22f`
- ADR-0015 audit summary: `e26c9a084767e0f3f29a479552d14d24ac27d0a0fff426f953c811bac3d606c4`

U-11 may create exactly one outcome-blind economic hypothesis for the
point-in-time liquid spot cross-section. Its mechanism must be economically
independent of U-04 through U-10 and document causal timing, non-duplication,
failure regimes and future validation boundaries.

Prior outcome signs, measured paths, failed Gates and censor patterns may not
select U-11. U-09's sample-ceiling defect and U-10's sparse complete-path result
may not be repaired, relabeled or reused. No new result was read for this
decision.

Only hypothesis design is authorized. Event scanning, signals, returns, fixed
rules, Freqtrade code, backtesting, OOS, API/trading, `execution/live` and M2
remain false.
