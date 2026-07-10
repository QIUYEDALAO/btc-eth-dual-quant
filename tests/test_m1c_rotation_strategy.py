from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import types
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from btc_eth_dual_quant.audit.m1c_time_semantics import (
    RotationEvent,
    validate_rotation_event,
    validate_rotation_switch,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from m1c_freqtrade_runtime_check import validate_runtime_outputs

STRATEGY_PATH = ROOT / "freqtrade_lab" / "user_data" / "strategies" / "BTCETHRelativeStrengthRotation.py"


def load_strategy_class():
    strategy_module = types.ModuleType("freqtrade.strategy")
    strategy_module.IStrategy = object
    freqtrade_module = types.ModuleType("freqtrade")
    freqtrade_module.strategy = strategy_module
    sys.modules["freqtrade"] = freqtrade_module
    sys.modules["freqtrade.strategy"] = strategy_module
    spec = importlib.util.spec_from_file_location("m1c_rotation_strategy", STRATEGY_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BTCETHRelativeStrengthRotation


class FakeDataProvider:
    def __init__(self, frames: dict[str, pd.DataFrame]) -> None:
        self.frames = frames

    def get_pair_dataframe(self, pair: str, timeframe: str) -> pd.DataFrame:
        if timeframe != "1d":
            raise AssertionError(f"unexpected timeframe: {timeframe}")
        return self.frames[pair].copy()


def frame(closes: list[float], start: str = "2025-11-10") -> pd.DataFrame:
    dates = pd.date_range(start=start, periods=len(closes), freq="1D", tz="UTC")
    return pd.DataFrame(
        {
            "date": dates,
            "open": closes,
            "high": [value * 1.01 for value in closes],
            "low": [value * 0.99 for value in closes],
            "close": closes,
            "volume": [100.0] * len(closes),
        }
    )


class M1CRotationStrategyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy_class = load_strategy_class()

    def strategy(self, btc: pd.DataFrame, eth: pd.DataFrame):
        strategy = self.strategy_class()
        strategy.dp = FakeDataProvider({"BTC/USDT": btc, "ETH/USDT": eth})
        return strategy

    def test_fixed_safety_and_capital_contract(self) -> None:
        strategy = self.strategy_class()
        self.assertFalse(strategy.can_short)
        self.assertEqual(strategy.max_open_trades, 1)
        self.assertEqual(strategy.stoploss, -0.20)
        self.assertEqual(strategy.minimal_roi, {"0": 100.0})
        self.assertFalse(strategy.trailing_stop)
        self.assertFalse(strategy.position_adjustment_enable)

        config = json.loads(
            (ROOT / "freqtrade_lab" / "user_data" / "configs" / "config.m1c-rotation-research.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(config["max_open_trades"], 1)
        self.assertEqual(config["stake_amount"], "unlimited")
        self.assertEqual(config["tradable_balance_ratio"], 0.5)
        self.assertFalse(config["api_server"]["enabled"])
        self.assertNotIn("key", config["exchange"])
        self.assertNotIn("secret", config["exchange"])

    def test_tie_chooses_btc_and_only_sunday_signals(self) -> None:
        closes = [100.0 + i for i in range(240)]
        btc = frame(closes)
        eth = frame(closes)
        strategy = self.strategy(btc, eth)

        analyzed = strategy.populate_indicators(btc, {"pair": "BTC/USDT"})
        btc_signals = strategy.populate_entry_trend(analyzed, {"pair": "BTC/USDT"})
        eth_signals = strategy.populate_entry_trend(analyzed, {"pair": "ETH/USDT"})

        eligible = analyzed["btc_eligible"] & analyzed["eth_eligible"]
        self.assertTrue((analyzed.loc[eligible, "rotation_target"] == "BTC/USDT").all())
        self.assertTrue((btc_signals.loc[btc_signals["enter_long"] == 1, "date"].dt.weekday == 6).all())
        self.assertEqual(int(eth_signals["enter_long"].sum()), 0)

    def test_stronger_eth_is_unique_winner(self) -> None:
        btc = frame([100.0 + i * 0.5 for i in range(240)])
        eth = frame([100.0 + i * 1.5 for i in range(240)])
        strategy = self.strategy(btc, eth)
        analyzed = strategy.populate_indicators(btc, {"pair": "BTC/USDT"})
        latest_sunday = analyzed[(analyzed["date"].dt.weekday == 6) & analyzed["cross_pair_aligned"]].iloc[-1]
        self.assertEqual(latest_sunday["rotation_target"], "ETH/USDT")

    def test_ineligible_or_missing_cross_pair_data_selects_cash(self) -> None:
        descending = [500.0 - i for i in range(240)]
        btc = frame(descending)
        eth = frame(descending)
        strategy = self.strategy(btc, eth)
        analyzed = strategy.populate_indicators(btc, {"pair": "BTC/USDT"})
        self.assertTrue((analyzed.loc[analyzed.index[199]:, "rotation_target"] == "CASH").all())

        missing_eth = eth.drop(index=eth.index[-1])
        strategy = self.strategy(btc, missing_eth)
        analyzed = strategy.populate_indicators(btc, {"pair": "BTC/USDT"})
        self.assertFalse(bool(analyzed.iloc[-1]["cross_pair_aligned"]))
        self.assertEqual(analyzed.iloc[-1]["rotation_target"], "CASH")

    def test_future_row_does_not_change_prior_indicators(self) -> None:
        btc = frame([100.0 + i for i in range(240)])
        eth = frame([100.0 + i * 1.1 for i in range(240)])
        base = self.strategy(btc, eth).populate_indicators(btc, {"pair": "BTC/USDT"})

        future_date = btc.iloc[-1]["date"] + pd.Timedelta(days=1)
        future_btc = pd.concat([btc, frame([1_000_000.0], start=str(future_date.date()))], ignore_index=True)
        future_eth = pd.concat([eth, frame([2_000_000.0], start=str(future_date.date()))], ignore_index=True)
        extended = self.strategy(future_btc, future_eth).populate_indicators(
            future_btc, {"pair": "BTC/USDT"}
        )
        columns = ["btc_sma", "btc_return", "eth_sma", "eth_return", "rotation_target"]
        pd.testing.assert_series_equal(base.iloc[-1][columns], extended.iloc[-2][columns], check_names=False)

    def test_exit_signal_rotates_old_pair_or_moves_to_cash(self) -> None:
        btc = frame([100.0 + i * 0.5 for i in range(240)])
        eth = frame([100.0 + i * 1.5 for i in range(240)])
        strategy = self.strategy(btc, eth)
        analyzed = strategy.populate_indicators(btc, {"pair": "BTC/USDT"})
        exits = strategy.populate_exit_trend(analyzed, {"pair": "BTC/USDT"})
        sunday_eth_targets = (analyzed["date"].dt.weekday == 6) & (analyzed["rotation_target"] == "ETH/USDT")
        self.assertTrue((exits.loc[sunday_eth_targets, "exit_long"] == 1).all())


class M1CTimeSemanticsTests(unittest.TestCase):
    def test_sunday_close_scores_and_monday_fill_are_valid(self) -> None:
        sunday_open = datetime(2026, 7, 5, tzinfo=UTC)
        monday_open = sunday_open + timedelta(days=1)
        event = RotationEvent(
            signal_candle_open=sunday_open,
            signal_candle_close=monday_open,
            btc_score_time=monday_open,
            eth_score_time=monday_open,
            effective_fill_time=monday_open,
        )
        self.assertEqual(validate_rotation_event(event), [])

    def test_same_close_fill_and_misaligned_scores_are_rejected(self) -> None:
        sunday_open = datetime(2026, 7, 5, tzinfo=UTC)
        monday_open = sunday_open + timedelta(days=1)
        event = RotationEvent(
            signal_candle_open=sunday_open,
            signal_candle_close=monday_open,
            btc_score_time=monday_open,
            eth_score_time=monday_open - timedelta(days=1),
            effective_fill_time=sunday_open,
        )
        failures = validate_rotation_event(event)
        self.assertTrue(any("same UTC timestamp" in failure for failure in failures))
        self.assertTrue(any("next 1d open" in failure for failure in failures))

    def test_rotation_switch_requires_same_timestamp(self) -> None:
        monday = datetime(2026, 7, 6, tzinfo=UTC)
        self.assertEqual(validate_rotation_switch(monday, monday), [])
        self.assertNotEqual(validate_rotation_switch(monday, monday + timedelta(days=1)), [])


class M1CRuntimeOutputTests(unittest.TestCase):
    def _write_fixture(self, root: Path, second_open: str) -> tuple[Path, Path, Path]:
        results = root / "results"
        results.mkdir()
        payload = {
            "strategy": {
                "BTCETHRelativeStrengthRotation": {
                    "trades": [
                        {
                            "pair": "BTC/USDT",
                            "open_date": "2024-01-01 00:00:00+00:00",
                            "close_date": "2024-02-05 00:00:00+00:00",
                        },
                        {
                            "pair": "ETH/USDT",
                            "open_date": second_open,
                            "close_date": "2024-03-04 00:00:00+00:00",
                        },
                    ]
                }
            }
        }
        with ZipFile(results / "m1c.zip", "w", ZIP_DEFLATED) as archive:
            archive.writestr("m1c.json", json.dumps(payload))
            archive.writestr("m1c_config.json", "{}")
        lookahead = root / "lookahead.csv"
        lookahead.write_text(
            "filename,strategy,has_bias,total_signals,biased_entry_signals,biased_exit_signals,biased_indicators\n"
            "strategy.py,BTCETHRelativeStrengthRotation,False,20,0,0,\n",
            encoding="utf-8",
        )
        recursive = root / "recursive.log"
        recursive.write_text(
            "No variance on indicator(s) found due to recursive formula.\n"
            "No lookahead bias on indicators found.\n",
            encoding="utf-8",
        )
        return results, lookahead, recursive

    def test_runtime_fixture_accepts_same_open_switch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write_fixture(Path(tmp), "2024-02-05 00:00:00+00:00")
            self.assertEqual(validate_runtime_outputs(*paths), [])

    def test_runtime_fixture_rejects_delayed_switch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write_fixture(Path(tmp), "2024-02-12 00:00:00+00:00")
            failures = validate_runtime_outputs(*paths)
            self.assertTrue(any("same-open" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
