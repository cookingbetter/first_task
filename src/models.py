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
    validate_non_negative,
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


class SavingsAccount(BankAccount):
    """Сберегательный счёт с минимальным остатком и месячной ставкой."""

    def __init__(
        self,
        owner: str,
        currency: Currency = Currency.RUB,
        min_balance: Decimal | int | float | str = 0,
        interest_rate: Decimal | int | float | str = Decimal("0.01"),
        **kwargs,
    ) -> None:
        super().__init__(owner=owner, currency=currency, **kwargs)
        self.min_balance = validate_non_negative(min_balance, "min_balance")
        self.interest_rate = validate_non_negative(interest_rate, "interest_rate")

    def withdraw(self, amount) -> None:
        """Снимает средства, не допуская опускания ниже минимального остатка."""
        self._check_active()
        validated_amount = validate_amount(amount)

        if self._balance - validated_amount < self.min_balance:
            raise InsufficientFundsError(
                f"Снятие нарушит минимальный остаток. Баланс: {self._balance}, "
                f"мин. остаток: {self.min_balance}, запрошено: {validated_amount}"
            )

        self._balance -= validated_amount

    def apply_monthly_interest(self) -> Decimal:
        """Начисляет месячные проценты на текущий баланс."""
        self._check_active()
        interest = self._balance * self.interest_rate
        self._balance += interest
        return interest

    def get_account_info(self) -> dict:
        info = super().get_account_info()
        info["min_balance"] = self.min_balance
        info["interest_rate"] = self.interest_rate
        return info

    def __str__(self) -> str:
        last_digits = self.account_number[-4:]
        return (
            f"SavingsAccount | Клиент: {self.owner} | "
            f"****{last_digits} | Статус: {self.status.value} | "
            f"Баланс: {self._balance} {self.currency.value} | "
            f"Мин. остаток: {self.min_balance} | Ставка: {self.interest_rate}"
        )


class PremiumAccount(BankAccount):
    """Премиальный счёт с овердрафтом, комиссией и увеличенными лимитами."""

    def __init__(
        self,
        owner: str,
        currency: Currency = Currency.RUB,
        overdraft_limit: Decimal | int | float | str = Decimal("1000"),
        withdrawal_fee: Decimal | int | float | str = Decimal("50"),
        withdrawal_limit: Decimal | int | float | str = Decimal("1000000"),
        **kwargs,
    ) -> None:
        super().__init__(owner=owner, currency=currency, **kwargs)
        self.overdraft_limit = validate_non_negative(overdraft_limit, "overdraft_limit")
        self.withdrawal_fee = validate_non_negative(withdrawal_fee, "withdrawal_fee")
        self.withdrawal_limit = validate_non_negative(
            withdrawal_limit, "withdrawal_limit"
        )

    def withdraw(self, amount) -> None:
        """Снимает средства с учётом комиссии и допустимого овердрафта."""
        self._check_active()
        validated_amount = validate_amount(amount)

        if validated_amount > self.withdrawal_limit:
            raise InvalidOperationError(
                f"Превышен лимит снятия. Лимит: {self.withdrawal_limit}, "
                f"запрошено: {validated_amount}"
            )

        total = validated_amount + self.withdrawal_fee
        if self._balance - total < -self.overdraft_limit:
            raise InsufficientFundsError(
                f"Превышен лимит овердрафта. Баланс: {self._balance}, "
                f"овердрафт: {self.overdraft_limit}, "
                f"списание с комиссией: {total}"
            )

        self._balance -= total

    def get_account_info(self) -> dict:
        info = super().get_account_info()
        info["overdraft_limit"] = self.overdraft_limit
        info["withdrawal_fee"] = self.withdrawal_fee
        info["withdrawal_limit"] = self.withdrawal_limit
        return info

    def __str__(self) -> str:
        last_digits = self.account_number[-4:]
        return (
            f"PremiumAccount | Клиент: {self.owner} | "
            f"****{last_digits} | Статус: {self.status.value} | "
            f"Баланс: {self._balance} {self.currency.value} | "
            f"Овердрафт: {self.overdraft_limit} | Комиссия: {self.withdrawal_fee}"
        )


class InvestmentAccount(BankAccount):
    """Инвестиционный счёт с виртуальным портфелем активов."""

    ASSET_GROWTH = {
        "stocks": Decimal("0.12"),
        "bonds": Decimal("0.05"),
        "etf": Decimal("0.08"),
    }

    def __init__(
        self,
        owner: str,
        currency: Currency = Currency.RUB,
        **kwargs,
    ) -> None:
        super().__init__(owner=owner, currency=currency, **kwargs)
        self.portfolio = {asset: Decimal("0") for asset in self.ASSET_GROWTH}

    def invest(self, asset: str, amount) -> None:
        """Переводит средства с баланса в актив портфеля."""
        if asset not in self.ASSET_GROWTH:
            raise InvalidOperationError(
                f"Недопустимый актив: {asset!r}. "
                f"Доступны: {', '.join(self.ASSET_GROWTH)}"
            )
        self._check_active()
        validated_amount = validate_amount(amount)

        if validated_amount > self._balance:
            raise InsufficientFundsError(
                f"Недостаточно средств для инвестиции. Баланс: {self._balance}, "
                f"запрошено: {validated_amount}"
            )

        self._balance -= validated_amount
        self.portfolio[asset] += validated_amount

    def project_yearly_growth(self) -> Decimal:
        """Прогнозирует годовой прирост стоимости портфеля."""
        return sum(
            (self.portfolio[asset] * rate for asset, rate in self.ASSET_GROWTH.items()),
            Decimal("0"),
        )

    def withdraw(self, amount) -> None:
        """Снимает средства только со свободного баланса (не из активов)."""
        self._check_active()
        validated_amount = validate_amount(amount)

        if validated_amount > self._balance:
            raise InsufficientFundsError(
                f"Недостаточно свободных средств. Баланс: {self._balance}, "
                f"запрошено: {validated_amount}"
            )

        self._balance -= validated_amount

    def get_account_info(self) -> dict:
        info = super().get_account_info()
        info["portfolio"] = dict(self.portfolio)
        info["projected_yearly_growth"] = self.project_yearly_growth()
        return info

    def __str__(self) -> str:
        last_digits = self.account_number[-4:]
        assets_value = sum(self.portfolio.values(), Decimal("0"))
        return (
            f"InvestmentAccount | Клиент: {self.owner} | "
            f"****{last_digits} | Статус: {self.status.value} | "
            f"Баланс: {self._balance} {self.currency.value} | "
            f"Активы: {assets_value}"
        )
