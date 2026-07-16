# U-03F V4 Independent Auditor Implementation Status

- Status: implementation_fixture_only_pending_independent_review
- Protocol content hash: `0f4127ceb4f57f78c6fead022f9c71cb07d0f10c55d4a91f3f9cde57005a8157`
- Audit algorithm hash: `a20da081dff753ba9091c91b91205bf9bf55781c7e1e04ea67e16b83a65469d8`
- Production builder imported or called: no
- Full `2020-01` through `2026-06` audit executed: no
- Production evidence modified: no
- U-04/strategy/events/returns/backtesting/OOS/M2 authorized: no

The implementation provides independent strict JSON/canonical serialization,
integer UTC month/day/grid arithmetic, Binance ZIP/CRC/schema parsing,
source-freeze verification, monthly-primary/daily-fill authority, generic
hash-bound ADR-0013 conflict resolution, Decimal 365/90-day eligibility and
ranking, registry-driven lifecycle boundaries and affected-row quarantine,
exact 5m grids, 1h aggregation, complete-day and active-universe state,
gap attribution, all 15 required audit artifacts and field-level comparison.
The fixture/fault suite covers tampered source evidence, unknown conflicts,
registry drift, lifecycle overlap/new rows, rank/future leakage, missing bars,
manifest/report tamper, copied production code and authorization escalation.
It runs without raw public data.

The implementation checker records float-timestamp candidates in the current
production V4 authority path. These are not repaired or adjudicated here. The
real audit must apply the frozen integer-time Gate; any policy violation or
data difference is a truthful `failed_audit` result.
