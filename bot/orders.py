import logging
from typing import Optional

from bot.client import BinanceFuturesClient

logger = logging.getLogger("trading_bot.orders")


def place_market_order(client: BinanceFuturesClient, symbol: str, side: str, quantity: str) -> dict:
    """Executes a MARKET order (executes immediately at current price)."""
    logger.info("Placing MARKET %s %s qty=%s", side, symbol, quantity)
    return client.place_order(
        symbol=symbol,
        side=side,
        type="MARKET",
        quantity=quantity,
    )


def place_limit_order(client: BinanceFuturesClient, symbol: str, side: str, quantity: str, price: str) -> dict:
    """Executes a LIMIT order (executes at a specified price or better)."""
    logger.info("Placing LIMIT %s %s qty=%s price=%s", side, symbol, quantity, price)
    return client.place_order(
        symbol=symbol,
        side=side,
        type="LIMIT",
        quantity=quantity,
        price=price,
        timeInForce="GTC",  # Good Till Cancelled
    )


def place_stop_limit_order(client: BinanceFuturesClient, symbol: str, side: str, quantity: str, price: str, stop_price: str) -> dict:
    """Executes a STOP-LIMIT order (triggers limit order when stop_price is hit)."""
    logger.info("Placing STOP-LIMIT %s %s qty=%s price=%s stopPrice=%s", side, symbol, quantity, price, stop_price)
    return client.place_order(
        symbol=symbol,
        side=side,
        type="STOP",
        quantity=quantity,
        price=price,
        stopPrice=stop_price,
        timeInForce="GTC",
    )


def place_order(
    client: BinanceFuturesClient, symbol: str, side: str, order_type: str, 
    quantity: str, price: Optional[str] = None, stop_price: Optional[str] = None
) -> dict:
    """Routes the incoming request to the correct specific order function based on order_type."""
    if order_type == "MARKET":
        response = place_market_order(client, symbol, side, quantity)
    elif order_type == "LIMIT":
        response = place_limit_order(client, symbol, side, quantity, price)
    elif order_type == "STOP":
        response = place_stop_limit_order(client, symbol, side, quantity, price, stop_price)
    else:
        raise ValueError(f"Unsupported order type: {order_type}")

    logger.info(
        "Order placed successfully: orderId=%s status=%s",
        response.get("orderId"),
        response.get("status"),
    )
    return response