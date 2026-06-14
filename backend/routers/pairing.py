from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from database import get_db
from models import User
from routers.auth import get_current_user
from services.pairing_service import build_pairing_cluster

router = APIRouter(prefix="/api/pairing", tags=["pairing"])


class PairingRequest(BaseModel):
    product_ids: List[str]
    is_vegetarian: Optional[bool] = None
    is_vegan: Optional[bool] = None


@router.post("")
def get_pairings(
    data: PairingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filters = {}
    if data.is_vegetarian:
        filters["is_vegetarian"] = True
    if data.is_vegan:
        filters["is_vegan"] = True

    cluster = build_pairing_cluster(
        seed_ids=data.product_ids,
        filters=filters or None,
    )
    return cluster
