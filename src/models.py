"""Модели банковских счетов."""

from abc import ABC, abstractmethod
from decimal import Decimal
import uuid

from src.exceptions import (
    AccountClosedError,
    AccountFrozenError,
    InsufficientFundsError,
    InvalidOperationError,
)
from src.utils import (
    AccountStatus,
    Currency,
    generate_account_number,
    validate_amount,
    validate_currency,
    validate_status,
)


class AbstractAccount(ABC):
    """Абстрактная модель банковского счёта."""

    def __init__(
        self,
        owner: str,
        account_id: str | None = None,
        balance: Decimal | int | float | str = 0,
        status: AccountStatus = AccountStatus.ACTIVE,
    ) -> None:
        if not owner or not str(owner).strip():
            raise InvalidOperationError("Имя владельца не может быть пустым")

        self.account_id = account_id or str(uuid.uuid4())
        self.owner = str(owner).strip()
        self._balance = validate_amount(balance) if balance else Decimal("0")
        self.status = validate_status(status)

    @property
    def balance(self) -> Decimal:
        """Текущий баланс счёта (только чтение)."""
        return self._balance

    @abstractmethod
    def deposit(self, amount) -> None:
        """Пополнение счёта."""

    @abstractmethod
    def withdraw(self, amount) -> None:
        """Снятие средств со счёта."""

    @abstractmethod
    def get_account_info(self) -> dict:
        """Возвращает сводную информацию о счёте."""


class BankAccount(AbstractAccount):
    """Конкретная реализация банковского счёта."""

    def __init__(
        self,
        owner: str,
        currency: Currency = Currency.RUB,
        account_number: str | None = None,
        balance: Decimal | int | float | str = 0,
        status: AccountStatus = AccountStatus.ACTIVE,
        account_id: str | None = None,
    ) -> None:
        super().__init__(
            owner=owner,
            account_id=account_id,
            balance=balance,
            status=status,
        )
        self.account_number = account_number or generate_account_number()
        self.currency = validate_currency(currency)

    def _check_active(self) -> None:
        """Проверяет, что счёт активен и допускает операции."""
        if self.status == AccountStatus.FROZEN:
            raise AccountFrozenError("Счёт заморожен. Операции недоступны.")
        if self.status == AccountStatus.CLOSED:
            raise AccountClosedError("Счёт закрыт. Операции недоступны.")

    def deposit(self, amount) -> None:
        """Пополняет счёт на указанную сумму."""
        self._check_active()
        validated_amount = validate_amount(amount)
        self._balance += validated_amount

    def withdraw(self, amount) -> None:
        """Снимает указанную сумму со счёта."""
        self._check_active()
        validated_amount = validate_amount(amount)

        if validated_amount > self._balance:
            raise InsufficientFundsError(
                f"Недостаточно средств. Баланс: {self._balance}, "
                f"запрошено: {validated_amount}"
            )

        self._balance -= validated_amount

    def freeze(self) -> None:
        """Замораживает счёт."""
        if self.status == AccountStatus.CLOSED:
            raise AccountClosedError("Нельзя заморозить закрытый счёт.")
        self.status = AccountStatus.FROZEN

    def activate(self) -> None:
        """Активирует счёт."""
        if self.status == AccountStatus.CLOSED:
            raise AccountClosedError("Нельзя активировать закрытый счёт.")
        self.status = AccountStatus.ACTIVE

    def close(self) -> None:
        """Закрывает счёт."""
        self.status = AccountStatus.CLOSED

    def get_account_info(self) -> dict:
        """Возвращает сводную информацию о счёте."""
        return {
            "account_id": self.account_id,
            "account_number": self.account_number,
            "owner": self.owner,
            "balance": self._balance,
            "currency": self.currency.value,
            "status": self.status.value,
            "account_type": self.__class__.__name__,
        }

    def __str__(self) -> str:
        last_digits = self.account_number[-4:]
        return (
            f"BankAccount | Клиент: {self.owner} | "
            f"****{last_digits} | Статус: {self.status.value} | "
            f"Баланс: {self._balance} {self.currency.value}"
        )
