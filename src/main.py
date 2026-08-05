"""Демонстрация работы банковских счетов."""

from datetime import date, datetime

from src.bank import Bank, Client
from src.exceptions import (
    AccountFrozenError,
    AgeRestrictionError,
    AuthenticationError,
    ClientBlockedError,
    InsufficientFundsError,
    OperationNotAllowedError,
)
from src.models import (
    BankAccount,
    InvestmentAccount,
    PremiumAccount,
    SavingsAccount,
)
from src.utils import AccountStatus, Currency


def main() -> None:
    """Демонстрация создания счетов и базовых операций."""
    print("=== Демонстрация банковской системы ===\n")

    active_account = BankAccount(
        owner="Иванов Иван Иванович",
        currency=Currency.RUB,
        account_number="12345678",
        balance=1000,
    )
    frozen_account = BankAccount(
        owner="Петров Пётр Петрович",
        currency=Currency.USD,
        account_number="87654321",
        balance=500,
        status=AccountStatus.FROZEN,
    )

    print("1. Создание счетов:")
    print(f"   Активный:   {active_account}")
    print(f"   Замороженный: {frozen_account}\n")

    print("2. Попытка операций над замороженным счётом:")
    for operation_name, operation in (
        ("deposit(100)", lambda: frozen_account.deposit(100)),
        ("withdraw(50)", lambda: frozen_account.withdraw(50)),
    ):
        try:
            operation()
            print(f"   {operation_name}: неожиданный успех")
        except AccountFrozenError as exc:
            print(f"   {operation_name}: {exc}")

    print("\n3. Валидные операции над активным счётом:")
    active_account.deposit(500)
    print(f"   После deposit(500): {active_account.balance} {active_account.currency.value}")

    active_account.withdraw(300)
    print(f"   После withdraw(300): {active_account.balance} {active_account.currency.value}")

    print(f"\n4. Строковое представление:\n   {active_account}")
    print(f"\n5. Информация о счёте:\n   {active_account.get_account_info()}")


def demo_day2() -> None:
    """Демонстрация продвинутых типов счетов (День 2)."""
    print("\n=== Демонстрация продвинутых типов счетов ===\n")

    savings = SavingsAccount(
        owner="Смирнова Анна",
        currency=Currency.RUB,
        account_number="11112222",
        balance=1000,
        min_balance=500,
        interest_rate="0.05",
    )
    premium = PremiumAccount(
        owner="Кузнецов Олег",
        currency=Currency.USD,
        account_number="33334444",
        balance=200,
        overdraft_limit=1000,
        withdrawal_fee=50,
    )
    investment = InvestmentAccount(
        owner="Волкова Мария",
        currency=Currency.EUR,
        account_number="55556666",
        balance=5000,
    )

    print("1. SavingsAccount (сберегательный):")
    interest = savings.apply_monthly_interest()
    print(f"   Начислены проценты: +{interest}, баланс: {savings.balance}")
    try:
        savings.withdraw(900)
    except InsufficientFundsError as exc:
        print(f"   Попытка снять ниже min_balance: {exc}")

    print("\n2. PremiumAccount (премиальный, овердрафт + комиссия):")
    print(f"   Баланс до: {premium.balance}")
    premium.withdraw(500)
    print(f"   После withdraw(500) с комиссией 50 -> баланс: {premium.balance}")

    print("\n3. InvestmentAccount (инвестиционный):")
    investment.invest("stocks", 2000)
    investment.invest("bonds", 1000)
    investment.invest("etf", 500)
    print(f"   Портфель: {investment.portfolio}")
    print(f"   Прогноз годового прироста: {investment.project_yearly_growth()}")

    print("\n4. Полиморфизм (общий цикл по разным типам):")
    for account in (savings, premium, investment):
        print(f"   {account}")
        print(f"      info: {account.get_account_info()}")


def demo_day3() -> None:
    """Демонстрация системы Bank (День 3)."""
    print("\n=== Демонстрация системы Bank ===\n")

    # фиксированное дневное время, чтобы демонстрация работала в любое время суток
    bank = Bank("МойБанк", clock=lambda: datetime(2026, 1, 1, 12, 0))

    alice = Client(
        full_name="Алиса Иванова",
        birth_date=date(1990, 5, 20),
        pin="1234",
        contacts={"phone": "+7-900-000-0001", "email": "alice@example.com"},
    )
    bob = Client(
        full_name="Борис Петров",
        birth_date=date(1985, 3, 10),
        pin="4321",
        contacts={"phone": "+7-900-000-0002"},
    )
    bank.add_client(alice)
    bank.add_client(bob)
    print(f"1. Банк: {bank}")

    print("\n2. Проверка возраста < 18:")
    try:
        Client(full_name="Юный Клиент", birth_date=date(2015, 1, 1), pin="0000")
    except AgeRestrictionError as exc:
        print(f"   {exc}")

    print("\n3. Открытие счетов:")
    acc_a = bank.open_account(alice.client_id, currency=Currency.RUB, balance=10000)
    acc_b = bank.open_account(bob.client_id, currency=Currency.USD, balance=3000)
    print(f"   Алиса: {acc_a}")
    print(f"   Борис: {acc_b}")
    print(f"   Общий баланс банка: {bank.get_total_balance()}")

    print("\n4. Аутентификация (3 неверные попытки -> блокировка):")
    print(f"   Верный PIN: {bank.authenticate_client(alice.client_id, '1234')}")
    for attempt in range(1, 4):
        try:
            bank.authenticate_client(bob.client_id, "0000")
        except AuthenticationError as exc:
            print(f"   Попытка {attempt}: {exc}")
        except ClientBlockedError as exc:
            print(f"   Попытка {attempt}: {exc}")

    print("\n5. Заморозка / разморозка счёта:")
    bank.freeze_account(acc_a.account_number)
    print(f"   После freeze: {acc_a.status.value}")
    bank.unfreeze_account(acc_a.account_number)
    print(f"   После unfreeze: {acc_a.status.value}")

    print("\n6. Поиск счетов по владельцу 'алиса':")
    for found in bank.search_accounts(owner="алиса"):
        print(f"   {found}")

    print("\n7. Рейтинг клиентов по балансу:")
    for client, total in bank.get_clients_ranking():
        print(f"   {client.full_name}: {total}")

    print("\n8. Ночной запрет операций (03:00):")
    night_bank = Bank("НочнойБанк", clock=lambda: datetime(2026, 1, 1, 3, 0))
    night_bank.add_client(alice)
    try:
        night_bank.open_account(alice.client_id, balance=100)
    except OperationNotAllowedError as exc:
        print(f"   {exc}")
    print(f"   Подозрительных действий зафиксировано: {len(night_bank.suspicious_activities)}")


if __name__ == "__main__":
    main()
    # demo_day2()
    demo_day3()
