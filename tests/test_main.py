"""Тесты банковской системы."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from src.bank import Bank, Client
from src.exceptions import (
    AccountFrozenError,
    AgeRestrictionError,
    AuthenticationError,
    ClientBlockedError,
    InsufficientFundsError,
    InvalidOperationError,
    OperationNotAllowedError,
)
from src.models import (
    BankAccount,
    InvestmentAccount,
    PremiumAccount,
    SavingsAccount,
)
from src.utils import AccountStatus, ClientStatus, Currency


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


# --- День 3: система Bank ---


def make_client(pin="1234", name="Иван Иванов", birth_year=1990) -> Client:
    return Client(full_name=name, birth_date=date(birth_year, 1, 1), pin=pin)


def make_bank(name="TestBank") -> Bank:
    # фиксированное дневное время, чтобы тесты не зависели от реального времени суток
    return Bank(name, clock=lambda: datetime(2026, 1, 1, 12, 0))


def test_add_client_and_open_account_links_balance():
    bank = make_bank()
    client = make_client()
    bank.add_client(client)

    account = bank.open_account(client.client_id, balance=1000)
    assert account.account_number in client.account_numbers
    assert bank.get_total_balance() == Decimal("1000")


def test_client_age_restriction():
    with pytest.raises(AgeRestrictionError):
        Client(full_name="Юный", birth_date=date(2020, 1, 1), pin="1234")


def test_authenticate_success_resets_attempts():
    bank = Bank("TestBank")
    client = make_client(pin="1234")
    bank.add_client(client)

    assert bank.authenticate_client(client.client_id, "1234") is True
    assert client.failed_attempts == 0


def test_authenticate_blocks_after_three_attempts():
    bank = Bank("TestBank")
    client = make_client(pin="1234")
    bank.add_client(client)

    for _ in range(2):
        with pytest.raises(AuthenticationError):
            bank.authenticate_client(client.client_id, "0000")

    # третья неверная попытка -> блокировка
    with pytest.raises(ClientBlockedError):
        bank.authenticate_client(client.client_id, "0000")

    assert client.status == ClientStatus.BLOCKED

    # заблокированный клиент не может войти даже с верным PIN
    with pytest.raises(ClientBlockedError):
        bank.authenticate_client(client.client_id, "1234")


def test_freeze_and_unfreeze_account():
    bank = make_bank()
    client = make_client()
    bank.add_client(client)
    account = bank.open_account(client.client_id, balance=500)

    bank.freeze_account(account.account_number)
    assert account.status == AccountStatus.FROZEN

    bank.unfreeze_account(account.account_number)
    assert account.status == AccountStatus.ACTIVE


def test_search_accounts_by_owner_and_currency():
    bank = make_bank()
    alice = make_client(name="Алиса Иванова")
    bob = make_client(name="Борис Петров")
    bank.add_client(alice)
    bank.add_client(bob)

    bank.open_account(alice.client_id, currency=Currency.RUB, balance=100)
    bank.open_account(bob.client_id, currency=Currency.USD, balance=200)

    by_owner = bank.search_accounts(owner="алиса")
    assert len(by_owner) == 1
    assert by_owner[0].owner == "Алиса Иванова"

    by_currency = bank.search_accounts(currency=Currency.USD)
    assert len(by_currency) == 1
    assert by_currency[0].currency == Currency.USD


def test_clients_ranking_sorted_desc():
    bank = make_bank()
    poor = make_client(name="Бедный Клиент")
    rich = make_client(name="Богатый Клиент")
    bank.add_client(poor)
    bank.add_client(rich)

    bank.open_account(poor.client_id, balance=100)
    bank.open_account(rich.client_id, balance=5000)

    ranking = bank.get_clients_ranking()
    assert ranking[0][0].full_name == "Богатый Клиент"
    assert ranking[0][1] == Decimal("5000")
    assert ranking[-1][0].full_name == "Бедный Клиент"


def test_night_operations_forbidden():
    night_bank = Bank("NightBank", clock=lambda: datetime(2026, 1, 1, 3, 0))
    client = make_client()
    night_bank.add_client(client)

    with pytest.raises(OperationNotAllowedError):
        night_bank.open_account(client.client_id, balance=100)

    assert len(night_bank.suspicious_activities) == 1
