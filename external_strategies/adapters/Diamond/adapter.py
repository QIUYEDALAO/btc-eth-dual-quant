"""Freqtrade 2026.6 identity adapter for the frozen Diamond source."""

from original_source import Diamond as _OriginalDiamond


class Diamond(_OriginalDiamond):
    # Ten-bar horizontal shifts plus the cross comparison require prior rows.
    startup_candle_count = 12
