"""Управляющий класс банка и модель клиента (День 3)."""

from datetime import date, datetime
from decimal import Decimal
import uuid

from src.exceptions import (
    AgeRestrictionError,
    AuthenticationError,
    ClientBlockedError,
    InvalidOperationError,
    OperationNotAllowedError,
)
from src.models import BankAccount
from src.utils import (
    ClientStatus,
    calculate_age,
    validate_currency,
    validate_pin,
    validate_status,
)

MIN_AGE = 18
MAX_LOGIN_ATTEMPTS = 3
NIGHT_START_HOUR = 0
NIGHT_END_HOUR = 5


class Client:
    """Клиент банка."""

    def __init__(
        self,
        full_name: str,
        birth_date: date,
        pin,
        contacts: dict | None = None,
        client_id: str | None = None,
        status: ClientStatus = ClientStatus.ACTIVE,
    ) -> None:
        if not full_name or not str(full_name).strip():
            raise InvalidOperationError("ФИО клиента не может быть пустым")

        if calculate_age(birth_date) < MIN_AGE:
            raise AgeRestrictionError(
                f"Клиент должен быть не младше {MIN_AGE} лет"
            )

        self.full_name = str(full_name).strip()
        self.birth_date = birth_date
        self.client_id = client_id or str(uuid.uuid4())
        self.status = status if isinstance(status, ClientStatus) else ClientStatus(status)
        self.contacts = dict(contacts) if contacts else {}
        self.account_numbers: list[str] = []
        self._pin = validate_pin(pin)
        self._failed_attempts = 0

    def check_pin(self, pin) -> bool:
        """Сравнивает переданный PIN с сохранённым."""
        return str(pin) == self._pin

    @property
    def failed_attempts(self) -> int:
        return self._failed_attempts

    def get_info(self) -> dict:
        """Сводная информация о клиенте (без раскрытия PIN)."""
        return {
            "client_id": self.client_id,
            "full_name": self.full_name,
            "status": self.status.value,
            "age": calculate_age(self.birth_date),
            "contacts": dict(self.contacts),
            "account_numbers": list(self.account_numbers),
        }

    def __str__(self) -> str:
        return (
            f"Client | {self.full_name} | ID: {self.client_id[:8]} | "
            f"Статус: {self.status.value} | Счетов: {len(self.account_numbers)}"
        )


