"""Freqtrade 2026.6 identity adapter for the frozen Heracles source."""

from original_source import Heracles as _OriginalHeracles


class Heracles(_OriginalHeracles):
    # The longest source dependency is the 20-bar indicator plus a 15-bar lag.
    startup_candle_count = 40
