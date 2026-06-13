from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User, CartItem
from schemas import CartItemAdd, CartItemUpdate, CartResponse, CartItemResponse
from services.product_service import get_product_by_id, get_products_by_ids
from routers.auth import get_current_user

router = APIRouter(prefix="/api/cart", tags=["cart"])


@router.get("", response_model=CartResponse)
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    product_ids = [item.product_id for item in items]
    products = {p["id"]: p for p in get_products_by_ids(product_ids)}

    result = []
    total = 0.0
    for item in items:
        product = products.get(item.product_id)
        if product:
            subtotal = product["price"] * item.quantity
            total += subtotal
            result.append(
                CartItemResponse(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    product=product,
                    subtotal=subtotal,
                )
            )
    return CartResponse(items=result, total=total)


@router.post("/add")
def add_to_cart(
    data: CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = get_product_by_id(data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = (
        db.query(CartItem)
        .filter(
            CartItem.user_id == current_user.id,
            CartItem.product_id == data.product_id,
        )
        .first()
    )
    if existing:
        existing.quantity += data.quantity
    else:
        db.add(
            CartItem(
                user_id=current_user.id,
                product_id=data.product_id,
                quantity=data.quantity,
            )
        )
    db.commit()
    return {"message": "Added to cart", "product_name": product["name"]}


@router.put("/update/{product_id}")
def update_cart(
    product_id: str,
    data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id, CartItem.product_id == product_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")

    if data.quantity <= 0:
        db.delete(item)
    else:
        item.quantity = data.quantity
    db.commit()
    return {"message": "Cart updated"}


@router.delete("/remove/{product_id}")
def remove_from_cart(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id, CartItem.product_id == product_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")
    db.delete(item)
    db.commit()
    return {"message": "Removed from cart"}


@router.delete("/clear")
def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Cart cleared"}


@router.post("/checkout")
def checkout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Convert current cart into a completed order and clear the cart."""
    from services.order_service import create_order_from_cart
    
    result = create_order_from_cart(current_user.id, db)
    if not result:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    return {
        "message": "Order placed successfully! 🎉",
        **result,
    }

