from datetime import datetime, timezone
from pathlib import Path

from btc_eth_dual_quant.data.kline_row_conflicts import RawKlineRow
from btc_eth_dual_quant.data.lifecycle_availability import MarketBar


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "config/liquid_spot_lifecycle_event_resolutions_v4.json"
POLICY_PATH = ROOT / "config/liquid_spot_lifecycle_policy_v4.json"
CONTRACT_PATH = ROOT / "config/liquid_spot_universe_contract_v4.json"


def ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()) * 1_000


def five_minute_bar(open_time_ms: int) -> MarketBar:
    return MarketBar(
        symbol="KLAYUSDT",
        interval="5m",
        open_time_ms=open_time_ms,
        close_time_ms=open_time_ms + 299_999,
        open="1",
        high="2",
        low="0.5",
        close="1.5",
        volume="10",
    )


def daily_row(open_time: str, close_time: str, raw_hash_archive: str = "a" * 64) -> RawKlineRow:
    return RawKlineRow.from_fields(
        symbol="KLAYUSDT",
        interval="1d",
        fields=(
            open_time,
            "0.12550000",
            "0.12550000",
            "0.12550000",
            "0.12550000",
            "0.00000000",
            close_time,
            "0.00000000",
            "0",
            "0.00000000",
            "0.00000000",
            "0",
        ),
        line_number=1,
        archive_key="fixture.zip",
        archive_sha256=raw_hash_archive,
        authority="official_monthly_zip",
    )
