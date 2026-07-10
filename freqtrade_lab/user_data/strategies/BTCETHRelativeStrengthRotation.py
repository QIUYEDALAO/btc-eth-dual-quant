"""Fixed M1C BTC/ETH/cash weekly rotation research strategy.

This strategy is for public-data Freqtrade research only. Its parameters are
locked by the M1C P1 design contract. It does not implement execution, API
access, leverage, shorting, position adjustment, or parameter optimization.
"""

from __future__ import annotations

import pandas as pd
from freqtrade.strategy import IStrategy


class BTCETHRelativeStrengthRotation(IStrategy):
    timeframe = "1d"
    can_short = False
    startup_candle_count = 200
    process_only_new_candles = True

    max_open_trades = 1
    stoploss = -0.20
    minimal_roi = {"0": 100.0}
    trailing_stop = False
    position_adjustment_enable = False
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    sma_window = 200
    relative_window = 90
    allowed_pairs = ("BTC/USDT", "ETH/USDT")

    def informative_pairs(self) -> list[tuple[str, str]]:
        return [(pair, self.timeframe) for pair in self.allowed_pairs]

    def _pair_features(self, pair: str, prefix: str) -> pd.DataFrame:
        if not self.dp:
            return pd.DataFrame(columns=["date", f"{prefix}_close", f"{prefix}_sma", f"{prefix}_return"])

        source = self.dp.get_pair_dataframe(pair=pair, timeframe=self.timeframe).copy()
        if source.empty:
            return pd.DataFrame(columns=["date", f"{prefix}_close", f"{prefix}_sma", f"{prefix}_return"])

        source["date"] = pd.to_datetime(source["date"], utc=True)
        source[f"{prefix}_close"] = source["close"]
        source[f"{prefix}_sma"] = source["close"].rolling(self.sma_window).mean()
        source[f"{prefix}_return"] = source["close"] / source["close"].shift(self.relative_window) - 1.0
        return source[["date", f"{prefix}_close", f"{prefix}_sma", f"{prefix}_return"]]

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        result = dataframe.copy()
        result["date"] = pd.to_datetime(result["date"], utc=True)

        btc = self._pair_features("BTC/USDT", "btc")
        eth = self._pair_features("ETH/USDT", "eth")
        result = result.merge(btc, on="date", how="left", validate="one_to_one")
        result = result.merge(eth, on="date", how="left", validate="one_to_one")

        required = [
            "btc_close",
            "btc_sma",
            "btc_return",
            "eth_close",
            "eth_sma",
            "eth_return",
        ]
        result["cross_pair_aligned"] = result[required].notna().all(axis=1)
        result["btc_eligible"] = (
            result["cross_pair_aligned"]
            & (result["btc_close"] > result["btc_sma"])
            & (result["btc_return"] > 0.0)
        )
        result["eth_eligible"] = (
            result["cross_pair_aligned"]
            & (result["eth_close"] > result["eth_sma"])
            & (result["eth_return"] > 0.0)
        )

        btc_wins = result["btc_eligible"] & (
            ~result["eth_eligible"] | (result["btc_return"] >= result["eth_return"])
        )
        eth_wins = result["eth_eligible"] & (
            ~result["btc_eligible"] | (result["eth_return"] > result["btc_return"])
        )

        result["rotation_target"] = "CASH"
        result.loc[btc_wins, "rotation_target"] = "BTC/USDT"
        result.loc[eth_wins, "rotation_target"] = "ETH/USDT"
        result["weekly_decision"] = result["date"].dt.weekday == 6
        return result

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        result = dataframe.copy()
        pair = metadata.get("pair")
        result["enter_long"] = 0
        if pair in self.allowed_pairs:
            entry = (
                result["weekly_decision"]
                & result["cross_pair_aligned"]
                & (result["rotation_target"] == pair)
                & (result["volume"] > 0)
            )
            result.loc[entry, ["enter_long", "enter_tag"]] = (1, "weekly_rotation")
        return result

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        result = dataframe.copy()
        pair = metadata.get("pair")
        result["exit_long"] = 0
        if pair in self.allowed_pairs:
            exit_signal = (
                result["weekly_decision"]
                & (result["rotation_target"] != pair)
                & (result["volume"] > 0)
            )
            result.loc[exit_signal, ["exit_long", "exit_tag"]] = (1, "weekly_rotation")
        return result
