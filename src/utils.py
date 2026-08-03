"""Вспомогательные функции и перечисления банковской системы."""

from decimal import Decimal, InvalidOperation
from enum import Enum
import uuid

from src.exceptions import InvalidOperationError


class Currency(Enum):
    """Поддерживаемые валюты счёта."""

    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    KZT = "KZT"
    CNY = "CNY"


class  AccountStatus(Enum):
    """Статус банковского счёта."""

    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


def generate_account_number() -> str:
    """Генерирует короткий уникальный номер счёта (8 символов)."""
    return uuid.uuid4().hex[:8]


def validate_currency(value) -> Currency:
    """Приводит значение к Currency (enum или строка), иначе InvalidOperationError."""
    if isinstance(value, Currency):
        return value
    if isinstance(value, str):
        try:
            return Currency(value.upper())
        except ValueError:
            pass
    raise InvalidOperationError(f"Недопустимая валюта: {value!r}")


def validate_status(value) -> AccountStatus:
    """Приводит значение к AccountStatus (enum или строка), иначе InvalidOperationError."""
    if isinstance(value, AccountStatus):
        return value
    if isinstance(value, str):
        try:
            return AccountStatus(value.lower())
        except ValueError:
            pass
    raise InvalidOperationError(f"Недопустимый статус: {value!r}")


def validate_non_negative(value, name: str = "значение") -> Decimal:
    """Приводит к Decimal и требует конечное значение >= 0."""
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise InvalidOperationError(f"Некорректное {name}: {value!r}") from exc
    if not result.is_finite() or result < 0:
        raise InvalidOperationError(
            f"{name} должно быть неотрицательным числом: {value!r}"
        )
    return result


def validate_amount(amount) -> Decimal:
    """Проверяет и приводит сумму к Decimal."""
    if amount is None:
        raise InvalidOperationError("Сумма не может быть None")

    try:
        decimal_amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise InvalidOperationError(
            f"Некорректная сумма: {amount!r}"
        ) from exc

    if not decimal_amount.is_finite():
        raise InvalidOperationError(
            f"Сумма должна быть конечным числом: {amount!r}"
        )

    if decimal_amount <= 0:
        raise InvalidOperationError(
            "Сумма должна быть положительной"
        )

    return decimal_amount
