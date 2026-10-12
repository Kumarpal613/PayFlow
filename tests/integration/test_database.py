from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.models.account import Account
from app.repositories.accounts import (
    create_account,
    get_account,
    get_accounts_by_name_for_update,
)


def test_account_is_persisted_and_retrievable(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory.begin() as session:
        account = create_account(session, "Alice", Decimal("125.50"))
        account_id = account.id

    with session_factory() as session:
        retrieved = get_account(session, account_id)

    assert retrieved is not None
    assert retrieved.name == "Alice"
    assert retrieved.balance == Decimal("125.50")


def test_rollback_discards_new_account(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        account = create_account(session, "Temporary", Decimal("10.00"))
        account_id = account.id
        session.rollback()

    with session_factory() as session:
        assert get_account(session, account_id) is None


@pytest.mark.parametrize(
    ("name", "balance"),
    [("Negative balance", Decimal("-0.01")), ("   ", Decimal("10.00"))],
)
def test_database_constraints_reject_invalid_accounts(
    session_factory: sessionmaker[Session], name: str, balance: Decimal
) -> None:
    with session_factory() as session:
        session.add(Account(name=name, balance=balance))

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

    with session_factory() as session:
        assert session.query(Account).count() == 0


def test_accounts_for_update_returns_existing_accounts_in_id_order(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory.begin() as session:
        first = create_account(session, "First", Decimal("30.00"))
        second = create_account(session, "Second", Decimal("40.00"))
        first_id, second_id = first.id, second.id

    with session_factory() as session:
        locked_accounts = get_accounts_by_name_for_update(
            session, ["Second", "First", "Missing"]
        )

    assert [account.id for account in locked_accounts.values()] == [
        first_id,
        second_id,
    ]
    assert locked_accounts["First"].balance == Decimal("30.00")
    assert locked_accounts["Second"].balance == Decimal("40.00")


def test_transfer_persists_both_account_balances(
    seeded_session_factory: sessionmaker[Session],
) -> None:
    from app.services.transfer_service import transfer_money

    with seeded_session_factory() as session:
        result = transfer_money(
            session, "alice", "bob", Decimal("125.25")
        )

    with seeded_session_factory() as session:
        alice = session.query(Account).filter_by(name="alice").one()
        bob = session.query(Account).filter_by(name="bob").one()

    assert result.sender_balance == Decimal("874.75")
    assert result.receiver_balance == Decimal("625.25")
    assert alice.balance == Decimal("874.75")
    assert bob.balance == Decimal("625.25")


def test_transfer_rolls_back_debit_if_credit_fails(
    seeded_session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services import transfer_service
    from app.services.transfer_service import transfer_money

    def fail_credit(session: Session, account: Account, amount: Decimal) -> None:
        raise RuntimeError("Simulated credit failure")

    monkeypatch.setattr(transfer_service, "credit_account", fail_credit)
    with seeded_session_factory() as session:
        with pytest.raises(RuntimeError, match="Simulated credit failure"):
            transfer_money(session, "alice", "bob", Decimal("100.00"))

    with seeded_session_factory() as session:
        alice = session.query(Account).filter_by(name="alice").one()
        bob = session.query(Account).filter_by(name="bob").one()

    assert alice.balance == Decimal("1000.00")
    assert bob.balance == Decimal("500.00")
