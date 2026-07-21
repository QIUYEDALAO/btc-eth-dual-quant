"""Freqtrade 2026.6 identity adapter for the frozen Strategy001 source."""

from original_source import Strategy001 as _OriginalStrategy001


class Strategy001(_OriginalStrategy001):
    # The source computes EMA100 but leaves the Freqtrade warmup at zero.
    startup_candle_count = 100
