# M0 Signoff

Date: 2026-07-09

## 1. M0 Scope Statement

M0 is approved as read-only data engineering only.

- read-only data engineering only: yes
- no `execution/live`: yes
- no order placement: yes
- no cancel order: yes
- no simulated matching: yes
- no trading permission calls: yes

Signed Binance requests are limited to read-only archival and cost-calibration endpoints: `GET /fapi/v1/income`, `GET /api/v3/account/commission`, and `GET /fapi/v1/commissionRate`.

## 2. Registry Acceptance

Validation command:

```bash
PYTHONPATH=src /Users/liudehua/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 - <<'PY'
from btc_eth_dual_quant.data.registry import load_registry
r = load_registry('data_registry.yaml')
print('total', len(r.datasets))
print('enabled', len(r.enabled_records()))
for rec in r.enabled_records():
    print(rec.name)
PY
```

Result:

- `data_registry.yaml` total records: 20
- `enabled=true` records: 13
- Pydantic schema validation: pass

Enabled data items:

1. `spot_klines`
2. `um_futures_klines`
3. `funding_rate_history`
4. `premium_index`
5. `funding_info`
6. `mark_price_klines`
7. `index_price_klines`
8. `premium_index_klines`
9. `open_interest`
10. `order_book_depth`
11. `funding_income`
12. `commissions`
13. `exchange_rules`

Specific coverage checks:

- Depth/bookTicker included: yes, via `order_book_depth`
- Spot/futures `exchangeInfo` included: yes, via `exchange_rules`

## 3. Collector Matrix

Raw storage path convention: `storage/raw/<dataset>/year=YYYY/month=MM/day=DD/raw.jsonl`.

