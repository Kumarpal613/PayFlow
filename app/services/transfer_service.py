from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.accounts import (
    credit_account,
    get_accounts_by_name_for_update,
)


class InvalidTransferError(ValueError):
    pass


class AccountNotFoundError(LookupError):
    pass


class InsufficientFundsError(ValueError):
    pass


@dataclass(frozen=True)
class TransferResult:
    sender_balance: Decimal
    receiver_balance: Decimal


def transfer_money(
    session: Session,
    sender_name: str,
    receiver_name: str,
    amount: Decimal,
) -> TransferResult:
    if amount <= 0:
        raise InvalidTransferError("Amount must be greater than zero")
    if sender_name == receiver_name:
        raise InvalidTransferError("Sender and receiver must be different accounts")

    with session.begin():
        accounts = get_accounts_by_name_for_update(
            session, (sender_name, receiver_name)
        )
        sender = accounts.get(sender_name)
        receiver = accounts.get(receiver_name)
        if sender is None or receiver is None:
            missing_name = sender_name if sender is None else receiver_name
            raise AccountNotFoundError(f"Account not found: {missing_name}")
        if sender.balance < amount:
            raise InsufficientFundsError("Insufficient balance")

        sender.balance -= amount
        session.flush()
        credit_account(session, receiver, amount)

        return TransferResult(
            sender_balance=sender.balance,
            receiver_balance=receiver.balance,
        )
