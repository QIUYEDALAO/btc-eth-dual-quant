"""Inject a frozen one-pair CCXT market only for offline causal fixtures."""

from __future__ import annotations

import json
import os
from pathlib import Path


if os.environ.get("EXTERNAL_STRATEGY_OFFLINE_CAUSAL") == "1":
    expected = "/harness/offline_markets.json"
    configured = os.environ.get("FROZEN_MARKETS_PATH", expected)
    if configured != expected:
        raise RuntimeError("offline market authority path changed")
    markets = json.loads(Path(configured).read_text(encoding="utf-8"))
    if list(markets) != ["BTC/USDT"] or not markets["BTC/USDT"].get("spot"):
        raise RuntimeError("offline market authority changed")

    import ccxt
    import ccxt.async_support as ccxt_async

    def _sync_load_markets(self, reload=False, params=None):
        self.set_markets(markets)
        return self.markets

    async def _async_load_markets(self, reload=False, params=None):
        self.set_markets(markets)
        return self.markets

    ccxt.binance.load_markets = _sync_load_markets
    ccxt_async.binance.load_markets = _async_load_markets
