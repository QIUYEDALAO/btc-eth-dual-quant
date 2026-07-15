# Liquid Spot Universe V2 Source Conflict Adjudication Report

- Overall decision: new_policy_adr_required
- Same-contract U-03E rerun authorized: no
- Contract hash: `051894e89b713f541caa601efab51be22f83461a4e624e1d51d7f576ed8cda51`
- Source manifest hash: `928c3520028ddf5bfc1c03fe3185d5af4b9ad8fea0f327469d60f388a3f638cf`
- Qualification summary hash: `80cd0a88b6253f06aeb40bfe4123aa55f874ce31a40d2e94a46859b2aba8380c`
- Evidence content hash: `8214079900d311c232ecde4b348712f2a5a6d958c8cd98270b9501a71f77330b`
- Strategy/events/returns/backtesting/OOS/M2/API or trading authorized: no
- Raw ZIP, cache, DuckDB or logs committed: no

## Adjudication

### U03E-BTTUSDT-1D-2019-01-NEGATIVE-BASE-VOLUME

- Symbol / interval / month: BTTUSDT / 1d / 2019-01
- Affected timestamps: 2019-01-31T00:00:00+00:00
- Monthly key: `data/spot/monthly/klines/BTTUSDT/1d/BTTUSDT-1d-2019-01.zip`
- Monthly URL: https://data.binance.vision/data/spot/monthly/klines/BTTUSDT/1d/BTTUSDT-1d-2019-01.zip
- Current checksum: `304382601fa91cd11ecdda83442850b35dd8c072875ef96d9871808179c4c724  BTTUSDT-1d-2019-01.zip`
- ZIP SHA256 / bytes / CRC: `304382601fa91cd11ecdda83442850b35dd8c072875ef96d9871808179c4c724` / 232 / pass
- CSV filename / columns / header rows: `BTTUSDT-1d-2019-01.csv` / 12 / 0
- Timestamp unit / duplicate type: milliseconds / not_duplicate
- Current official checksum changed from local cache: no
- Classification: official_monthly_daily_conflict
- Adjudication: confirmed_requires_general_data_policy
- Same-contract rerun allowed: no

Affected monthly rows:

- line 1: `1548892800000,0.00040000,0.00060000,0.00031990,0.00047640,-61596941261.09551616,1548979199999,62154329.51276230,81569,55075450629.00000000,27674180.32962640,0`

Same-month schema comparator: `data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2019-01.zip` / `445904985d35f847c5c0cb4dc582c10e07967aaa6a424ee30373194b2f815519` / 12 columns / 0 header rows / milliseconds timestamps.

The negative value is column 6 `base_volume`. Official daily ZIP and both public REST hosts agree on the positive row; all other authoritative fields match. The delta is exactly `2^64 / 1e8`, an overflow signature. This is evidence of a monthly/daily official-source conflict, not permission to repair the monthly row.

### U03E-BTTUSDT-1D-2019-02-NEGATIVE-BASE-VOLUME

- Symbol / interval / month: BTTUSDT / 1d / 2019-02
- Affected timestamps: 2019-02-04T00:00:00+00:00, 2019-02-05T00:00:00+00:00, 2019-02-06T00:00:00+00:00, 2019-02-12T00:00:00+00:00
- Monthly key: `data/spot/monthly/klines/BTTUSDT/1d/BTTUSDT-1d-2019-02.zip`
- Monthly URL: https://data.binance.vision/data/spot/monthly/klines/BTTUSDT/1d/BTTUSDT-1d-2019-02.zip
- Current checksum: `9d396d4bc1995456cf2f37a286c637c623420170e03a9c5c02db32f7c28907a5  BTTUSDT-1d-2019-02.zip`
- ZIP SHA256 / bytes / CRC: `9d396d4bc1995456cf2f37a286c637c623420170e03a9c5c02db32f7c28907a5` / 1842 / pass
- CSV filename / columns / header rows: `BTTUSDT-1d-2019-02.csv` / 12 / 0
- Timestamp unit / duplicate type: milliseconds / not_duplicate
- Current official checksum changed from local cache: no
- Classification: official_monthly_daily_conflict
- Adjudication: confirmed_requires_general_data_policy
- Same-contract rerun allowed: no

