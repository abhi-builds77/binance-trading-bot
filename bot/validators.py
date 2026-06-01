from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP"}


def _to_decimal(value: str, name: str) -> Decimal:
    """Converts a string to a Decimal, ensuring it is a valid, positive number."""
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"Invalid {name}: {value!r} is not a valid number.")
    if d <= 0:
        raise ValueError(f"{name} must be greater than zero, got {value!r}.")
    return d


def validate_symbol(symbol: str) -> str:
    """Ensures the trading pair symbol is alphanumeric."""
    s = symbol.strip().upper()
    if not s or not s.isalnum():
        raise ValueError(f"Symbol must be alphanumeric (e.g. BTCUSDT), got {symbol!r}.")
    return s


def validate_side(side: str) -> str:
    """Ensures side is either BUY or SELL."""
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValueError(f"Side must be BUY or SELL, got {side!r}.")
    return s


def validate_order_type(order_type: str) -> str:
    """Ensures order type is one of the supported types."""
    t = order_type.strip().upper()
    if t not in VALID_ORDER_TYPES:
        raise ValueError(f"Order type must be MARKET, LIMIT, or STOP, got {order_type!r}.")
    return t


def validate_quantity(quantity: str) -> str:
    return str(_to_decimal(quantity, "quantity"))


def validate_price(price: str, name: str = "price") -> str:
    return str(_to_decimal(price, name))


def validate_order_params(
    symbol: str, side: str, order_type: str, quantity: str,
    price: Optional[str] = None, stop_price: Optional[str] = None,
) -> Tuple[str, str, str, str, Optional[str], Optional[str]]:
    """Master validation function to check combinations of parameters."""
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    quantity = validate_quantity(quantity)

    # Dependency checks: Limit and Stop orders require a price.
    if order_type in ("LIMIT", "STOP") and price is None:
        raise ValueError(f"--price is required for {order_type} orders.")
    
    # Stop orders also require a stop_price.
    if order_type == "STOP" and stop_price is None:
        raise ValueError("--stop-price is required for STOP (Stop-Limit) orders.")

    # Validate numbers if provided
    price = validate_price(price) if price is not None else None
    stop_price = validate_price(stop_price, "stop_price") if stop_price is not None else None

    return symbol, side, order_type, quantity, price, stop_price