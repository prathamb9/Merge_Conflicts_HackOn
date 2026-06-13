from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserProfile, CartItem
from schemas import ChatRequest, ChatResponse
from services.llm_service import get_chat_response
from routers.auth import get_current_user

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()

        user_profile = None
        if profile:
            user_profile = {
                "is_vegetarian": profile.is_vegetarian,
                "is_vegan": profile.is_vegan,
                "is_high_protein": profile.is_high_protein,
                "budget_preference": profile.budget_preference,
            }

        # Calculate current cart value for optimization
        from services.product_service import get_products_by_ids
        cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
        cart_value = 0.0
        if cart_items:
            product_ids = [item.product_id for item in cart_items]
            products = {p["id"]: p for p in get_products_by_ids(product_ids)}
            cart_value = sum(
                products.get(item.product_id, {}).get("price", 0) * item.quantity
                for item in cart_items
            )

        result = get_chat_response(
            message=request.message,
            history=[h.model_dump() for h in request.history],
            user_profile=user_profile,
            user_id=current_user.id,
            cart_value=cart_value,
        )
        return ChatResponse(**result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"LLM service error: {str(e)}"
        )
