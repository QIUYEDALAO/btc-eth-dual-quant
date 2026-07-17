# U-03F V4 Invalid-Interval Adjudication Diagnostic

- Status: completed_new_policy_adr_required
- Decision: `new_policy_adr_required`
- Diagnostic base main: `70c784b1573de8437e189672c89e9c00b6505978`
- Protocol content hash: `9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190`
- Source freeze: `c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c`
- Frozen archives verified per order: 27,736
- Invalid physical rows: 119
- Synchronized windows: 8 / 8
- Three-order canonical hash: `ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677`
- Diagnostic run manifest: `df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33`
- Production pipeline modified: no
- Policy adopted: no
- Requalification/new audit/U-04/OOS/M2 authorized: no

## Evidence

All 27,736 source-freeze entries passed exact byte-size, SHA256, ZIP CRC
and single-member identity checks in normal, reverse and deterministic-
shuffled traversal. The 1,170 frozen Top-15 member-month 5m archives were
then scanned with integer-only timestamp normalization.

The 119 known blocked symbol-months resolve to exactly 119 physical rows.
They group into eight exact UTC open times; every group meets the frozen
two-symbol and 80% synchronous evidence threshold.

| Open time UTC | Invalid / active | Missing invalid member | Close deltas ms |
| --- | ---: | --- | --- |
| 2020-02-19T11:35:00.000Z | 15 / 15 | none | 32286, 32298, 33099, 33491, 33982, 34985, 35062, 35180, 35287, 35448, 35470, 35480, 35736, 36218, 36364 |
| 2020-03-04T09:20:00.000Z | 15 / 15 | none | 106694, 106700, 107141, 107365, 107641, 108160, 108203, 108269, 108330, 108414, 108426, 108432, 108566, 108826, 108907 |
| 2020-12-21T14:05:00.000Z | 15 / 15 | none | -1059479, -1059472, -1059076, -1058937, -1058747, -1058367, -1058344, -1058290, -1058162, -1058046, -1057875, -1057729, -1057718, -1057593, -1057016 |
| 2021-02-11T03:40:00.000Z | 15 / 15 | none | 53902, 54403, 54577, 54773, 55279, 55700, 55732, 55829, 56650, 56799, 58431, 58650, 58958, 59081, 59257 |
| 2021-04-25T04:00:00.000Z | 15 / 15 | none | 57224, 57487, 57803, 57981, 58146, 58902, 59140, 59271, 60132, 60278, 60367, 62102, 62371, 62685, 62802 |
| 2021-08-13T01:55:00.000Z | 15 / 15 | none | 299000 |
| 2021-12-24T04:55:00.000Z | 14 / 15 | XRPUSDT | 292654, 293504, 294118, 294362, 295588, 295682, 296158, 296316, 296613, 297827, 298113, 298268, 300475, 301217 |
| 2023-03-24T12:35:00.000Z | 15 / 15 | none | 280151, 281001, 281451, 281646, 282562, 283061, 283183, 283413, 283510, 284685, 284908, 285102, 286774, 286948, 288301 |

## Policy Boundary

This is evidence, not policy adoption. The current V4 contract does not
authorize converting invalid physical rows into accepted synchronized gaps.
Direct reuse of the existing gap policy and per-row exception registration
remain forbidden. After this evidence merges, only a separate Draft policy
ADR may be created and independently reviewed.

Historical PR #89, PR #95 and PR #100 evidence and every frozen source byte
remain unchanged. Runtime implementation, public requalification, a new
independent audit, U-04, strategy/backtesting, OOS, API/trading,
`execution/live` and M2 remain unauthorized.
