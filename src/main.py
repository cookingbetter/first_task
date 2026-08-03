"""Демонстрация работы банковских счетов."""

from src.exceptions import AccountFrozenError, InsufficientFundsError
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


if __name__ == "__main__":
    main()
    demo_day2()
