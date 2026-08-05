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


class AuthenticationError(AccountError):
    """Неверные данные аутентификации (например, PIN)."""


class ClientBlockedError(AccountError):
    """Клиент заблокирован из-за превышения числа неверных попыток входа."""


class OperationNotAllowedError(AccountError):
    """Операция запрещена в текущее время (например, ночью)."""


class AgeRestrictionError(AccountError):
    """Возраст клиента не соответствует минимальному требованию."""
