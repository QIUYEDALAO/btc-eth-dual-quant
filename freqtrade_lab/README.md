# Freqtrade Lab

This directory is the project's primary framework for single-leg public-data
research, backtesting, time-series diagnostics, and local-only WebUI access.

It is not a live-trading deployment. Do not add real exchange credentials, do
not enable exchange trading permissions, and do not expose services publicly.

## Scope

- Stage: Freqtrade primary-framework hardening.
- Uses the upstream official Docker image pinned to release and digest:
  `freqtradeorg/freqtrade:2026.6@sha256:d451af021d5e08b70580c0eea5848534e9846b57391b34821c0a5814416397e6`.
- Upstream repository: https://github.com/freqtrade/freqtrade
- Default Docker command is `version`, not a trading runner.
- The example config is local dry-run/backtest oriented and contains no API
  credentials.
- `runtime-manifest.json` is the sanitized runtime/provenance contract.
- M1A trend strategy is frozen as a historical failed-validation reproduction.
- M1C BTC/ETH/cash rotation is the active fixed-rule research candidate. Its
  design contract is `m1c-btc-eth-rotation-contract.json`.
- New single-leg strategy research belongs only in `user_data/strategies/`.

## Local Commands

All commands below are optional local checks. They use public market data or
static config validation only.

```bash
cd freqtrade_lab
bash scripts/ft_pull.sh
bash scripts/ft_verify_runtime.sh
bash scripts/ft_research.sh download-data --help
bash scripts/ft_research.sh list-data --help
bash scripts/ft_research.sh backtesting --help
bash scripts/ft_research.sh lookahead-analysis --help
bash scripts/ft_research.sh recursive-analysis --help
bash scripts/ft_research.sh webserver
```

M1C public-data research commands are deliberately separate from any runtime
bot command:

```bash
bash scripts/ft_download_m1c.sh
bash scripts/ft_backtest_m1c.sh
bash scripts/ft_lookahead_m1c.sh
bash scripts/ft_recursive_m1c.sh
```

They use `config.m1c-rotation-research.json`, which contains no exchange
credentials and keeps the API server disabled. Generated data and results stay
under ignored Freqtrade runtime directories.

The public futures-leg cross-check remains a single-leg capability probe and
must not be used as spot-long plus perpetual-short portfolio evidence:

```bash
bash scripts/ft_futures_probe.sh
```

Normal pull-request CI is static and does not access public market data. The
manual public-data smoke workflow uses no secrets and uploads no runtime data.

## 中文快速入口

- 我想打开 WebUI，看 `WEBUI_中文说明.md`。
- 我想确认安全边界，看 `安全操作清单.md`。
- 我想启动 WebUI，本机先 SSH tunnel，再执行 `bash scripts/ft_webui_local.sh`。
- 我想停止 WebUI，执行 `bash scripts/ft_webui_stop.sh`。
- 我想回测，执行 `bash scripts/ft_research.sh backtesting ...`。
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
