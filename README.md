# BTC/ETH Dual Quant Research System

This repository is a Freqtrade-first research system with an independent data
and time-semantics audit layer.

## Architecture

- Freqtrade is the primary framework for single-leg strategy research, public
  data download, backtesting, and WebUI.
- M0 Python owns data lineage, append-only raw storage, DuckDB queries, data
  quality, funding cadence, and cost evidence.
- Python time-semantic checks independently enforce no future data and no
  same-bar close fills.
- The custom funding-arbitrage module is offline accounting only for the
  spot-long plus perpetual-short structure Freqtrade cannot natively combine.
- The self-managed M1A trend engine is frozen as a historical
  failed-validation artifact.

See
`docs/superpowers/specs/2026-07-10-freqtrade-first-system-hardening-design.md`
and `docs/decisions/ADR-0006-freqtrade-first-with-audit-sidecar.md`.

## Current Status

- M0 read-only data engineering: accepted; audit revalidation required for two
  identified methodology gaps.
- M1A trend: failed_validation.
- M1B funding arbitrage: failed_validation; historical numerical evidence is
  pending event-time revalidation.
- Freqtrade Lab: accepted only as a research/backtest/WebUI framework.
- M2, live trading, paper trading with real API, order placement, cancellation,
  and `execution/live`: prohibited.

## Validation

```bash
PYTHONPATH=.deps:src python3 -m unittest discover -s tests -v
PYTHONPATH=.deps:src python3 -m compileall src scripts
bash scripts/project_validate.sh
```

No validation command requires an API key or private exchange data.
