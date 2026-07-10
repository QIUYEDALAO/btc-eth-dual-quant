# T5 M1D Sample Budget Precheck

- Status: blocked_insufficient_oos_calendar
- Generated UTC: 2026-07-10T17:30:43+00:00
- Scope: metadata-only calendar and sample-budget precheck
- Candidate evaluated: no
- Events selected: no
- OOS prices/returns accessed: no
- Trial count incremented: no
- T5 feasibility analysis executed: no
- Strategy returns computed: no
- API key used: no
- Private data used: no
- Live/paper/execution implemented: no

## Input Authority

- T1 manifest SHA256: `b1fc70626eb05c989635af70866996aa9a432d3627855db7502ae45d893535a7`
- T2 manifest SHA256: `73117868e2c467377fbd399596fc1281e53c04c665e0e2db71e9598ad0857213`
- Candidate hypothesis SHA256: `fdccf79b213f87fc9ee1cb74daf42f67e7ba63fba6de9990851c2eec9e11e1a7`
- Budget result SHA256: `a7fc17af9a4691cca7344c69463aca56f064366d80d93b6de2622d92e7f0336e`
- Only manifest calendar fields, public/private safety flags, and T2 blocker count were read.
- No OHLCV row, price, event, signal, trade, equity, or return field was read.

## Fixed Policy

- Calendar split: final 30% is sealed OOS.
- Minimum sealed OOS calendar: 540 days.
- The API rejects any different fraction or calendar minimum.

## Calendar Result

| Measure | Result | Gate |
|---|---:|---|
| Research start | 2023-10-01 | frozen |
| Latest complete day | 2026-06-30 | complete month |
| Full history | 1004 days | diagnostic |
| IS | 702 days | diagnostic |
| Sealed OOS | 302 days | fail |
| Required sealed OOS | 540 days | fixed |
| OOS shortage | 238 days | blocked |
| Required full history | 1800 days | fixed |
| Earliest eligible complete day | 2028-09-03 | informational |

## Gate

| Check | Status |
|---|---|
| T1/T2 metadata alignment | pass |
| T2 relevant blockers equal zero | pass |
| Trial ledger identity and hash locked | pass |
| OOS remains sealed | pass |
| Metadata-only precheck boundary | pass |
| OOS calendar >= 540 days | fail |

- T5 sample-budget precheck: completed_blocked
- T5 final status: blocked_insufficient_oos_calendar
- T6 authorized: no
- Strategy code authorized: no
- M2 authorized: no

The current M1D candidate stops here. No event threshold, return analysis, Freqtrade strategy, or OOS opening may follow this failed precheck.