class Bank:
    """Управляющий класс банка: клиенты, счета, безопасность, аналитика."""

    def __init__(self, name: str, clock=datetime.now) -> None:
        self.name = name
        self._clock = clock
        self._clients: dict[str, Client] = {}
        self._accounts: dict[str, BankAccount] = {}
        self.suspicious_activities: list[dict] = []

    # --- безопасность ---

    def _flag_suspicious(self, description: str, **details) -> None:
        """Фиксирует подозрительное действие."""
        record = {
            "description": description,
            "timestamp": self._clock(),
            **details,
        }
        self.suspicious_activities.append(record)

    def _check_operation_time(self) -> None:
        """Запрещает операции в ночное время (00:00-05:00)."""
        hour = self._clock().hour
        if NIGHT_START_HOUR <= hour < NIGHT_END_HOUR:
            self._flag_suspicious("Операция в запрещённое ночное время", hour=hour)
            raise OperationNotAllowedError(
                f"Операции запрещены с 00:00 до 05:00 (сейчас {hour}:00)"
            )

    # --- клиенты ---

    def add_client(self, client: Client) -> str:
        """Регистрирует клиента в банке."""
        if client.client_id in self._clients:
            raise InvalidOperationError(
                f"Клиент уже зарегистрирован: {client.client_id}"
            )
        self._clients[client.client_id] = client
        return client.client_id

    def get_client(self, client_id: str) -> Client:
        """Возвращает клиента по идентификатору."""
        client = self._clients.get(client_id)
        if client is None:
            raise InvalidOperationError(f"Клиент не найден: {client_id}")
        return client

    def authenticate_client(self, client_id: str, pin) -> bool:
        """Аутентифицирует клиента по PIN. 3 неверные попытки -> блокировка."""
        client = self.get_client(client_id)

        if client.status == ClientStatus.BLOCKED:
            raise ClientBlockedError(f"Клиент заблокирован: {client_id}")

        if client.check_pin(pin):
            client._failed_attempts = 0
            return True

        client._failed_attempts += 1
        self._flag_suspicious(
            "Неверная попытка входа",
            client_id=client_id,
            attempt=client._failed_attempts,
        )

        if client._failed_attempts >= MAX_LOGIN_ATTEMPTS:
            client.status = ClientStatus.BLOCKED
            raise ClientBlockedError(
                f"Клиент заблокирован после {MAX_LOGIN_ATTEMPTS} неверных попыток"
            )

        raise AuthenticationError(
            f"Неверный PIN. Осталось попыток: "
            f"{MAX_LOGIN_ATTEMPTS - client._failed_attempts}"
        )

    # --- счета ---

    def open_account(
        self,
        client_id: str,
        account_cls: type[BankAccount] = BankAccount,
        **kwargs,
    ) -> BankAccount:
        """Открывает счёт для клиента."""
        self._check_operation_time()
        client = self.get_client(client_id)

        account = account_cls(owner=client.full_name, **kwargs)
        self._accounts[account.account_number] = account
        client.account_numbers.append(account.account_number)
        return account

    def get_account(self, account_number: str) -> BankAccount:
        """Возвращает счёт по номеру."""
        account = self._accounts.get(account_number)
        if account is None:
            raise InvalidOperationError(f"Счёт не найден: {account_number}")
        return account

    def close_account(self, account_number: str) -> None:
        """Закрывает счёт."""
        self._check_operation_time()
        self.get_account(account_number).close()

    def freeze_account(self, account_number: str) -> None:
        """Замораживает счёт."""
        self._check_operation_time()
        self.get_account(account_number).freeze()

    def unfreeze_account(self, account_number: str) -> None:
        """Размораживает (активирует) счёт."""
        self._check_operation_time()
        self.get_account(account_number).activate()

    def search_accounts(
        self,
        owner: str | None = None,
        currency=None,
        status=None,
        client_id: str | None = None,
    ) -> list[BankAccount]:
        """Ищет счета по критериям (любой набор фильтров)."""
        currency = validate_currency(currency) if currency is not None else None
        status = validate_status(status) if status is not None else None
        allowed_numbers = (
            set(self.get_client(client_id).account_numbers)
            if client_id is not None
            else None
        )

        result = []
        for account in self._accounts.values():
            if owner is not None and owner.lower() not in account.owner.lower():
                continue
            if currency is not None and account.currency != currency:
                continue
            if status is not None and account.status != status:
                continue
            if allowed_numbers is not None and account.account_number not in allowed_numbers:
                continue
            result.append(account)
        return result

    # --- аналитика ---

    def get_total_balance(self) -> Decimal:
        """Суммарный баланс всех счетов банка."""
        return sum(
            (account.balance for account in self._accounts.values()),
            Decimal("0"),
        )

    def get_clients_ranking(self) -> list[tuple[Client, Decimal]]:
        """Рейтинг клиентов по убыванию суммарного баланса их счетов."""
        ranking = []
        for client in self._clients.values():
            total = sum(
                (
                    self._accounts[number].balance
                    for number in client.account_numbers
                    if number in self._accounts
                ),
                Decimal("0"),
            )
            ranking.append((client, total))

        ranking.sort(key=lambda item: item[1], reverse=True)
        return ranking

    def __str__(self) -> str:
        return (
            f"Bank '{self.name}' | Клиентов: {len(self._clients)} | "
            f"Счетов: {len(self._accounts)}"
        )
