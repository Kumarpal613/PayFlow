from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services import transfer_service
from app.services.transfer_service import (
    AccountNotFoundError,
    InsufficientFundsError,
    InvalidTransferError,
    transfer_money,
)


@pytest.fixture
def accounts():
    return {
        "alice": SimpleNamespace(balance=Decimal("100.00")),
        "bob": SimpleNamespace(balance=Decimal("50.00")),
    }


@pytest.fixture
def session() -> MagicMock:
    mock_session = MagicMock()
    mock_session.begin.return_value.__enter__.return_value = None
    return mock_session


def test_successful_transfer_updates_both_balances(
    session: MagicMock, accounts: dict[str, SimpleNamespace], monkeypatch
) -> None:
    monkeypatch.setattr(
        transfer_service,
        "get_accounts_by_name_for_update",
        lambda *_: accounts,
    )

    result = transfer_money(session, "alice", "bob", Decimal("25.00"))

    assert result.sender_balance == Decimal("75.00")
    assert result.receiver_balance == Decimal("75.00")
    assert session.flush.call_count == 2


def test_transfer_rejects_insufficient_funds_without_changing_balances(
    session: MagicMock, accounts: dict[str, SimpleNamespace], monkeypatch
) -> None:
    monkeypatch.setattr(
        transfer_service,
        "get_accounts_by_name_for_update",
        lambda *_: accounts,
    )

    with pytest.raises(InsufficientFundsError, match="Insufficient balance"):
        transfer_money(session, "alice", "bob", Decimal("101.00"))

    assert accounts["alice"].balance == Decimal("100.00")
    assert accounts["bob"].balance == Decimal("50.00")


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-1.00")])
def test_transfer_rejects_non_positive_amount(
    session: MagicMock, amount: Decimal
) -> None:
    with pytest.raises(InvalidTransferError, match="greater than zero"):
        transfer_money(session, "alice", "bob", amount)


def test_transfer_rejects_same_account(session: MagicMock) -> None:
    with pytest.raises(InvalidTransferError, match="different accounts"):
        transfer_money(session, "alice", "alice", Decimal("1.00"))


@pytest.mark.parametrize(
    ("accounts", "missing_name"),
    [
        ({"bob": SimpleNamespace(balance=Decimal("50.00"))}, "alice"),
        ({"alice": SimpleNamespace(balance=Decimal("100.00"))}, "bob"),
    ],
)
def test_transfer_rejects_missing_sender_or_receiver(
    session: MagicMock,
    accounts: dict[str, SimpleNamespace],
    missing_name: str,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        transfer_service,
        "get_accounts_by_name_for_update",
        lambda *_: accounts,
    )

    with pytest.raises(AccountNotFoundError, match=missing_name):
        transfer_money(session, "alice", "bob", Decimal("1.00"))


def test_unexpected_credit_failure_propagates(
    session: MagicMock,
    accounts: dict[str, SimpleNamespace],
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        transfer_service,
        "get_accounts_by_name_for_update",
        lambda *_: accounts,
    )

    def fail_credit(*_args) -> None:
        raise RuntimeError("credit failed")

    monkeypatch.setattr(transfer_service, "credit_account", fail_credit)

    with pytest.raises(RuntimeError, match="credit failed"):
        transfer_money(session, "alice", "bob", Decimal("25.00"))
