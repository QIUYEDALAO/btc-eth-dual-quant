"""Commission refresh, round-trip cost, and funding-payback threshold logic."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class CommissionRate:
    maker: Decimal
    taker: Decimal
    discount: Decimal = Decimal("0")
    commission_asset: str | None = None


@dataclass(frozen=True)
class RoundTripCost:
    spot_fee_rate: Decimal
    futures_fee_rate: Decimal
    slippage_per_side: Decimal
    total_rate: Decimal


@dataclass(frozen=True)
class PaybackResult:
    expected_funding_income_rate: Decimal
    roundtrip_cost_rate: Decimal
    payback_ratio: Decimal
    passes: bool


@dataclass(frozen=True)
class RealFeeSnapshot:
    spot: CommissionRate
    futures: CommissionRate
    roundtrip_cost: RoundTripCost


def _decimal(value: Any, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    return Decimal(str(value))


def parse_spot_commission(payload: dict[str, Any]) -> CommissionRate:
    """Parse Binance spot account commission payload variants conservatively."""

    standard = payload.get("standardCommission", payload)
    maker = standard.get("maker", payload.get("makerCommissionRate", payload.get("maker", "0")))
    taker = standard.get("taker", payload.get("takerCommissionRate", payload.get("taker", "0")))
    discount_payload = payload.get("discount", {})
    discount = (
        discount_payload.get("discount", payload.get("discount", "0"))
        if isinstance(discount_payload, dict)
        else discount_payload
    )
    commission_asset = payload.get("commissionAsset") or payload.get("discountAsset")
    return CommissionRate(_decimal(maker), _decimal(taker), _decimal(discount), commission_asset)


def parse_futures_commission(payload: dict[str, Any]) -> CommissionRate:
    return CommissionRate(
        maker=_decimal(payload.get("makerCommissionRate", payload.get("maker"))),
        taker=_decimal(payload.get("takerCommissionRate", payload.get("taker"))),
        discount=_decimal(payload.get("discount")),
        commission_asset=payload.get("commissionAsset"),
    )


def compute_roundtrip_cost(
    spot_taker_fee: Decimal | str | float,
    futures_taker_fee: Decimal | str | float,
    slippage_per_side: Decimal | str | float,
) -> RoundTripCost:
    """Spot buy/sell + futures open/close + four slippage legs."""

    spot = _decimal(spot_taker_fee)
    futures = _decimal(futures_taker_fee)
    slippage = _decimal(slippage_per_side)
    total = (spot * 2) + (futures * 2) + (slippage * 4)
    return RoundTripCost(spot, futures, slippage, total)


def refresh_real_fee_snapshot(
    collector: Any,
    commission_record: Any,
    spot_symbol: str,
    futures_symbol: str,
    slippage_per_side: Decimal | str | float,
) -> RealFeeSnapshot:
    """Read current commissions through M0 read-only collectors and compute cost baseline."""

    spot_envelope = collector.spot_account_commission(commission_record, spot_symbol)
    futures_envelope = collector.futures_commission_rate(commission_record, futures_symbol)
    spot = parse_spot_commission(spot_envelope.payload)
    futures = parse_futures_commission(futures_envelope.payload)
    roundtrip = compute_roundtrip_cost(spot.taker, futures.taker, slippage_per_side)
    return RealFeeSnapshot(spot=spot, futures=futures, roundtrip_cost=roundtrip)


def funding_payback_threshold(
    annualized_funding_rate: Decimal | str | float,
    expected_hold_days: Decimal | str | float,
    roundtrip_cost_rate: Decimal | str | float,
    min_payback_ratio: Decimal | str | float = Decimal("2.0"),
) -> PaybackResult:
    income = _decimal(annualized_funding_rate) * (_decimal(expected_hold_days) / Decimal("365"))
    cost = _decimal(roundtrip_cost_rate)
    ratio = Decimal("Infinity") if cost == 0 else income / cost
    threshold = _decimal(min_payback_ratio)
    return PaybackResult(income, cost, ratio, ratio >= threshold)
