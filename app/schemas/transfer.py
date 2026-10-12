from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TransferRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    sender: str = Field(min_length=1, max_length=100)
    receiver: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=Decimal("0"), max_digits=12, decimal_places=2)


class TransferResponse(BaseModel):
    message: str
    sender_balance: Decimal
    receiver_balance: Decimal