| Dataset | Collector function | Endpoint | Required fields | Raw storage path | DuckDB table | Validation rules | Fallback rules |
|---|---|---|---|---|---|---|---|
| `spot_klines` | `spot_klines()` | `GET /api/v3/klines` | `open_time`, `open`, `high`, `low`, `close`, `volume`, `quote_volume`, `trade_count`, `close_time` | `storage/raw/spot_klines/.../raw.jsonl` | `raw_spot_klines` | `gap_check`, `zip_rest_compare`, `kline_anomaly` | Binance Public Data monthly/daily ZIP |
| `um_futures_klines` | `um_futures_klines()` | `GET /fapi/v1/klines` | `open_time`, `open`, `high`, `low`, `close`, `volume`, `quote_volume`, `trade_count`, `close_time` | `storage/raw/um_futures_klines/.../raw.jsonl` | `raw_um_futures_klines` | `gap_check`, `zip_rest_compare`, `kline_anomaly` | Binance Public Data futures/um monthly/daily ZIP |
| `funding_rate_history` | `funding_rate_history()` | `GET /fapi/v1/fundingRate` | `symbol`, `fundingRate`, `fundingTime`, `markPrice` | `storage/raw/funding_rate_history/.../raw.jsonl` | `raw_funding_rate_history` | `gap_check`, `funding_interval_check` | `premium_index_next_funding_time` |
| `premium_index` | `premium_index()` | `GET /fapi/v1/premiumIndex` | `markPrice`, `indexPrice`, `lastFundingRate`, `nextFundingTime`, `time` | `storage/raw/premium_index/.../raw.jsonl` | `raw_premium_index` | `required_fields`, `funding_interval_check` | `funding_rate_history_time_delta` |
| `funding_info` | `funding_info()` | `GET /fapi/v1/fundingInfo` | `fundingIntervalHours`, `adjustedFundingRateCap`, `adjustedFundingRateFloor` | `storage/raw/funding_info/.../raw.jsonl` | `raw_funding_info` | `required_fields`, `funding_interval_check` | `premiumIndex.nextFundingTime`, `fundingRate.fundingTime` |
| `mark_price_klines` | `mark_price_klines()` | `GET /fapi/v1/markPriceKlines` | `open_time`, `open`, `high`, `low`, `close`, `close_time` | `storage/raw/mark_price_klines/.../raw.jsonl` | `raw_mark_price_klines` | `gap_check`, `kline_anomaly` | `premium_index.markPrice snapshots` |
| `index_price_klines` | `index_price_klines()` | `GET /fapi/v1/indexPriceKlines` | `open_time`, `open`, `high`, `low`, `close`, `close_time` | `storage/raw/index_price_klines/.../raw.jsonl` | `raw_index_price_klines` | `gap_check`, `kline_anomaly` | `premium_index.indexPrice snapshots` |
| `premium_index_klines` | `premium_index_klines()` | `GET /fapi/v1/premiumIndexKlines` | `open_time`, `open`, `high`, `low`, `close`, `close_time` | `storage/raw/premium_index_klines/.../raw.jsonl` | `raw_premium_index_klines` | `gap_check`, `kline_anomaly` | `premium_index snapshots` |
| `open_interest` | `open_interest_hist()` | `GET /futures/data/openInterestHist` | `sumOpenInterest`, `sumOpenInterestValue`, `timestamp` | `storage/raw/open_interest/.../raw.jsonl` | `raw_open_interest` | `archive_completeness`, `gap_check` | third-party CoinGlass or self-built archive |
| `order_book_depth` | `spot_depth()`, `futures_depth()`, `spot_book_ticker()`, `futures_book_ticker()` | `GET /api/v3/depth`, `GET /api/v3/ticker/bookTicker`, `GET /fapi/v1/depth`, `GET /fapi/v1/ticker/bookTicker` | `bids_top5`, `asks_top5`, `bookTicker`, `local_received_time` | `storage/raw/order_book_depth/.../raw.jsonl` | `raw_order_book_depth` | `required_fields`, `non_crossed_book` | bookTicker when full depth unavailable |
| `funding_income` | `funding_income()` | `GET /fapi/v1/income?incomeType=FUNDING_FEE` | `income`, `incomeType`, `symbol`, `time`, `tranId` | `storage/raw/funding_income/.../raw.jsonl` | `raw_funding_income` | `archive_completeness`, `required_fields` | account statements |
| `commissions` | `spot_account_commission()`, `futures_commission_rate()` | `GET /api/v3/account/commission`, `GET /fapi/v1/commissionRate` | `maker`, `taker`, `discount`, `commissionAsset` | `storage/raw/commissions/.../raw.jsonl` | `raw_commissions` | `required_fields`, `cost_model_drift` | official fee page manual review |
| `exchange_rules` | `spot_exchange_info()`, `futures_exchange_info()` | `GET /api/v3/exchangeInfo`, `GET /fapi/v1/exchangeInfo` | `tickSize`, `stepSize`, `minQty`, `minNotional`, `pricePrecision`, `quantityPrecision` | `storage/raw/exchange_rules/.../raw.jsonl` | `raw_exchange_rules` | `required_fields`, `versioned_snapshot` | official exchange info snapshot archive |

## 4. Read-only Safety Scan

Trading endpoint and SDK-method scan:

```bash
rg -n '(/api/v3/order|/fapi/v1/order|/sapi/v1/margin/order|POST|DELETE|place_order|cancel_order|create_order|simulate_fill|matching_engine)' src || true
```

Result: no matches in `src/`.

`execution/live` path scan:

```bash
find . -path './src/execution/live' -print -o -path './execution/live' -print
```

Result: no output; no `execution/live` path exists.

Tests are allowed to mention forbidden endpoints to assert rejection behavior. Current test coverage includes `test_client_rejects_trading_paths` and `test_no_trading_endpoint_implementation`.

## 5. Storage Acceptance

Append-only raw store:

- Raw responses are written as JSONL envelopes through `AppendOnlyRawStore.append()`.
- Path convention is partitioned by UTC ingestion date.
- Envelope includes dataset, source, endpoint, params, payload, ingestion timestamp, and payload hash.
- The implementation opens raw files with append mode only.

Repeated write proof:

- `test_raw_store_is_append_only_jsonl` writes two payloads to the same dataset and verifies both records remain present in order.

DuckDB layer:

- `DuckDBLayer.index_envelopes()` indexes immutable raw envelopes into `raw_envelopes`.
- `DuckDBLayer.create_derived_table()` appends derived rows.
- DuckDB code does not overwrite or mutate raw JSONL files.

