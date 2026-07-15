# Liquid Spot Universe V3 KLAY Source Conflict Adjudication Report

- Classification: `symbol_lifecycle_boundary_artifact`
- Overall decision: `new_policy_adr_required`
- Evidence content hash: `6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a`
- Evidence only: yes
- Registry / contract mutation: no / no
- V3 cold, warm or worker rerun: no
- U-03F / U-04 / strategy / outcomes / OOS / API or trading / M2 authorized: no

## Official Archives

- Monthly key: `data/spot/monthly/klines/KLAYUSDT/1d/KLAYUSDT-1d-2024-10.zip`
- Monthly checksum / ZIP SHA256 / bytes / CRC: `68dce6c6be6ac4e22428771a1402d957becb8e6a1ec9bb7b83507b2029712a59` / `68dce6c6be6ac4e22428771a1402d957becb8e6a1ec9bb7b83507b2029712a59` / 1684 / 84d684ec
- Monthly CSV / rows / columns / header rows / first / last: `KLAYUSDT-1d-2024-10.csv` / 30 / 12 / 0 / `1727740800000` / `1730246400000000`
- Monthly affected line 30: `1730246400000000,0.12550000,0.12550000,0.12550000,0.12550000,0.00000000,1730084399999000,0.00000000,0,0.00000000,0.00000000,0`
- Monthly affected row hash: `8c916992e12bcf4318a93c2ecaf4f00571e1ac7251748cef6676cdead535bfa1`
- Monthly previous row / hash: `1730160000000000,0.12550000,0.12550000,0.12550000,0.12550000,0.00000000,1730246399999999,0.00000000,0,0.00000000,0.00000000,0` / `fde7b4044554dff07cc39570082938a67e4c6763d2106e2b94809dd7d85695b7`
- Monthly next row: None
- Monthly occurrence / duplicate type / republished: 1 / not_duplicate / no
- Daily key: `data/spot/daily/klines/KLAYUSDT/1d/KLAYUSDT-1d-2024-10-30.zip`
- Daily checksum / ZIP SHA256 / bytes / CRC: `7256e669015de0d5d401db062338415318bb1091f2e78e16c4a48b5f75d2a642` / `7256e669015de0d5d401db062338415318bb1091f2e78e16c4a48b5f75d2a642` / 190 / 1e84cc7d
- Daily affected line 1: `1730246400000000,0.12550000,0.12550000,0.12550000,0.12550000,0.00000000,1730084399999000,0.00000000,0,0.00000000,0.00000000,0`
- Daily affected row hash: `8c916992e12bcf4318a93c2ecaf4f00571e1ac7251748cef6676cdead535bfa1`
- Monthly/daily raw, normalized and row-hash identical: True / True / True
- Daily correction candidate valid: no

## Timestamp And Parser Analysis

- Raw open / close: `1730246400000000` / `1730084399999000`
- Independent units / digit counts: microseconds (16) / microseconds (16)
- Normalized open / close UTC: 2024-10-30T00:00:00+00:00 / 2024-10-28T02:59:59.999000+00:00
- Expected close: 2024-10-30T23:59:59.999000+00:00
- Actual / expected duration / delta ms: -162000001 / 86399999 / -248400000
- close_time before open_time: True
- Parser-created / raw-data conflict: False / True
- Independent units / integer conversion / open unit reused for close / float datetime in decision: True / True / False / False

## Public REST Comparators

- api.binance.com: available / HTTP 200 / payload `2ad5825e64bbd0f3cd479f07d1b86cdd22525562a5e58e92d57d562f16a39d12` / row `1730246400000,0.12550000,0.12550000,0.12550000,0.12550000,0.00000000,1730084399999,0.00000000,0,0.00000000,0.00000000,0`
- data-api.binance.vision: available / HTTP 200 / payload `2ad5825e64bbd0f3cd479f07d1b86cdd22525562a5e58e92d57d562f16a39d12` / row `1730246400000,0.12550000,0.12550000,0.12550000,0.12550000,0.00000000,1730084399999,0.00000000,0,0.00000000,0.00000000,0`
- REST sources complete / identical / semantically match archives: True / True / True
- REST is corroboration only and is not a canonical replacement authority.

## Intraday And Lifecycle Diagnostics

- Affected UTC day has official 5m/1h trading bars: False
- Last official intraday close: 2024-10-28T02:59:59.999000+00:00
- Last intraday close equals invalid 1d raw close: True
- Intraday-derived row is diagnostic only; no 1d replacement was created.
- Official announcement: Binance Will Support the Kaia (KLAY) Rebranding to Kaia (KAIA)
- Official reference: https://www.binance.com/en/support/announcement/detail/f75f933759ee49d0af1dfbce7e32144c
- Publication / effective / replacement trading UTC: 2024-10-16T08:00:03.464000+00:00 / 2024-10-28T03:00:00+00:00 / 2024-10-31T08:00:00+00:00
- Announcement payload / normalized evidence hashes: `73570cb9c2f6153337d81f06ad3dac6a208d3b6ae0d89fb45034954979fd2b35` / `26409a7e4f3eecc8fc9332e5ad473f48052d5441b74b70291b718548e6bace42`
- The invalid close_time is exactly one millisecond before KLAY spot trading ceased. The announcement is provenance only and cannot mutate data.

## Similar-Scope Scan

- KLAY monthly / daily / same-month other-symbol archives: 41 / 1 / 386
- Scanned archives / rows: 427 / 13072
- close<open / close=open / invalid duration: 2 / 0 / 5
- close<open affected symbols: KLAYUSDT
- Non-full-duration symbols (includes valid listing/delisting partial days): KLAYUSDT, ORNUSDT, SCRUSDT
- Only KLAY has the close<open class: True
- Remote KLAY daily archives / rows / close<open: 1225 / 1225 / 1
- Remote KLAY daily archive-set hash: `563604866e7de434b55521edeffb90e150b927c4aedc4326831d7be146adc219`

## Decision

Monthly, daily and both public REST sources preserve the same semantically invalid row. The project parser does not create the conflict. Official intraday archives stop exactly at the announced KLAY trading cessation boundary, and no intraday bars exist on the affected day. This uniquely supports `symbol_lifecycle_boundary_artifact`.

ADR-0013 does not define a canonicalization or quarantine rule for a lifecycle placeholder whose monthly and daily authorities are both invalid. The only valid decision is `new_policy_adr_required`. This report records that candidate next stage but does not authorize or create it.

## Immutable Baselines

- blocked_cold_artifact_set: `f661d7abd99adc4067d354afba0c5421e7d1f33c54f768b89c8011ec01eab4f3`
- btt_axs_adjudication_evidence: `8214079900d311c232ecde4b348712f2a5a6d958c8cd98270b9501a71f77330b`
- qualification_summary: `fe236096824fa016be748e67132f225ff02ce4a527fb9b14e67555728c7aa668`
- requalification_run_manifest: `057d4d94e277054b8cbd157dbb5ba05f04f1d0c3c2d28160d5b99689b1624e9c`
- resolution_registry: `570b66e32c3a7ac910ba5ef6688eff966304e65a9519f4f8a902b60fbe4957a4`
- source_manifest: `67529beb72cceeed9aad0baa825cccb5ca1e64c31cf30fdf9a4c076c40fd3bf9`
- v3_contract: `f41f5fedf6002487c9d576a39927ade4409d55e1bc0442aa097e6b2ed054b3ed`

All downstream authorizations remain false. The V3 qualification stays blocked; no registry entry, contract revision, qualification rerun, membership change or hidden repair was made.
