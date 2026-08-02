"""Тесты банковской системы."""

from decimal import Decimal

import pytest

from src.exceptions import AccountFrozenError
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


def test_deposit_increases_balance(active_account: BankAccount):
    active_account.deposit(250)
    assert active_account.balance == Decimal("1250")


def test_withdraw_decreases_balance(active_account: BankAccount):
    active_account.withdraw(400)
    assert active_account.balance == Decimal("600")


def test_frozen_account_operations(frozen_account: BankAccount):
    with pytest.raises(AccountFrozenError):
        frozen_account.deposit(100)

    with pytest.raises(AccountFrozenError):
        frozen_account.withdraw(50)