Affected monthly rows:

- line 4: `1549238400000,0.00061400,0.00095360,0.00061070,0.00086630,-40903096150.09551616,1549324799999,110277831.58541880,212350,70054616493.00000000,53850055.79687110,0`
- line 5: `1549324800000,0.00086520,0.00128430,0.00086520,0.00101830,-5990281771.09551616,1549411199999,191790754.23974620,346174,84693921491.00000000,90975211.88162550,0`
- line 6: `1549411200000,0.00101820,0.00105750,0.00085700,0.00096750,-91425140619.09551616,1549497599999,88267214.69020920,190995,43873513218.00000000,41634912.46783460,0`
- line 12: `1549929600000,0.00086820,0.00116500,0.00086370,0.00102170,-86918434254.09551616,1550015999999,99391188.38483510,188301,46603004102.00000000,47509114.84409810,0`

Same-month schema comparator: `data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2019-02.zip` / `9bcdcbc003cce89ba5917367cd617bdd5abf17e427e4f7625b62f9ab9cc7439c` / 12 columns / 0 header rows / milliseconds timestamps.

The negative value is column 6 `base_volume`. Official daily ZIP and both public REST hosts agree on the positive row; all other authoritative fields match. The delta is exactly `2^64 / 1e8`, an overflow signature. This is evidence of a monthly/daily official-source conflict, not permission to repair the monthly row.

### U03E-AXSUSDT-1D-2026-02-10-DUPLICATE

- Symbol / interval / month: AXSUSDT / 1d / 2026-02
- Affected timestamps: 2026-02-10T00:00:00+00:00
- Monthly key: `data/spot/monthly/klines/AXSUSDT/1d/AXSUSDT-1d-2026-02.zip`
- Monthly URL: https://data.binance.vision/data/spot/monthly/klines/AXSUSDT/1d/AXSUSDT-1d-2026-02.zip
- Current checksum: `7f18d5a29f2e767389efce407d47a247dac3e0e309cef4a3b377040bddf001bf  AXSUSDT-1d-2026-02.zip`
- ZIP SHA256 / bytes / CRC: `7f18d5a29f2e767389efce407d47a247dac3e0e309cef4a3b377040bddf001bf` / 1666 / pass
- CSV filename / columns / header rows: `AXSUSDT-1d-2026-02.csv` / 12 / 0
- Timestamp unit / duplicate type: microseconds / byte_identical_duplicate
- Current official checksum changed from local cache: no
- Classification: exact_identical_duplicate
- Adjudication: confirmed_requires_general_data_policy
- Same-contract rerun allowed: no

Affected monthly rows:

- line 10: `1770681600000000,1.47900000,1.65400000,1.44000000,1.57400000,18935177.03000000,1770767999999999,29141814.85779000,128555,9355027.88000000,14408718.46470000,0`
- line 11: `1770681600000000,1.47900000,1.65400000,1.44000000,1.57400000,18935177.03000000,1770767999999999,29141814.85779000,128555,9355027.88000000,14408718.46470000,0`

Both official monthly and daily ZIPs contain two byte-identical rows for the timestamp; both public REST hosts return one matching row. The raw archive itself is duplicated, so this is not parser-created. AXS is not a V2 Top-15 member, but that does not waive the conflict.

## Decision

The current V2 contract correctly fails closed. No official monthly archive was republished, no parser/schema bug was found, and the current contract has no approved general rule for replacing an invalid monthly row with daily/REST evidence or collapsing exact same-authority duplicates.

A new general data-policy ADR is required before any behavior can change. This adjudication does not adopt such a policy, modify the V2 contract, rerun U-03E, authorize U-03F/U-04, or approve any strategy work.

## Official Source Context

- Binance public-data schema and checksum authority: https://github.com/binance/binance-public-data
- Monthly and daily archives: https://data.binance.vision/
- Public REST comparators: https://api.binance.com/api/v3/klines and https://data-api.binance.vision/api/v3/klines
- No source-owner issue/comment was posted by this task.
