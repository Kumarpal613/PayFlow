
def transfer_money(sender, receiver, amount):
    if sender["balance"]  < amount :
        raise ValueError("Insufficient balance")
    old_balance = sender["balance"]

    try :
        sender["balance"] -= amount
        raise RuntimeError( "Simulate crash")
        receiver["balance"] += amount
    except Exception:
        sender["balance"] = old_balance
        raise


alice = {"balance": 1000}
bob = {"balance":500}

try :
    transfer_money(alice, bob, 1700)
except (ValueError, RuntimeError) as e :
    print("Transfer failed:", e)

print(alice)
print(bob)
