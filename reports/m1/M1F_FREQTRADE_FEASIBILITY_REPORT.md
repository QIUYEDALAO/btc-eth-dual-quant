# M1F Freqtrade Feasibility Report

Generated UTC: 2026-07-09T05:45:00Z

## Status

- Status: under_review
- Scope: Freqtrade feasibility deployment only
- No live trading
- No paper trading with real API
- No execution/live
- No order placement
- No API trading permissions
- Freqtrade source: upstream official Docker image `freqtradeorg/freqtrade:stable` and GitHub repository https://github.com/freqtrade/freqtrade

## Checklist

- Docker compose deployment: pass
- User data structure: pass
- Dry-run config safety: pass
- No secrets committed: pass
- M1A trend strategy ported: pass
- M1A trend strategy status: failed_validation, not eligible for M2
- Backtest command available: pass
- Futures capability checked: pass
- Funding-rate data availability checked: under_review

## Data And Config

- Strategy pairs: BTC/USDT, ETH/USDT
- Trading mode in example config: spot
- Example config: `freqtrade_lab/user_data/configs/config.dryrun.example.json`
- Docker compose: `freqtrade_lab/docker-compose.yml`
- Local commands use Docker Compose and are optional.
- CI performs static checks only and does not require Docker, network access, private data, or downloaded Freqtrade data.

## Capability Summary

- Can support spot long-only trend: yes
- Can directly support spot-long + perp-short funding arbitrage in one bot: unknown

## VPS Deployment

- VPS sync script: pass
- Remote docker install script: pass
- Remote project validation: pass
- Remote docker smoke: pass
- Freqtrade image pull: pass
- Freqtrade show-config: pass
- Public data download: pass
- Freqtrade M1A backtest smoke: pass
- Smoke timerange: 20240101-
- Public market-data endpoint override: `https://data-api.binance.vision/api/v3`
- CCXT market loading: spot-only
- WebUI exposed publicly: no
- API key used: no
- Live trading enabled: no
- Runtime artifacts committed: no

## Chinese Operator Guide

- WEBUI_中文说明.md: pass
- 安全操作清单.md: pass
- M1F_中文验收摘要.md: pass
- WebUI local-only start script: pass
- WebUI stop script: pass

## M1A Strategy Port Notes

The Freqtrade strategy ports the fixed M1A trend rules: 1d timeframe, close above SMA(200), close above prior 55-day Donchian high for entry, close below prior 20-day Donchian low for exit, ATR(20), and a 2x ATR reference. It does not alter parameters, add symbols, add smaller timeframes, enable hyperopt, enable futures, or enable leverage.

Freqtrade's backtest fill model is framework-defined. The project must not assume it is identical to the existing M1A next-open time-semantics validation without a dedicated comparison.

## Gaps / Limitations

- Freqtrade has not been accepted as a trading system.
- M1A trend remains failed_validation and is not eligible for M2.
- Funding-rate arbitrage requires separate gap analysis before any M1B-style validation.
- Docker commands are optional local checks and were not required for CI.
- No live credentials are present or allowed.

## Recommendation

- Use Freqtrade as a candidate framework if feasibility remains positive.
- Do not use Freqtrade deployment as proof of strategy profitability.
- Do not enable live trading until a later explicitly approved stage.
- Continue funding-arbitrage suitability review before any strategy approval.

## Not Investment Advice

This report is an engineering feasibility artifact, not investment advice. No result here approves trading with real funds.