## 6. Data Quality Acceptance

Unit test command:

```bash
PYTHONPATH=src /Users/liudehua/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest discover -s tests -v
```

Result: 18 tests passed.

Covered data quality checks:

- K-line gap detection: `test_gap_detection_blocks_only_over_three_missing_bars`
- ZIP/REST dual-source comparison interface: `test_zip_rest_compare_and_anomaly_flags`
- K-line anomaly marking for amplitude greater than 30% and zero volume: `test_zip_rest_compare_and_anomaly_flags`
- OI/income archival completeness checks: `test_archive_completeness_missing_days`

## 7. Funding Acceptance

Funding interval resolution order:

1. `fundingInfo.fundingIntervalHours`
2. `premiumIndex.nextFundingTime`
3. historical `fundingRate.fundingTime`

Acceptance cases:

- `fundingInfo` priority case: `test_funding_info_has_priority_when_consistent`
- `premiumIndex.nextFundingTime` fallback case: `test_premium_index_fallback`
- `fundingRate.fundingTime` inference case: `test_history_fallback_and_annualization`
- Conflict case uses shorter interval and emits warning: `test_conflict_uses_shorter_interval_and_warns`

Hardcoded 8-hour scan:

```bash
rg -n 'fundingIntervalHours.*8|8.*fundingIntervalHours|interval_hours\s*=\s*8|Decimal\("8"\)|default.*8h|hard.?code.*8' src/btc_eth_dual_quant || true
```

Result: no matches. Funding annualization requires an inferred interval and does not assume 8 hours.

## 8. Cost / Payback Acceptance

Implemented functions:

- Real fee refresh: `refresh_real_fee_snapshot()`
- Spot commission parser: `parse_spot_commission()`
- Futures commission parser: `parse_futures_commission()`
- Round-trip cost baseline: `compute_roundtrip_cost()`
- Funding payback threshold: `funding_payback_threshold()`

Configured M0 assumptions from V1.1:

- `arb.min_payback_ratio = 2.0`
- `arb.expected_hold_days = 14`
- Round-trip cost baseline example: `0.50%`

Payback math:

- Expected funding income over holding window = annualized funding rate x `14 / 365`
- Required annualized funding rate = `2.0 x 0.005 x 365 / 14 = 0.2607142857`
- Required annualized funding rate is approximately `26.1%`
- At `8%` annualized funding: `0.08 x 14 / 365 / 0.005 = 0.6137`, below `2.0`; entry must be rejected.

Test coverage:

- `test_parse_commissions_and_roundtrip_cost`
- `test_payback_threshold`

## 9. Backtest Skeleton Acceptance

M0 backtest skeleton validates time semantics only.

Rules:

- Signal is produced after the current bar close.
- Earliest effective fill time is the next bar open.
- A feature timestamp after decision time is rejected as lookahead.
- Scheduling on the final bar without a next open is rejected.

Test coverage:

- `test_decision_schedules_next_bar_open`
- `test_feature_after_decision_is_lookahead`
- `test_current_bar_close_fill_is_rejected`

The skeleton does not implement order execution, fills, simulated matching, or position accounting.

## 10. Final Conclusion

M0 result: pass.

Completed:

- Full 20-item registry coverage for V1.1 section 4.1.
- 13 M0 enabled read-only collectors registered and implemented.
- Append-only raw storage and DuckDB query/index layer.
- Data quality checks for gaps, ZIP/REST comparison, K-line anomalies, and archive completeness.
- Funding interval inference without hardcoded 8-hour assumptions.
- Real-fee refresh, round-trip cost baseline, and funding payback threshold.
- Minimal backtest time-semantics skeleton.
- Unit tests and read-only guardrails.

Unfinished items:

- No live API data was pulled during signoff.
- No historical ZIP backfill runner or scheduler CLI was added.
- No production report renderer was added beyond this Markdown signoff.

M1 blockers:

- Produce actual M0 data-quality reports from downloaded BTC/ETH history.
- Run real read-only commission refresh with API keys that have no trading permission.
- Archive OI and income daily from the first paper/live observation day.
- Review any unexplained data-quality anomalies before enabling M1 backtests.
