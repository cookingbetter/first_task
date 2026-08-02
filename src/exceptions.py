"""Исключения банковской системы."""


class AccountError(Exception):
    """Базовое исключение для операций со счётом."""


class AccountFrozenError(AccountError):
    """Операция над замороженным счётом."""


class AccountClosedError(AccountError):
    """Операция над закрытым счётом."""


class InvalidOperationError(AccountError):
    """Некорректная сумма или неверная операция."""


class InsufficientFundsError(AccountError):
    """Недостаточно средств на счёте."""
