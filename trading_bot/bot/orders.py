from typing import Any, Dict

from .client import BinanceFuturesClient


class OrderService:
    """Order placement use case layer."""

    def __init__(self, client: BinanceFuturesClient) -> None:
        self.client = client

    def place_order(self, order: Dict[str, str], recv_window: int = 5000) -> Dict[str, Any]:
        return self.client.place_order(
            symbol=order["symbol"],
            side=order["side"],
            order_type=order["type"],
            quantity=order["quantity"],
            price=order.get("price"),
            time_in_force=order.get("timeInForce", "GTC"),
            recv_window=recv_window,
        )
