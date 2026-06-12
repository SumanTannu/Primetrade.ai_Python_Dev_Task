import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests


TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class BinanceAPIError(RuntimeError):
    """Raised when Binance returns a non-success API response."""

    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self.payload = payload
        message = payload.get("msg") if isinstance(payload, dict) else str(payload)
        super().__init__(f"Binance API error {status_code}: {message}")


class BinanceNetworkError(RuntimeError):
    """Raised when the request cannot reach Binance."""


class BinanceFuturesClient:
    """Small Binance USDT-M Futures REST client for signed testnet orders."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = TESTNET_BASE_URL,
        timeout: int = 10,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret.encode("utf-8")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logger or logging.getLogger("trading_bot")
        self._time_offset_ms = 0

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: Optional[str] = None,
        time_in_force: str = "GTC",
        recv_window: int = 5000,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "recvWindow": recv_window,
        }

        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force

        return self._signed_request("POST", "/fapi/v1/order", params)

    def ping_account(self) -> Dict[str, Any]:
        return self._signed_request("GET", "/fapi/v2/account", {})

    def sync_time(self) -> int:
        """Sync local request timestamps with Binance server time."""
        started_at = int(time.time() * 1000)
        payload = self._request("GET", "/fapi/v1/time", {}, signed=False)
        completed_at = int(time.time() * 1000)

        server_time = payload.get("serverTime") if isinstance(payload, dict) else None
        if server_time is None:
            raise BinanceAPIError(500, {"msg": "Binance time response missing serverTime"})

        local_midpoint = started_at + ((completed_at - started_at) // 2)
        self._time_offset_ms = int(server_time) - local_midpoint
        self.logger.info("Time sync | offset_ms=%s", self._time_offset_ms)
        return self._time_offset_ms

    def _signed_request(
        self, method: str, path: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            return self._signed_request_once(method, path, params)
        except BinanceAPIError as exc:
            if self._is_timestamp_error(exc):
                self.logger.info("Timestamp rejected; syncing server time and retrying")
                self.sync_time()
                return self._signed_request_once(method, path, params)
            raise

    def _signed_request_once(
        self, method: str, path: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        signed_params = {
            **params,
            "timestamp": self._timestamp_ms(),
        }
        query_string = urlencode(signed_params, doseq=True)
        signature = hmac.new(
            self.api_secret,
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        signed_params["signature"] = signature

        return self._request(method, path, signed_params)

    def _request(
        self,
        method: str,
        path: str,
        params: Dict[str, Any],
        signed: bool = True,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        safe_params = self._redact(params)
        self.logger.info("API request | method=%s url=%s params=%s", method, url, safe_params)

        try:
            request_kwargs: Dict[str, Any] = {
                "method": method,
                "url": url,
                "timeout": self.timeout,
            }
            if signed:
                request_kwargs["headers"] = {"X-MBX-APIKEY": self.api_key}
            if method.upper() == "GET":
                request_kwargs["params"] = params
            else:
                request_kwargs["data"] = params

            response = requests.request(
                **request_kwargs,
            )
        except requests.RequestException as exc:
            self.logger.error(
                "Network failure | method=%s url=%s error_type=%s",
                method,
                url,
                exc.__class__.__name__,
            )
            raise BinanceNetworkError(
                "request failed before Binance returned a response"
            ) from exc

        payload = self._parse_response(response)
        self.logger.info(
            "API response | status_code=%s payload=%s",
            response.status_code,
            payload,
        )

        if response.status_code >= 400:
            self.logger.error(
                "API error | status_code=%s payload=%s",
                response.status_code,
                payload,
            )
            raise BinanceAPIError(response.status_code, payload)

        return payload

    @staticmethod
    def _parse_response(response: requests.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text

    @staticmethod
    def _redact(params: Dict[str, Any]) -> Dict[str, Any]:
        redacted = dict(params)
        if "signature" in redacted:
            redacted["signature"] = "***"
        return redacted

    def _timestamp_ms(self) -> int:
        return int(time.time() * 1000) + self._time_offset_ms

    @staticmethod
    def _is_timestamp_error(exc: BinanceAPIError) -> bool:
        if not isinstance(exc.payload, dict):
            return False
        return exc.payload.get("code") == -1021
