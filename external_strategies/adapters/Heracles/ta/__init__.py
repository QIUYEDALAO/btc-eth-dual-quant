"""Minimal source-compatible ``ta`` package required by frozen Heracles."""

from __future__ import annotations

import pandas as pd


class _Volatility:
    @staticmethod
    def keltner_channel_wband(high, low, close, window=20, window_atr=10, fillna=False, original_version=True):
        if not original_version:
            raise ValueError("Heracles freezes original_version=True")
        middle = ((high + low + close) / 3.0).rolling(window, min_periods=window).mean()
        upper = (((4.0 * high) - (2.0 * low) + close) / 3.0).rolling(window, min_periods=window).mean()
        lower = (((-2.0 * high) + (4.0 * low) + close) / 3.0).rolling(window, min_periods=window).mean()
        result = ((upper - lower) / middle) * 100.0
        return result.fillna(0.0) if fillna else result

    @staticmethod
    def donchian_channel_pband(high, low, close, window=10, offset=0, fillna=False):
        upper = high.rolling(window, min_periods=window).max()
        lower = low.rolling(window, min_periods=window).min()
        result = (close - lower) / (upper - lower)
        if offset:
            result = result.shift(offset)
        return result.fillna(0.0) if fillna else result


volatility = _Volatility()
