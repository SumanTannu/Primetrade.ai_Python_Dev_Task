import re
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}
VALID_TIME_IN_FORCE = {"GTC", "IOC", "FOK"}
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")


class ValidationError(ValueError):
    """Raised when CLI input is invalid."""


def normalize_symbol(symbol: str) -> str:
    value = symbol.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(value):
        raise ValidationError(
            "symbol must be 5-20 uppercase letters/numbers, e.g. BTCUSDT"
        )
    return value


def normalize_side(side: str) -> str:
    value = side.strip().upper()
    if value not in VALID_SIDES:
        raise ValidationError("side must be BUY or SELL")
    return value


def normalize_order_type(order_type: str) -> str:
    value = order_type.strip().upper()
    if value not in VALID_ORDER_TYPES:
        raise ValidationError("order type must be MARKET or LIMIT")
    return value


def normalize_time_in_force(time_in_force: str) -> str:
    value = time_in_force.strip().upper()
    if value not in VALID_TIME_IN_FORCE:
        raise ValidationError("time-in-force must be GTC, IOC, or FOK")
    return value


def positive_decimal(value: str, field_name: str) -> str:
    try:
        parsed = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValidationError(f"{field_name} must be a valid number") from exc

    if parsed <= 0:
        raise ValidationError(f"{field_name} must be greater than zero")

    return format(parsed.normalize(), "f")


def validate_order_input(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    time_in_force: str = "GTC",
) -> Dict[str, str]:
    normalized_type = normalize_order_type(order_type)
    normalized = {
        "symbol": normalize_symbol(symbol),
        "side": normalize_side(side),
        "type": normalized_type,
        "quantity": positive_decimal(quantity, "quantity"),
    }

    if normalized_type == "LIMIT":
        if price is None:
            raise ValidationError("price is required for LIMIT orders")
        normalized["price"] = positive_decimal(price, "price")
        normalized["timeInForce"] = normalize_time_in_force(time_in_force)
    elif price is not None:
        raise ValidationError("price is only supported for LIMIT orders")

    return normalized
