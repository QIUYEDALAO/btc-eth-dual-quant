# Freqtrade Lab

This directory is a local feasibility lab for evaluating Freqtrade as an
external framework for research, backtesting, dry-run tooling, WebUI hosting,
and strategy-host experiments.

It is not a live-trading deployment. Do not add real exchange credentials, do
not enable exchange trading permissions, and do not expose services publicly.

## Scope

- Stage: M1F Freqtrade feasibility deployment.
- Uses the upstream official Docker image: `freqtradeorg/freqtrade:stable`.
- Upstream repository: https://github.com/freqtrade/freqtrade
- Default Docker command is `version`, not a trading runner.
- The example config is local dry-run/backtest oriented and contains no API
  credentials.
- M1A trend strategy is ported only as a failed-validation reproduction.

## Local Commands

All commands below are optional local checks. They use public market data or
static config validation only.

```bash
cd freqtrade_lab
bash scripts/ft_pull.sh
bash scripts/ft_create_userdir.sh
bash scripts/ft_validate_config.sh
bash scripts/ft_download_spot_data.sh
bash scripts/ft_backtest_m1a_trend.sh
bash scripts/ft_check_futures_capability.sh
```

The repository CI does not run Docker and does not access the network.

## 中文快速入口

- 我想打开 WebUI，看 `WEBUI_中文说明.md`。
- 我想确认安全边界，看 `安全操作清单.md`。
- 我想启动 WebUI，本机先 SSH tunnel，再执行 `bash scripts/ft_webui_local.sh`。
- 我想停止 WebUI，执行 `bash scripts/ft_webui_stop.sh`。
- 我想回测，执行 `bash scripts/ft_backtest_m1a_trend.sh`。
- 我想看部署结论，看 `../reports/m1/M1F_中文验收摘要.md`。

## WebUI Boundary

The example config disables the API/WebUI server. If a future local experiment
enables WebUI, bind only to `127.0.0.1`. On a VPS, access the UI through an SSH
tunnel or VPN. Do not expose it directly to the public internet.

## Safety Boundary

- No live trading.
- No paper trading with real API credentials.
- No `execution/live` directory.
- No order placement or cancellation.
- No API trading permissions.
- No FreqAI or hyperopt rescue of the failed M1A trend leg.
- No downloaded data, logs, sqlite databases, or generated backtest results in
  git.
