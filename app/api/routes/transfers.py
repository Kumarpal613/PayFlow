from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.transfer_controller import make_transfer
from app.db.database import get_session
from app.schemas.transfer import TransferRequest, TransferResponse
from app.services.transfer_service import (
    AccountNotFoundError,
    InsufficientFundsError,
    InvalidTransferError,
)

router = APIRouter()


@router.post(
    "/transfer",
    response_model=TransferResponse,
    status_code=status.HTTP_200_OK,
)
def transfer(
    data: TransferRequest,
    session: Session = Depends(get_session),
) -> TransferResponse:
    try:
        return make_transfer(session, data)
    except AccountNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
    except InsufficientFundsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(error)
        ) from error
    except InvalidTransferError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transfer failed",
        ) from error
