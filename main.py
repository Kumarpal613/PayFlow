from fastapi import FastAPI, HTTPException 
from pydantic import BaseModel

from payment import transfer_money

app = FastAPI()

# dictionary
accounts = {
    "alice":{"balance": 1000},
    "bob": {"balance": 500}
}

class TransferRequest(BaseModel):
    sender : str
    receiver: str
    amount : float
    simulate_failure: bool = False


@app.post("/transfer")
def transfer(data: TransferRequest):
    sender = accounts.get(data.sender)
    receiver = accounts.get(data.receiver)

    if sender is None or receiver is None :
        raise HTTPException(status_code=404,detail="Account not found")

    try:
        transfer_money(sender,receiver, data.amount, data.simulate_failure)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    except RuntimeError as e:
        raise HTTPException(status_code=500,detail="Payment failed") 

    return {"message":"Transfer Successful",
            "sender_balance": sender["balance"],
            "receiver_balance": receiver["balance"]}