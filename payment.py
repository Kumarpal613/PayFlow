
def transfer_money(sender, receiver, amount, simulate_failure=False):
    if sender["balance"]  < amount :
        raise ValueError("Insufficient balance")
    old_balance = sender["balance"]
    if amount <= 0 :
        raise ValueError("Amount should be greater than Zero")
    if sender == receiver :
        raise ValueError("Sender and Receiver cannot be the same account")

    try :
        sender["balance"] -= amount
        if simulate_failure:
            raise RuntimeError("Simulated crash")
        receiver["balance"] += amount
    except Exception:
        sender["balance"] = old_balance
        raise
