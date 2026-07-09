"""M1A trend validation port for Freqtrade feasibility checks.

This strategy mirrors the fixed BTC/ETH 1d spot trend rule that already failed
the project's self-managed M1A validation. It is not approved for live use,
paper use with real credentials, hyperopt, leverage, futures, FreqAI, or rescue
parameter tuning. It exists only to check whether Freqtrade can host an
equivalent research strategy skeleton.

Freqtrade's backtest fill model is framework-defined and is not asserted here
to be identical to the project's strict next-open time-semantics checks.
"""

from __future__ import annotations

from functools import reduce

import pandas as pd
from freqtrade.strategy import IStrategy


class M1ATrendValidationStrategy(IStrategy):
    timeframe = "1d"
    can_short = False
    startup_candle_count = 220
    minimal_roi = {"0": 100}
    stoploss = -0.99
    process_only_new_candles = True
    use_exit_signal = True
    ignore_roi_if_entry_signal = True

    regime_window = 200
    entry_window = 55
    exit_window = 20
    atr_window = 20
    atr_stop_mult = 2.0

    @staticmethod
    def _atr(dataframe: pd.DataFrame, window: int) -> pd.Series:
        previous_close = dataframe["close"].shift(1)
        ranges = pd.concat(
            [
                dataframe["high"] - dataframe["low"],
                (dataframe["high"] - previous_close).abs(),
                (dataframe["low"] - previous_close).abs(),
            ],
            axis=1,
        )
        return ranges.max(axis=1).rolling(window).mean()

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe["sma_200"] = dataframe["close"].rolling(self.regime_window).mean()
        dataframe["prior_donchian_high_55"] = dataframe["high"].shift(1).rolling(self.entry_window).max()
        dataframe["prior_donchian_low_20"] = dataframe["low"].shift(1).rolling(self.exit_window).min()
        dataframe["atr_20"] = self._atr(dataframe, self.atr_window)
        dataframe["atr_stop_reference"] = dataframe["close"] - self.atr_stop_mult * dataframe["atr_20"]
        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        allowed_pairs = {"BTC/USDT", "ETH/USDT"}
        pair = metadata.get("pair")
        conditions = [
            dataframe["volume"] > 0,
            dataframe["close"] > dataframe["sma_200"],
            dataframe["close"] > dataframe["prior_donchian_high_55"],
        ]
        dataframe.loc[:, "enter_long"] = 0
        if pair in allowed_pairs:
            dataframe.loc[reduce(lambda left, right: left & right, conditions), "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        conditions = [
            dataframe["volume"] > 0,
            dataframe["close"] < dataframe["prior_donchian_low_20"],
        ]
        dataframe.loc[:, "exit_long"] = 0
        dataframe.loc[reduce(lambda left, right: left & right, conditions), "exit_long"] = 1
        return dataframe
