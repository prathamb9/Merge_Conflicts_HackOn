"""
Order Service
Handles order history, frequent purchases, and recent purchase analysis
for cart optimization and recipe deduplication.
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Order, OrderItem, CartItem
from services.product_service import get_product_by_id, get_products_by_ids


def create_order_from_cart(user_id: str, db: Session) -> Optional[Dict]:
    """
    Convert the current cart into a completed order.
    Returns order summary or None if cart is empty.
    """
    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    if not cart_items:
        return None
    
    # Build order items with current prices
    total = 0.0
    order_items_data = []
    for ci in cart_items:
        product = get_product_by_id(ci.product_id)
        if not product:
            continue
        price = product.get("price", 0)
        subtotal = price * ci.quantity
        total += subtotal
        order_items_data.append({
            "product_id": ci.product_id,
            "product_name": product["name"],
            "quantity": ci.quantity,
            "price_at_purchase": price,
        })
    
    if not order_items_data:
        return None
    
    # Determine delivery charge
    from config import settings
    delivery_charge = 0.0 if total >= settings.free_delivery_threshold else settings.delivery_charge
    
    # Create the order
    order = Order(
        user_id=user_id,
        total_amount=total,
        delivery_charge=delivery_charge,
        status="completed",
    )
    db.add(order)
    db.flush()  # Get the order ID
    
    # Create order items
    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=order.id,
            **item_data,
        )
        db.add(order_item)
    
    # Clear the cart
    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    db.commit()
    
    return {
        "order_id": order.id,
        "total_amount": total,
        "delivery_charge": delivery_charge,
        "items_count": len(order_items_data),
        "status": "completed",
    }


def get_frequent_purchases(user_id: str, db: Session, limit: int = 10) -> List[Dict]:
    """
    Get the user's most frequently ordered products.
    Returns products sorted by purchase frequency (most bought first).
    """
    # Count how many times each product was ordered
    freq_query = (
        db.query(
            OrderItem.product_id,
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label("total_qty"),
            func.count(OrderItem.id).label("order_count"),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id, Order.status == "completed")
        .group_by(OrderItem.product_id, OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )
    
    result = []
    for row in freq_query:
        product = get_product_by_id(row.product_id)
        if product and product.get("in_stock", True):
            result.append({
                "product": product,
                "total_quantity": int(row.total_qty),
                "order_count": int(row.order_count),
            })
    
    return result


def get_recent_purchase_ids(user_id: str, db: Session, days: int = 30) -> set:
    """
    Get product IDs that the user purchased in the last N days.
    Used by recipe-to-cart to skip common pantry items.
    """
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    recent = (
        db.query(OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == user_id,
            Order.status == "completed",
            Order.created_at >= cutoff,
        )
        .distinct()
        .all()
    )
    
    return {row.product_id for row in recent}


def get_cart_optimization_suggestions(
    user_id: str,
    cart_value: float,
    db: Session,
) -> Optional[Dict]:
    """
    Check if the user is close to a delivery/coupon threshold and suggest
    products from their frequent purchases to cross it.
    """
    from config import settings
    
    thresholds = [
        {
            "name": "Free Delivery",
            "amount": settings.free_delivery_threshold,
            "savings": settings.delivery_charge,
        },
        {
            "name": f"₹{settings.coupon_discount:.0f} Off Coupon",
            "amount": settings.coupon_threshold,
            "savings": settings.coupon_discount,
        },
    ]
    
    # Find the nearest threshold the user hasn't crossed yet
    best_threshold = None
    for t in thresholds:
        gap = t["amount"] - cart_value
        if 0 < gap < 150:  # Only suggest if gap is reasonable (< ₹150)
            if best_threshold is None or gap < best_threshold["gap"]:
                best_threshold = {**t, "gap": gap}
    
    if not best_threshold:
        return None
    
    # Get the user's frequent purchases to suggest specific items
    frequent = get_frequent_purchases(user_id, db, limit=5)
    gap = best_threshold["gap"]
    
    suggestions = []
    for fp in frequent:
        product = fp["product"]
        price = product.get("price", 0)
        # Suggest items that would cross the threshold
        if price >= gap * 0.8 and price <= gap * 4:
            suggestions.append({
                **product,
                "reason": f"Frequently purchased — adding this crosses the {best_threshold['name']} threshold",
            })
            if len(suggestions) >= 3:
                break
    
    # If no frequent purchases match, find cheap in-stock items near the gap
    if not suggestions:
        from services.product_service import load_products
        all_products = load_products()
        candidates = [
            p for p in all_products
            if p.get("in_stock", True)
            and gap * 0.5 <= p.get("price", 0) <= gap * 3
        ]
        candidates.sort(key=lambda p: abs(p["price"] - gap))
        for p in candidates[:3]:
            suggestions.append({
                **p,
                "reason": f"Add this to reach {best_threshold['name']} and save ₹{best_threshold['savings']:.0f}",
            })
    
    if not suggestions:
        return None
    
    return {
        "threshold_name": best_threshold["name"],
        "threshold_amount": best_threshold["amount"],
        "current_total": cart_value,
        "gap": gap,
        "suggested_products": suggestions,
        "savings": best_threshold["savings"],
    }
