"""Тесты банковской системы."""

from decimal import Decimal

import pytest

from src.exceptions import (
    AccountFrozenError,
    InsufficientFundsError,
    InvalidOperationError,
)
from src.models import (
    BankAccount,
    InvestmentAccount,
    PremiumAccount,
    SavingsAccount,
)
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


def test_invalid_currency_raises():
    with pytest.raises(InvalidOperationError):
        BankAccount(owner="Иванов Иван", currency="GBP")


def test_invalid_status_raises():
    with pytest.raises(InvalidOperationError):
        BankAccount(owner="Иванов Иван", status="unknown")


def test_valid_string_currency_and_status():
    account = BankAccount(owner="Иванов Иван", currency="USD", status="frozen")
    assert account.currency == Currency.USD
    assert account.status == AccountStatus.FROZEN

    # строковый "frozen" должен корректно блокировать операции
    with pytest.raises(AccountFrozenError):
        account.deposit(100)


@pytest.mark.parametrize("amount", [float("inf"), float("nan")])
def test_non_finite_amount_raises(active_account: BankAccount, amount):
    with pytest.raises(InvalidOperationError):
        active_account.deposit(amount)


# --- День 2: продвинутые типы счетов ---


def test_savings_apply_monthly_interest():
    account = SavingsAccount(owner="Смирнова Анна", balance=1000, interest_rate="0.05")
    interest = account.apply_monthly_interest()
    assert interest == Decimal("50.00")
    assert account.balance == Decimal("1050.00")


def test_savings_withdraw_below_min_balance():
    account = SavingsAccount(owner="Смирнова Анна", balance=1000, min_balance=500)
    with pytest.raises(InsufficientFundsError):
        account.withdraw(600)

    account.withdraw(400)
    assert account.balance == Decimal("600")


def test_premium_overdraft_and_fee():
    account = PremiumAccount(
        owner="Кузнецов Олег",
        balance=100,
        overdraft_limit=1000,
        withdrawal_fee=50,
    )
    account.withdraw(200)
    # 100 - (200 + 50) = -150, в пределах овердрафта -1000
    assert account.balance == Decimal("-150")


def test_premium_overdraft_limit_exceeded():
    account = PremiumAccount(
        owner="Кузнецов Олег",
        balance=0,
        overdraft_limit=100,
        withdrawal_fee=0,
    )
    with pytest.raises(InsufficientFundsError):
        account.withdraw(200)


def test_investment_invest_and_growth():
    account = InvestmentAccount(owner="Волкова Мария", balance=5000)
    account.invest("stocks", 2000)
    account.invest("bonds", 1000)

    assert account.balance == Decimal("2000")
    assert account.portfolio["stocks"] == Decimal("2000")
    assert account.portfolio["bonds"] == Decimal("1000")

    # 2000 * 0.12 + 1000 * 0.05 = 240 + 50 = 290
    assert account.project_yearly_growth() == Decimal("290.00")


def test_investment_invalid_asset():
    account = InvestmentAccount(owner="Волкова Мария", balance=1000)
    with pytest.raises(InvalidOperationError):
        account.invest("crypto", 100)


def test_polymorphism_account_type():
    accounts = [
        SavingsAccount(owner="A"),
        PremiumAccount(owner="B"),
        InvestmentAccount(owner="C"),
    ]
    for account in accounts:
        assert account.get_account_info()["account_type"] == type(account).__name__
