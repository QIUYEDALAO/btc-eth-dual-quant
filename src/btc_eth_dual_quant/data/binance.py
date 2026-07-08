"""Read-only Binance REST collectors for M0.

This module intentionally has no order, cancel, position-changing, or execution
methods. Signed requests are limited to read-only archival/cost endpoints.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .registry import RegistryRecord
from .storage import AppendOnlyRawStore, RawEnvelope


SPOT_BASE_URL = "https://api.binance.com"
FUTURES_BASE_URL = "https://fapi.binance.com"

TRADING_ENDPOINT_FRAGMENTS = (
    "/order",
    "/batchOrders",
    "/countdownCancelAll",
    "/positionSide",
    "/leverage",
    "/marginType",
)


class BinanceClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class BinanceCredentials:
    api_key: str
    api_secret: str

    @classmethod
    def from_env(cls) -> "BinanceCredentials":
        api_key = os.environ.get("BINANCE_API_KEY", "")
        api_secret = os.environ.get("BINANCE_API_SECRET", "")
        if not api_key or not api_secret:
            raise BinanceClientError(
                "BINANCE_API_KEY and BINANCE_API_SECRET are required for signed read-only endpoints."
            )
        return cls(api_key=api_key, api_secret=api_secret)


class BinanceReadOnlyRestClient:
    """Small stdlib REST client for public and signed read-only GET endpoints."""

    def __init__(
        self,
        spot_base_url: str = SPOT_BASE_URL,
        futures_base_url: str = FUTURES_BASE_URL,
        credentials: BinanceCredentials | None = None,
        timeout_sec: int = 20,
        retries: int = 3,
        retry_sleep_sec: float = 0.5,
    ) -> None:
        self.spot_base_url = spot_base_url.rstrip("/")
        self.futures_base_url = futures_base_url.rstrip("/")
        self.credentials = credentials
        self.timeout_sec = timeout_sec
        self.retries = retries
        self.retry_sleep_sec = retry_sleep_sec

    def get(
        self,
        market: str,
        path: str,
        params: dict[str, Any] | None = None,
        signed: bool = False,
    ) -> Any:
        self._assert_read_only(path)
        params = {k: v for k, v in (params or {}).items() if v is not None}
        headers: dict[str, str] = {}
        if signed:
            credentials = self.credentials or BinanceCredentials.from_env()
            params.setdefault("timestamp", int(time.time() * 1000))
            params.setdefault("recvWindow", 5000)
            query = urlencode(params)
            signature = hmac.new(
                credentials.api_secret.encode("utf-8"),
                query.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            params["signature"] = signature
            headers["X-MBX-APIKEY"] = credentials.api_key

        base_url = self.spot_base_url if market == "spot" else self.futures_base_url
        url = f"{base_url}{path}"
        query = urlencode(params)
        if query:
            url = f"{url}?{query}"
        request = Request(url, headers=headers, method="GET")
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                with urlopen(request, timeout=self.timeout_sec) as response:  # nosec - fixed HTTPS API URLs.
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt < self.retries - 1:
                    time.sleep(self.retry_sleep_sec)
        assert last_error is not None
        raise last_error

    @staticmethod
    def _assert_read_only(path: str) -> None:
        lowered = path.lower()
        for fragment in TRADING_ENDPOINT_FRAGMENTS:
            if fragment.lower() in lowered:
                raise BinanceClientError(f"Trading endpoint is not allowed in M0: {path}")


class BinanceReadOnlyCollector:
    """Registry-aware collector that persists every raw response append-only."""

    def __init__(self, client: BinanceReadOnlyRestClient, store: AppendOnlyRawStore) -> None:
        self.client = client
        self.store = store

    def _collect(
        self,
        record: RegistryRecord,
        market: str,
        path: str,
        params: dict[str, Any],
        signed: bool = False,
    ) -> RawEnvelope:
        payload = self.client.get(market=market, path=path, params=params, signed=signed)
        return self.store.append(
            dataset=record.name,
            source=record.source,
            endpoint=f"GET {path}",
            params=params,
            payload=payload,
        )

    def spot_klines(self, record: RegistryRecord, symbol: str, interval: str, **params: Any) -> RawEnvelope:
        return self._collect(record, "spot", "/api/v3/klines", {"symbol": symbol, "interval": interval, **params})

    def um_futures_klines(self, record: RegistryRecord, symbol: str, interval: str, **params: Any) -> RawEnvelope:
        return self._collect(record, "futures", "/fapi/v1/klines", {"symbol": symbol, "interval": interval, **params})

    def funding_rate_history(self, record: RegistryRecord, symbol: str, **params: Any) -> RawEnvelope:
        return self._collect(record, "futures", "/fapi/v1/fundingRate", {"symbol": symbol, **params})

    def premium_index(self, record: RegistryRecord, symbol: str | None = None) -> RawEnvelope:
        return self._collect(record, "futures", "/fapi/v1/premiumIndex", {"symbol": symbol})

    def funding_info(self, record: RegistryRecord) -> RawEnvelope:
        return self._collect(record, "futures", "/fapi/v1/fundingInfo", {})

    def mark_price_klines(self, record: RegistryRecord, symbol: str, interval: str, **params: Any) -> RawEnvelope:
        return self._collect(record, "futures", "/fapi/v1/markPriceKlines", {"symbol": symbol, "interval": interval, **params})

    def index_price_klines(self, record: RegistryRecord, pair: str, interval: str, **params: Any) -> RawEnvelope:
        return self._collect(record, "futures", "/fapi/v1/indexPriceKlines", {"pair": pair, "interval": interval, **params})

    def premium_index_klines(self, record: RegistryRecord, symbol: str, interval: str, **params: Any) -> RawEnvelope:
        return self._collect(record, "futures", "/fapi/v1/premiumIndexKlines", {"symbol": symbol, "interval": interval, **params})

    def open_interest_hist(self, record: RegistryRecord, symbol: str, period: str, **params: Any) -> RawEnvelope:
        return self._collect(record, "futures", "/futures/data/openInterestHist", {"symbol": symbol, "period": period, **params})

    def funding_income(self, record: RegistryRecord, symbol: str | None = None, **params: Any) -> RawEnvelope:
        return self._collect(
            record,
            "futures",
            "/fapi/v1/income",
            {"incomeType": "FUNDING_FEE", "symbol": symbol, **params},
            signed=True,
        )

    def spot_account_commission(self, record: RegistryRecord, symbol: str) -> RawEnvelope:
        return self._collect(record, "spot", "/api/v3/account/commission", {"symbol": symbol}, signed=True)

    def futures_commission_rate(self, record: RegistryRecord, symbol: str) -> RawEnvelope:
        return self._collect(record, "futures", "/fapi/v1/commissionRate", {"symbol": symbol}, signed=True)

    def spot_exchange_info(self, record: RegistryRecord, symbol: str | None = None) -> RawEnvelope:
        return self._collect(record, "spot", "/api/v3/exchangeInfo", {"symbol": symbol})

    def futures_exchange_info(self, record: RegistryRecord, symbol: str | None = None) -> RawEnvelope:
        return self._collect(record, "futures", "/fapi/v1/exchangeInfo", {"symbol": symbol})

    def spot_depth(self, record: RegistryRecord, symbol: str, limit: int = 5) -> RawEnvelope:
        return self._collect(record, "spot", "/api/v3/depth", {"symbol": symbol, "limit": limit})

    def futures_depth(self, record: RegistryRecord, symbol: str, limit: int = 5) -> RawEnvelope:
        return self._collect(record, "futures", "/fapi/v1/depth", {"symbol": symbol, "limit": limit})

    def spot_book_ticker(self, record: RegistryRecord, symbol: str | None = None) -> RawEnvelope:
        return self._collect(record, "spot", "/api/v3/ticker/bookTicker", {"symbol": symbol})

    def futures_book_ticker(self, record: RegistryRecord, symbol: str | None = None) -> RawEnvelope:
        return self._collect(record, "futures", "/fapi/v1/ticker/bookTicker", {"symbol": symbol})
