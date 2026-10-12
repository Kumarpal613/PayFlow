from decimal import Decimal

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.models.account import Account


def test_transfer_returns_updated_balances(api_client) -> None:
    response = api_client.post(
        "/transfer",
        json={"sender": "alice", "receiver": "bob", "amount": "100.00"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Transfer Successful",
        "sender_balance": "900.00",
        "receiver_balance": "600.00",
    }


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"sender": "alice", "receiver": "bob"},
        {"sender": "alice", "receiver": "bob", "amount": "not-money"},
        {"sender": "alice", "receiver": "bob", "amount": "1.001"},
        {"sender": "alice", "receiver": "bob", "amount": 1, "unexpected": True},
    ],
)
def test_transfer_rejects_malformed_request(api_client, body: dict) -> None:
    response = api_client.post("/transfer", json=body)

    assert response.status_code == 422


@pytest.mark.parametrize("amount", ["0", "-10.00"])
def test_transfer_rejects_non_positive_amount(api_client, amount: str) -> None:
    response = api_client.post(
        "/transfer",
        json={"sender": "alice", "receiver": "bob", "amount": amount},
    )

    assert response.status_code == 422


def test_transfer_returns_not_found_for_missing_account(api_client) -> None:
    response = api_client.post(
        "/transfer",
        json={"sender": "missing", "receiver": "bob", "amount": "10.00"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found: missing"


def test_transfer_returns_conflict_for_insufficient_balance(api_client) -> None:
    response = api_client.post(
        "/transfer",
        json={"sender": "bob", "receiver": "alice", "amount": "501.00"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Insufficient balance"


def test_transfer_rejects_same_account(api_client) -> None:
    response = api_client.post(
        "/transfer",
        json={"sender": "alice", "receiver": "alice", "amount": "1.00"},
    )

    assert response.status_code == 400


def test_unexpected_transfer_failure_hides_internal_error(
    api_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.controllers import transfer_controller

    def fail_transfer(*args, **kwargs):
        raise RuntimeError("private database details")

    monkeypatch.setattr(transfer_controller, "transfer_money", fail_transfer)
    response = api_client.post(
        "/transfer",
        json={"sender": "alice", "receiver": "bob", "amount": "10.00"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Transfer failed"
    assert "private database details" not in response.text


def test_api_transfer_failure_leaves_balances_unchanged(
    api_client, seeded_session_factory: sessionmaker[Session]
) -> None:
    response = api_client.post(
        "/transfer",
        json={"sender": "bob", "receiver": "alice", "amount": "501.00"},
    )

    with seeded_session_factory() as session:
        alice = session.query(Account).filter_by(name="alice").one()
        bob = session.query(Account).filter_by(name="bob").one()

    assert response.status_code == 409
    assert alice.balance == Decimal("1000.00")
    assert bob.balance == Decimal("500.00")
