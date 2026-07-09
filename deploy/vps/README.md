# VPS Deployment For Freqtrade Lab

This directory contains deployment helpers for the M1F Freqtrade feasibility
environment. It deploys a research/backtest lab only. It must not be used to
enable live trading, paper trading with real API credentials, order placement,
or `execution/live`.

## Environment

Set:

```bash
export VPS_HOST=root@your.server.ip
export VPS_APP_DIR=/root/apps/btc-eth-dual-quant
```

Then run:

```bash
bash deploy/vps/sync_to_vps.sh
bash deploy/vps/remote_bootstrap.sh
bash deploy/vps/remote_freqtrade_smoke.sh
```

The scripts do not read exchange API keys and do not create `.env` files.

The lab config uses Binance Vision's public market-data endpoint and limits
CCXT market loading to spot markets. This avoids VPS environments where
`api.binance.com`, `fapi.binance.com`, or `dapi.binance.com` are unreachable,
while keeping the smoke test public-data only.

## Safety

- WebUI must not be exposed publicly.
- Use SSH tunnel for any future local WebUI access.
- Do not store API keys on the server.
- Runtime Freqtrade data, logs, sqlite, and backtest results are ignored and
  must not be committed.
