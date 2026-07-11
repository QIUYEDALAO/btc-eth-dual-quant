"""Frozen M1G panic-dislocation mean-reversion research strategy."""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy


class M1GPanicDislocationMeanReversion(IStrategy):
    timeframe = "1h"
    can_short = False
    startup_candle_count = 170
    process_only_new_candles = True

    max_open_trades = 1
    stoploss = -0.04
    minimal_roi = {"0": 0.018, "1440": -1}
    trailing_stop = False
    position_adjustment_enable = False
    use_exit_signal = False

    allowed_pairs = ("BTC/USDT", "ETH/USDT")
    reference_window = 168
    minimum_segment_age = 169
    close_return_maximum = -0.024
    absolute_return_multiple_minimum = 3.0
    true_range_multiple_minimum = 2.5
    close_location_maximum = 0.25
    cluster_hours = 24
    global_cooldown_hours = 72

    def informative_pairs(self) -> list[tuple[str, str]]:
        return [(pair, self.timeframe) for pair in self.allowed_pairs]

    @classmethod
    def _event_features(cls, source: pd.DataFrame, prefix: str) -> pd.DataFrame:
        frame = source.copy().sort_values("date").reset_index(drop=True)
        frame["date"] = pd.to_datetime(frame["date"], utc=True)
        gap = frame["date"].diff().ne(pd.Timedelta(hours=1))
        frame["segment_id"] = gap.cumsum()
        frame["segment_age"] = frame.groupby("segment_id").cumcount()

        prior_close = frame["close"].shift(1)
        frame["close_return"] = frame["close"] / prior_close - 1.0
        frame["true_range"] = pd.concat(
            [
                frame["high"] - frame["low"],
                (frame["high"] - prior_close).abs(),
                (frame["low"] - prior_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        by_segment = frame.groupby("segment_id", group_keys=False)
        frame["prior_abs_return_median"] = by_segment["close_return"].transform(
            lambda values: values.abs().shift(1).rolling(cls.reference_window).median()
        )
        frame["prior_true_range_median"] = by_segment["true_range"].transform(
            lambda values: values.shift(1).rolling(cls.reference_window).median()
        )
        frame["absolute_return_multiple"] = (
            frame["close_return"].abs() / frame["prior_abs_return_median"]
        )
        frame["true_range_multiple"] = frame["true_range"] / frame["prior_true_range_median"]
        bar_range = frame["high"] - frame["low"]
        frame["close_location"] = (frame["close"] - frame["low"]) / bar_range.where(bar_range > 0)
        frame["raw_event"] = (
            (frame["segment_age"] >= cls.minimum_segment_age)
            & (frame["close_return"] <= cls.close_return_maximum)
            & (frame["absolute_return_multiple"] >= cls.absolute_return_multiple_minimum)
            & (frame["true_range_multiple"] >= cls.true_range_multiple_minimum)
            & (frame["close_location"] <= cls.close_location_maximum)
        ).fillna(False)

        frame["cluster_event"] = False
        cluster_limit = pd.Timedelta(hours=cls.cluster_hours)
        for _, segment in frame.groupby("segment_id", sort=False):
            last_raw_time = None
            for index in segment.index[segment["raw_event"]]:
                event_time = frame.at[index, "date"]
                if last_raw_time is None or event_time - last_raw_time > cluster_limit:
                    frame.at[index, "cluster_event"] = True
                last_raw_time = event_time

        selected = [
            "date",
            "close_return",
            "absolute_return_multiple",
            "true_range_multiple",
            "close_location",
            "raw_event",
            "cluster_event",
        ]
        return frame[selected].rename(columns={name: f"{prefix}_{name}" for name in selected if name != "date"})

    def _pair_features(self, pair: str, prefix: str) -> pd.DataFrame:
        if not self.dp:
            return pd.DataFrame(columns=["date", f"{prefix}_cluster_event"])
        source = self.dp.get_pair_dataframe(pair=pair, timeframe=self.timeframe)
        if source.empty:
            return pd.DataFrame(columns=["date", f"{prefix}_cluster_event"])
        return self._event_features(source, prefix)

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        result = dataframe.copy()
        result["date"] = pd.to_datetime(result["date"], utc=True)
        result = result.merge(self._pair_features("BTC/USDT", "btc"), on="date", how="left", validate="one_to_one")
        result = result.merge(self._pair_features("ETH/USDT", "eth"), on="date", how="left", validate="one_to_one")

        required = [
            "btc_cluster_event",
            "btc_absolute_return_multiple",
            "btc_true_range_multiple",
            "eth_cluster_event",
            "eth_absolute_return_multiple",
            "eth_true_range_multiple",
        ]
        result["cross_pair_aligned"] = result[required].notna().all(axis=1)
        btc_event = result["cross_pair_aligned"] & result["btc_cluster_event"].astype(bool)
        eth_event = result["cross_pair_aligned"] & result["eth_cluster_event"].astype(bool)
        btc_wins_tie = (
            (result["btc_absolute_return_multiple"] > result["eth_absolute_return_multiple"])
            | (
                (result["btc_absolute_return_multiple"] == result["eth_absolute_return_multiple"])
                & (result["btc_true_range_multiple"] >= result["eth_true_range_multiple"])
            )
        )
        result["event_target"] = "CASH"
        result.loc[btc_event & (~eth_event | btc_wins_tie), "event_target"] = "BTC/USDT"
        result.loc[eth_event & (~btc_event | ~btc_wins_tie), "event_target"] = "ETH/USDT"
        return result

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        result = dataframe.copy()
        pair = metadata.get("pair")
        result["enter_long"] = 0
        result["enter_tag"] = ""
        if pair in self.allowed_pairs:
            selected = result["cross_pair_aligned"] & (result["event_target"] == pair)
            result.loc[selected, "enter_long"] = 1
            result.loc[selected, "enter_tag"] = "m1g_panic_dislocation"
        return result

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        result = dataframe.copy()
        result["exit_long"] = 0
        return result

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> bool:
        del pair, order_type, amount, rate, time_in_force, entry_tag, side, kwargs
        threshold = current_time - timedelta(hours=self.global_cooldown_hours)
        closed = Trade.get_trades_proxy(is_open=False, close_date=current_time)
        return not any(
            getattr(trade, "close_date_utc", getattr(trade, "close_date", None)) is not None
            and getattr(trade, "close_date_utc", getattr(trade, "close_date", None)) > threshold
            for trade in closed
        )
