from sqlalchemy.orm import Session

from app.schemas.transfer import TransferRequest, TransferResponse
from app.services.transfer_service import transfer_money


def make_transfer(
    session: Session, request: TransferRequest
) -> TransferResponse:
    result = transfer_money(
        session,
        sender_name=request.sender,
        receiver_name=request.receiver,
        amount=request.amount,
    )
    return TransferResponse(
        message="Transfer Successful",
        sender_balance=result.sender_balance,
        receiver_balance=result.receiver_balance,
    )
