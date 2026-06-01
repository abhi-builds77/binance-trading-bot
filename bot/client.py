import hashlib
import hmac
import logging
import time
import urllib.parse

import requests

logger = logging.getLogger("trading_bot.client")

BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000
REQUEST_TIMEOUT = 10


class BinanceFuturesClient:
    """Handles HTTP requests and cryptographic signing for the Binance Futures Testnet API."""
    
    def __init__(self, api_key: str, api_secret: str) -> None:
        self._api_key = api_key
        self._api_secret = api_secret.encode("utf-8")
        self._session = requests.Session()
        # Binance requires the API key in the headers
        self._session.headers.update({"X-MBX-APIKEY": api_key})

    def _sign(self, query_string: str) -> str:
        """Generates a SHA256 HMAC signature required by Binance for secure endpoints."""
        return hmac.new(
            self._api_secret,
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _build_signed_params(self, params: dict) -> dict:
        """Injects timestamp, recvWindow, and the generated signature into request parameters."""
        params["recvWindow"] = RECV_WINDOW
        params["timestamp"] = int(time.time() * 1000)
        params["signature"] = self._sign(urllib.parse.urlencode(params))
        return params

    def _request(self, method: str, path: str, params: dict = None, signed: bool = True) -> dict:
        """Core network wrapper with error handling and request logging."""
        url = BASE_URL + path
        params = dict(params) if params else {}

        if signed:
            params = self._build_signed_params(params)

        # Log params without exposing the signature
        safe_params = {k: v for k, v in params.items() if k != "signature"}
        logger.debug("→ %s %s  params=%s", method, url, safe_params)

        try:
            resp = self._session.request(method, url, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.HTTPError:
            # Attempt to parse a readable error message from Binance's JSON response
            body = {}
            try:
                body = resp.json()
            except Exception:
                pass
            msg = body.get("msg", resp.text)
            logger.error("HTTP %s from Binance: %s", resp.status_code, body)
            raise RuntimeError(f"Binance API error [{resp.status_code}]: {msg}") from None
        except requests.ConnectionError as exc:
            logger.error("Network unreachable: %s", exc)
            raise RuntimeError("Network error: could not reach testnet endpoint.") from exc
        except requests.Timeout:
            logger.error("Request timed out after %ss", REQUEST_TIMEOUT)
            raise RuntimeError(f"Request timed out after {REQUEST_TIMEOUT} s.") from None
        except requests.RequestException as exc:
            logger.error("Unexpected request error: %s", exc)
            raise RuntimeError(f"Request error: {exc}") from exc

        data = resp.json()
        logger.debug("← %s %s", resp.status_code, data)
        return data

    def place_order(self, **kwargs) -> dict:
        """Submit an order to the fapi/v1/order endpoint."""
        return self._request("POST", "/fapi/v1/order", params=kwargs)

    def ping(self) -> dict:
        """Test API connectivity (does not require a signature)."""
        return self._request("GET", "/fapi/v1/ping", signed=False)