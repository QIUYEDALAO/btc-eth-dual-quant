"""M1B futures funding probe for Freqtrade suitability checks.

This strategy is intentionally tiny and unsuitable for trading. It exists only
to verify whether Freqtrade can run a futures short backtest and expose funding
fee handling in its public-data backtest path. It is not a spot-long plus
perpetual-short arbitrage strategy.
"""

from __future__ import annotations

import pandas as pd
from freqtrade.strategy import IStrategy


class M1BFuturesFundingProbeStrategy(IStrategy):
    timeframe = "1d"
    can_short = True
    startup_candle_count = 5
    minimal_roi = {"0": 100}
    stoploss = -0.99
    process_only_new_candles = True
    use_exit_signal = True
    ignore_roi_if_entry_signal = True

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe["probe_sma"] = dataframe["close"].rolling(3).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[:, "enter_short"] = 0
        dataframe.loc[(dataframe["volume"] > 0) & (dataframe["close"] < dataframe["probe_sma"]), "enter_short"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[:, "exit_short"] = 0
        dataframe.loc[(dataframe["volume"] > 0) & (dataframe["close"] > dataframe["probe_sma"]), "exit_short"] = 1
        return dataframe
