"""Тесты банковской системы."""

from decimal import Decimal

import pytest

from src.exceptions import (
    AccountClosedError,
    AccountFrozenError,
    InsufficientFundsError,
    InvalidOperationError,
)
from src.models import BankAccount
from src.utils import AccountStatus, Currency


@pytest.fixture
def active_account() -> BankAccount:
    return BankAccount(
        owner="Иванов Иван",
        currency=Currency.RUB,
        account_number="12345678",
        balance=1000,
    )


@pytest.fixture
def frozen_account() -> BankAccount:
    return BankAccount(
        owner="Петров Пётр",
        currency=Currency.USD,
        account_number="87654321",
        balance=500,
        status=AccountStatus.FROZEN,
    )


def test_account_creation_with_auto_number():
    account = BankAccount(owner="Сидоров Сидор")
    assert len(account.account_number) == 8
    assert account.balance == Decimal("0")
    assert account.status == AccountStatus.ACTIVE
    assert account.currency == Currency.RUB


def test_deposit_increases_balance(active_account: BankAccount):
    active_account.deposit(250)
    assert active_account.balance == Decimal("1250")


def test_withdraw_decreases_balance(active_account: BankAccount):
    active_account.withdraw(400)
    assert active_account.balance == Decimal("600")


def test_withdraw_insufficient_funds(active_account: BankAccount):
    with pytest.raises(InsufficientFundsError):
        active_account.withdraw(2000)


def test_frozen_account_operations(frozen_account: BankAccount):
    with pytest.raises(AccountFrozenError):
        frozen_account.deposit(100)

    with pytest.raises(AccountFrozenError):
        frozen_account.withdraw(50)


def test_closed_account_operations(active_account: BankAccount):
    active_account.close()

    with pytest.raises(AccountClosedError):
        active_account.deposit(100)

    with pytest.raises(AccountClosedError):
        active_account.withdraw(50)


@pytest.mark.parametrize("amount", [0, -10, -0.01])
def test_invalid_amount_raises(active_account: BankAccount, amount):
    with pytest.raises(InvalidOperationError):
        active_account.deposit(amount)

    with pytest.raises(InvalidOperationError):
        active_account.withdraw(amount)


def test_str_representation(active_account: BankAccount):
    account_str = str(active_account)
    assert "BankAccount" in account_str
    assert "Иванов Иван" in account_str
    assert "****5678" in account_str
    assert AccountStatus.ACTIVE.value in account_str
    assert "RUB" in account_str


def test_get_account_info(active_account: BankAccount):
    info = active_account.get_account_info()
    assert info["owner"] == "Иванов Иван"
    assert info["account_number"] == "12345678"
    assert info["currency"] == "RUB"
    assert info["status"] == AccountStatus.ACTIVE.value
    assert info["account_type"] == "BankAccount"
