from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from database import get_db
from models import User, Order
from routers.auth import get_current_user
from services.bargain_service import negotiate

router = APIRouter(prefix="/api/bargain", tags=["bargain"])


class BargainRequest(BaseModel):
    product_ids: List[str]
    offer: float            # buyer's offered price in INR


class BargainResponse(BaseModel):
    outcome: str            # accept | counter | decline
    final_price: float
    message: str
    counter_items: list     # products in the counter-offer
    discount_pct: float
    payoff_data: dict


@router.post("", response_model=BargainResponse)
def haggle(
    data: BargainRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.offer <= 0:
        raise HTTPException(status_code=400, detail="Offer must be greater than 0")
    if not data.product_ids:
        raise HTTPException(status_code=400, detail="No products specified")

    # Count user's completed orders as loyalty signal
    order_count = db.query(Order).filter(
        Order.user_id == current_user.id,
        Order.status == "completed",
    ).count()

    result = negotiate(
        product_ids=data.product_ids,
        buyer_offer=data.offer,
        order_count=order_count,
    )
    return BargainResponse(**result)
