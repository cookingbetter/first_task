"""Демонстрация работы банковских счетов."""

from src.exceptions import AccountFrozenError
from src.models import BankAccount
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


if __name__ == "__main__":
    main()
