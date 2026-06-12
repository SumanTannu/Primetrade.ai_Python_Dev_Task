import argparse
import os
import sys
from typing import Any, Dict, List, Optional

from .client import (
    TESTNET_BASE_URL,
    BinanceAPIError,
    BinanceFuturesClient,
    BinanceNetworkError,
)
from .env_loader import load_dotenv
from .logging_config import configure_logging
from .orders import OrderService
from .validators import ValidationError, validate_order_input


def build_parser() -> argparse.ArgumentParser:
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Place Binance USDT-M Futures Testnet market and limit orders.",
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, help="BUY or SELL")
    parser.add_argument(
        "--type",
        required=True,
        dest="order_type",
        help="MARKET or LIMIT",
    )
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", help="Limit price; required for LIMIT orders")
    parser.add_argument(
        "--time-in-force",
        default="GTC",
        help="LIMIT order time in force: GTC, IOC, or FOK (default: GTC)",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("BINANCE_BASE_URL", TESTNET_BASE_URL),
        help="Binance Futures base URL",
    )
    parser.add_argument(
        "--log-file",
        default=os.getenv("TRADING_BOT_LOG_FILE", "logs/trading_bot.log"),
        help="Path to the log file",
    )
    parser.add_argument(
        "--recv-window",
        type=int,
        default=5000,
        help="Binance recvWindow in milliseconds",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logger = configure_logging(args.log_file)

    try:
        order = validate_order_input(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            time_in_force=args.time_in_force,
        )
        api_key = require_env("BINANCE_API_KEY")
        api_secret = require_env("BINANCE_API_SECRET")

        print_order_summary(order, args.base_url)

        client = BinanceFuturesClient(
            api_key=api_key,
            api_secret=api_secret,
            base_url=args.base_url,
            logger=logger,
        )
        service = OrderService(client)
        response = service.place_order(order, recv_window=args.recv_window)

        print_order_response(response)
        print("\nSUCCESS: order submitted to Binance Futures Testnet.")
        return 0
    except ValidationError as exc:
        logger.error("Validation error | %s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except BinanceAPIError as exc:
        print(f"ERROR: Binance rejected the request: {exc}", file=sys.stderr)
        return 1
    except BinanceNetworkError as exc:
        print(f"ERROR: network failure while contacting Binance: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        logger.error("Runtime error | %s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is required")
    return value


def print_order_summary(order: Dict[str, str], base_url: str) -> None:
    print("Order request summary")
    print("---------------------")
    print(f"Base URL : {base_url}")
    print(f"Symbol   : {order['symbol']}")
    print(f"Side     : {order['side']}")
    print(f"Type     : {order['type']}")
    print(f"Quantity : {order['quantity']}")
    if order["type"] == "LIMIT":
        print(f"Price    : {order['price']}")
        print(f"TIF      : {order['timeInForce']}")


def print_order_response(response: Dict[str, Any]) -> None:
    print("\nOrder response details")
    print("----------------------")
    fields = {
        "orderId": response.get("orderId"),
        "status": response.get("status"),
        "executedQty": response.get("executedQty"),
        "avgPrice": response.get("avgPrice"),
        "symbol": response.get("symbol"),
        "side": response.get("side"),
        "type": response.get("type"),
        "price": response.get("price"),
    }
    for key, value in fields.items():
        if value is not None:
            print(f"{key:11}: {value}")


if __name__ == "__main__":
    raise SystemExit(main())
