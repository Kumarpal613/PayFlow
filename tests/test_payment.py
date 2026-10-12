import pytest
from payment import transfer_money


def test_successful_transfer():
    alice = {"balance":1000}
    bob = {"balance": 500}

    transfer_money(alice ,bob , 100)

    assert alice["balance"] == 900
    assert bob["balance"] == 600


def test_transfer_rejects_insufficient_balance():
    alice = {"balance": 50}
    bob = {"balance": 500}

    with pytest.raises(ValueError, match="Insufficient balance"):
        transfer_money(alice, bob, 100)

    assert alice["balance"] == 50
    assert bob["balance"] == 500


@pytest.mark.parametrize("amount", [0, -10])
def test_transfer_rejects_non_positive_amount(amount):
    alice = {"balance": 1000}
    bob = {"balance": 500}

    with pytest.raises(ValueError, match="Amount should be greater than Zero"):
        transfer_money(alice, bob, amount)

    assert alice["balance"] == 1000
    assert bob["balance"] == 500


def test_transfer_rejects_same_account():
    alice = {"balance": 1000}

    with pytest.raises(
        ValueError, match="Sender and Receiver cannot be the same account"
    ):
        transfer_money(alice, alice, 100)

    assert alice["balance"] == 1000


def test_failed_transfer_rolls_back():
    alice = {"balance": 1000}
    bob = {"balance": 500}

    with pytest.raises(RuntimeError, match="Simulated crash"):
        transfer_money(alice, bob, 100, simulate_failure=True)

    assert alice["balance"] == 1000
    assert bob["balance"] == 500