#!/usr/bin/env python3
import argparse
import os
import sys
import textwrap
from typing import Optional

from dotenv import load_dotenv

from bot.client import BinanceFuturesClient
from bot.logging_config import setup_logging
from bot.orders import place_order
from bot.validators import (
    validate_order_params,
    validate_price,
    validate_quantity,
    validate_symbol,
)

SEP = "─" * 56


def upper_str(value: str) -> str:
    """Helper to ensure string inputs are uppercase and stripped of whitespace."""
    return value.strip().upper()


def print_banner() -> None:
    print(
        "\n╔══════════════════════════════════════════════════════╗"
        "\n║      Binance Futures Testnet  –  Trading Bot         ║"
        "\n╚══════════════════════════════════════════════════════╝\n"
    )


def print_request_summary(
    symbol: str, side: str, order_type: str, quantity: str, price: Optional[str], stop_price: Optional[str]
) -> None:
    """Displays a clean summary of the order being requested before submission."""
    print(f"\n{SEP}")
    print("  ORDER REQUEST")
    print(SEP)
    print(f"  Symbol      : {symbol}")
    print(f"  Side        : {side}")
    print(f"  Type        : {order_type}")
    print(f"  Quantity    : {quantity}")
    if price is not None:
        print(f"  Price       : {price}")
    if stop_price is not None:
        print(f"  Stop Price  : {stop_price}")
    print(SEP)


def print_order_response(resp: dict) -> None:
    """Displays a clean summary of the API response after order placement."""
    print(f"\n{SEP}")
    print("  ORDER RESPONSE")
    print(SEP)
    print(f"  Order ID      : {resp.get('orderId', 'N/A')}")
    print(f"  Symbol        : {resp.get('symbol', 'N/A')}")
    print(f"  Status        : {resp.get('status', 'N/A')}")
    print(f"  Side          : {resp.get('side', 'N/A')}")
    print(f"  Type          : {resp.get('type', 'N/A')}")
    print(f"  Orig Qty      : {resp.get('origQty', 'N/A')}")
    print(f"  Executed Qty  : {resp.get('executedQty', 'N/A')}")
    print(f"  Avg Price     : {resp.get('avgPrice', 'N/A')}")
    print(f"  Price         : {resp.get('price', 'N/A')}")
    print(f"  Time In Force : {resp.get('timeInForce', 'N/A')}")
    print(f"  Client Order  : {resp.get('clientOrderId', 'N/A')}")
    print(SEP)


def prompt_with_validation(prompt_text: str, validator) -> str:
    """Continually prompts the user until a valid input is provided."""
    while True:
        raw = input(prompt_text).strip()
        try:
            return validator(raw)
        except ValueError as exc:
            print(f"  ✗  {exc}")


def prompt_choice(label: str, choices: list) -> str:
    """Presents a numbered list of choices to the user."""
    print(f"\n{label}:")
    for i, c in enumerate(choices, 1):
        print(f"  [{i}] {c}")
    while True:
        raw = input(f"  Select [1-{len(choices)}]: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        print(f"  ✗  Enter a number between 1 and {len(choices)}.")


def interactive_mode() -> dict:
    """Guides the user through an interactive prompt to build an order."""
    print(f"\n{SEP}")
    print("  Interactive Order Entry")
    print(SEP)

    symbol = prompt_with_validation("  Symbol (e.g. BTCUSDT): ", validate_symbol)
    side = prompt_choice("  Side", ["BUY", "SELL"])
    order_type = prompt_choice("  Order Type", ["MARKET", "LIMIT", "STOP (Stop-Limit)"])

    if order_type == "STOP (Stop-Limit)":
        order_type = "STOP"

    quantity = prompt_with_validation("\n  Quantity: ", validate_quantity)

    price = None
    stop_price = None

    # Ask for limit and stop prices if applicable
    if order_type in ("LIMIT", "STOP"):
        price = prompt_with_validation("  Limit Price: ", validate_price)
    if order_type == "STOP":
        stop_price = prompt_with_validation("  Stop (Trigger) Price: ", validate_price)

    return dict(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )


def build_parser() -> argparse.ArgumentParser:
    """Builds the CLI argument parser for non-interactive use."""
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet – Order Placement CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Examples:
              python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
              python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 50000
              python cli.py --interactive
            """
        ),
    )
    parser.add_argument("--symbol", type=upper_str, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", type=upper_str, choices=["BUY", "SELL"], help="Order side")
    parser.add_argument(
        "--type", dest="order_type", type=upper_str, choices=["MARKET", "LIMIT", "STOP"], help="Order type"
    )
    parser.add_argument("--quantity", help="Amount to trade")
    parser.add_argument("--price", default=None, help="Limit price (required for LIMIT and STOP orders)")
    parser.add_argument("--stop-price", dest="stop_price", default=None, help="Stop/trigger price (required for STOP)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive prompt mode")
    return parser


def main() -> None:
    # Load environment variables (API keys)
    load_dotenv()
    print_banner()

    parser = build_parser()
    args = parser.parse_args()

    # Determine order parameters based on mode
    if args.interactive:
        raw = interactive_mode()
        symbol, side, order_type = raw["symbol"], raw["side"], raw["order_type"]
        quantity, price, stop_price = raw["quantity"], raw["price"], raw["stop_price"]
    else:
        # Check for missing arguments in CLI mode
        required_fields = {
            "--symbol": args.symbol,
            "--side": args.side,
            "--type": args.order_type,
            "--quantity": args.quantity,
        }
        missing = [k for k, v in required_fields.items() if not v]
        if missing:
            parser.error(
                f"The following arguments are required: {', '.join(missing)}\n"
                "  Tip: use --interactive / -i for guided input."
            )
        symbol, side, order_type = args.symbol, args.side, args.order_type
        quantity, price, stop_price = args.quantity, args.price, args.stop_price

    # 1. Initialize logging NOW that we know the order type
    logger = setup_logging(order_type)

    # 2. Validate all inputs
    try:
        symbol, side, order_type, quantity, price, stop_price = validate_order_params(
            symbol, side, order_type, quantity, price, stop_price
        )
    except ValueError as exc:
        logger.error("Validation failed: %s", exc)
        print(f"\n  ✗  Validation error: {exc}")
        sys.exit(1)

    print_request_summary(symbol, side, order_type, quantity, price, stop_price)
    logger.info(
        "Order request: symbol=%s side=%s type=%s qty=%s price=%s stop_price=%s",
        symbol, side, order_type, quantity, price, stop_price,
    )

    # 3. Retrieve credentials and initialize client
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        logger.error("Missing BINANCE_API_KEY or BINANCE_API_SECRET in environment.")
        print("\n  ✗  Missing credentials.\n     Copy .env.example → .env and fill in your testnet keys.")
        sys.exit(1)

    client = BinanceFuturesClient(api_key, api_secret)
    print("\n  Submitting order to Binance Futures Testnet…")

    # 4. Submit the order via API
    try:
        response = place_order(client, symbol, side, order_type, quantity, price, stop_price)
    except RuntimeError as exc:
        logger.error("Order placement failed: %s", exc)
        print(f"\n  ✗  FAILURE — {exc}")
        sys.exit(1)

    # 5. Display success
    print_order_response(response)
    print(f"\n  ✓  Order placed successfully!\n")


if __name__ == "__main__":
    main()