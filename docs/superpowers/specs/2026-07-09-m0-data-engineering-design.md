# M0 Data Engineering Design

## Scope

M0 implements a registry-driven, read-only data layer for the BTC/ETH dual-strategy project. It covers every item in V1.1 section 4.1 in `data_registry.yaml`, while only enabling the M0 collectors requested for market data, funding data, account read-only fee/income data, exchange rules, and top-of-book/depth snapshots.

M0 explicitly excludes `execution/live`, order placement, cancellation, simulated matching, position management, and any endpoint whose purpose is trading rather than read-only archival or cost calibration.

## Architecture

- `data_registry.yaml` is the source of truth for dataset lineage. Each record must include `name`, `source`, `endpoint`, `fields`, `granularity`, `history_start`, `retention_limit`, `update_freq`, `table`, `validations`, `fallback`, and `consumers`. Optional `phase` and `enabled` distinguish registered future datasets from currently implemented M0 datasets.
- `src/btc_eth_dual_quant/data/registry.py` validates the registry with Pydantic and exposes enabled records.
- `src/btc_eth_dual_quant/data/binance.py` contains only read-only Binance REST clients and collectors.
- `src/btc_eth_dual_quant/data/storage.py` writes every raw response as append-only JSONL under `storage/raw/...`.
- `src/btc_eth_dual_quant/data/duckdb_layer.py` creates DuckDB query/index tables from raw records and derived reports. Raw files are never overwritten.
- `src/btc_eth_dual_quant/data/quality.py` implements gap checks, ZIP/REST comparison, K-line anomaly flags, and OI/income archival completeness checks.
- `src/btc_eth_dual_quant/data/funding.py` resolves funding intervals using `fundingInfo.fundingIntervalHours`, then `premiumIndex.nextFundingTime`, then historical `fundingRate.fundingTime`. Conflicts emit warnings and use the shorter interval for conservative annualization.
- `src/btc_eth_dual_quant/data/costs.py` refreshes real account/futures commission data, computes round-trip cost baselines, and evaluates the funding-payback threshold.
- `src/btc_eth_dual_quant/backtest/skeleton.py` provides the minimum time-semantics skeleton needed for M0 forward-looking bias tests.

## Data Flow

Collectors receive a registry record plus symbol/interval parameters, call the configured read-only endpoint, and append a raw envelope containing ingestion time, source, endpoint, request params, response payload, and content hash. DuckDB tables are rebuilt or appended from those immutable envelopes for SQL querying and derived checks.

Signed read-only endpoints are supported only for `income`, spot account commission, and futures commission rate. API keys are supplied by environment variables and the client only signs GET query strings. No order endpoint constants or methods are present.

## Validation And Testing

Unit tests cover registry completeness, enabled M0 datasets, append-only raw writes, funding interval fallback and conflict handling, cost/payback math, quality checks, DuckDB SQL generation boundaries, backtest time semantics, and guardrails that ensure no `execution/live` tree or trading endpoint implementation exists.

## Local Validation Commands

This workspace may keep local dependencies in the ignored `.deps/` directory. The standard local commands are:

```bash
PYTHONPATH=.deps:src python3 -m unittest discover -s tests -v
PYTHONPATH=.deps:src python3 -m compileall src scripts
bash scripts/m0_validate.sh
```

The system command `python` is not required. If `python` is missing, that is an environment issue rather than an M0 failure; the standard validation entrypoint defaults to `python3` through `${PYTHON:-python3}`.

Code may reference the environment variable names `BINANCE_API_KEY` and `BINANCE_API_SECRET`, and internal field names such as `api_key` and `api_secret`, without that being a secret leak. Real key values are judged by `scripts/m0_secret_scan.py`, which scans git-indexed files for high-confidence secret values, tracked `.env` files, private key blocks, `sk-` tokens, and hardcoded long credential assignments.
