# U-10 Cross-Sectional Design Authorization Decision

- Status: `authorized_for_one_independent_outcome_blind_hypothesis_design_only`
- Decision content hash: `e196cc0fdd20e8b8fc84872b440baa09ae69e0752c75005bebefb51a4060c7a0`
- U-09 status: `failed_pre_observation_sample_ceiling`; OOS opened: `false`
- U-09 correction: `c6902525fd4163b0cf929242dc0b88404422421f03745385f615c9dafb3f4479`
- ADR-0015 audit summary: `e26c9a084767e0f3f29a479552d14d24ac27d0a0fff426f953c811bac3d606c4`

U-10 may create exactly one outcome-blind economic hypothesis for the
point-in-time liquid spot cross-section. Its mechanism must be economically
independent of U-04 through U-09 and document causal timing, non-duplication,
failure regimes and future validation boundaries.

Prior outcome signs and failed Gate values may not select U-10. U-09's
membership-boundary sample defect may not be repaired, relabeled or reused.
No new event, path, price or return outcome was read for this decision.

Only hypothesis design is authorized. Event scanning, signals, returns, fixed
rules, Freqtrade code, backtesting, OOS, API/trading, `execution/live` and M2
remain false.
