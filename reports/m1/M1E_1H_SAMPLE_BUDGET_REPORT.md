# M1E 1H Sample Budget Report

- Status: sample_budget_pass_design_only
- Generated UTC: 2026-07-10T21:10:18+00:00
- Scope: metadata-only calendar admission
- Candidate evaluated: no
- Events selected: no
- OOS prices/returns accessed: no
- Trial count incremented: no
- Strategy rules selected: no
- Strategy returns computed: no
- API key used: no
- Private data used: no

## Input Authority

- M1E requalification manifest SHA256: `c8b15858bd7cb7467fdc0e9067c9e7494e724a08af49762bfd72ad2c9528bba8`
- Candidate hypothesis SHA256: `3668032467e2f46edff7f0ab27d358d0b918889518bfaf97276699cbc783ed15`
- Budget result SHA256: `608edc28c01c263d2c72859aa8a994d23785e1c040ff49a6e56ad2fd9a5382d8`
- Only sanitized manifest admission metadata and sealed trial identity were read.
- No OHLCV row, price, event, signal, trade, equity, or return field was read.

## Fixed Policy

- Calendar split: final 30% is sealed OOS.
- Minimum full history: 1800 days.
- Minimum sealed OOS calendar: 540 days.
- Callers cannot override these values.

## Calendar Result

| Measure | Result | Gate |
| --- | ---: | --- |
| Research start | 2020-07-01 | frozen |
| Latest complete day | 2026-06-30 | complete month |
| Full history | 2191 days | pass |
| IS | 1533 days | diagnostic |
| Sealed OOS start | 2024-09-11 | frozen split |
| Sealed OOS | 658 days | pass |
| Required sealed OOS | 540 days | fixed |
| OOS shortage | 0 days | pass |
| Required full history | 1800 days | fixed |
| Earliest eligible complete day | 2025-06-04 | informational |

## Gate

- M1E sample-budget Gate: pass
- OOS remains sealed: pass
- Metadata-only boundary: pass
- IS-only design review authorized: yes
- Strategy code authorized: no
- Freqtrade backtesting authorized: no
- M2 authorized: no

Passing this Gate authorizes a separate IS-only rule-design review. It does not approve a strategy, open OOS, authorize backtesting, or permit trading.
