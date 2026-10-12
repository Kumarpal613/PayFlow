from collections.abc import Iterable
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account


def create_account(
    session: Session, name: str, balance: Decimal = Decimal("0.00")
) -> Account:
    account = Account(name=name, balance=balance)
    session.add(account)
    session.flush()
    return account


def get_account(session: Session, account_id: int) -> Account | None:
    return session.get(Account, account_id)


def get_accounts_by_name_for_update(
    session: Session, names: Iterable[str]
) -> dict[str, Account]:
    statement = (
        select(Account)
        .where(Account.name.in_(set(names)))
        .order_by(Account.id)
        .with_for_update()
    )
    accounts = session.scalars(statement).all()
    return {account.name: account for account in accounts}


def credit_account(session: Session, account: Account, amount: Decimal) -> None:
    account.balance += amount
    session.flush()
