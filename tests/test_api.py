from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_transfer_success():
    response = client.post(
        "/transfer",
        json={
            "sender":"alice",
            "receiver":"bob",
            "amount": 100
        }
    )

    assert response.status_code == 200
    assert response.json()['message'] == "Transfer Successful"

def test_transfer_failure_by_simulate():
    response = client.post(
        "/transfer",
        json ={
            "sender":"alice",
            "receiver":"bob",
            "amount": 100,
            "simulate_failure" : True
        }
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Payment failed"

def test_transfer_failure_by_invalidAccount():
    response = client.post(
        "/transfer",
        json ={
            "sender":"alicel",
            "receiver":"bob",
            "amount": 100,
            "simulate_failure" : False
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"