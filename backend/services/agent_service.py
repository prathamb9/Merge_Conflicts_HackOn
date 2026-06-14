"""
Agent Service
=============
Turns the recommendation chatbot into a conversational shopping *agent* that can
drive a full purchase flow (chat OR voice):

    browse / recommend  ->  "buy this"  ->  collect address (if needed)
        ->  collect payment (if needed)  ->  create order  ->  redirect to payment portal

State is intentionally kept on the client (CheckoutState) and echoed back each
turn, so the backend stays stateless apart from the final order creation.
"""
import re
import json
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from models import User, UserProfile, CartItem, Address, PaymentMethod
from services.bargain_service import detect_bargain_intent, negotiate
from services.emotion_service import detect_situation, build_care_kit
from services.product_service import get_product_by_id, get_products_by_ids
from services import order_service


# ── Intent detection ──────────────────────────────────────────────────────────

_BUY_PATTERNS = [
    r"\bbuy\b", r"\bpurchase\b", r"\border\b", r"\bcheckout\b", r"\bcheck out\b",
    r"\bplace (?:the |my )?order\b", r"\bi'?ll take\b", r"\bget me\b",
    r"\bproceed to (?:pay|checkout|payment)\b", r"\bpay now\b", r"\bbook it\b",
    r"\badd to order\b", r"\bcomplete (?:the |my )?(?:order|purchase)\b",
]
_BUY_RE = re.compile("|".join(_BUY_PATTERNS), re.IGNORECASE)

_CANCEL_RE = re.compile(
    r"\b(cancel|stop|never ?mind|forget it|abort|not now|don'?t buy)\b", re.IGNORECASE
)

_AFFIRM_RE = re.compile(
    r"\b(yes|yeah|yep|sure|confirm|ok(?:ay)?|go ahead|do it|proceed|correct|right)\b",
    re.IGNORECASE,
)

_ALL_REF_RE = re.compile(r"\b(all|everything|every ?thing|both|them all)\b", re.IGNORECASE)
_THIS_REF_RE = re.compile(r"\b(this|that|it|these|those|them)\b", re.IGNORECASE)


def detect_purchase_intent(message: str) -> bool:
    return bool(_BUY_RE.search(message or ""))


def is_cancel(message: str) -> bool:
    return bool(_CANCEL_RE.search(message or ""))


# ── Context helpers ─────────────────────────────────────────────────────────

def build_user_profile(user: User, db: Session) -> Optional[Dict]:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        return None
    import json as _json
    try:
        favs = _json.loads(profile.favorite_categories or "[]")
    except Exception:
        favs = []
    return {
        "is_vegetarian": profile.is_vegetarian,
        "is_vegan": profile.is_vegan,
        "is_high_protein": profile.is_high_protein,
        "weight_loss_mode": profile.weight_loss_mode,
        "budget_preference": profile.budget_preference,
        "favorite_categories": favs,
    }


def get_cart_value(user: User, db: Session) -> float:
    cart_items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    if not cart_items:
        return 0.0
    products = {p["id"]: p for p in get_products_by_ids([c.product_id for c in cart_items])}
    return sum(
        products.get(c.product_id, {}).get("price", 0) * c.quantity for c in cart_items
    )


def get_default_address(user: User, db: Session) -> Optional[Address]:
    q = db.query(Address).filter(Address.user_id == user.id)
    return q.filter(Address.is_default == True).first() or q.first()


def get_default_payment(user: User, db: Session) -> Optional[PaymentMethod]:
    q = db.query(PaymentMethod).filter(PaymentMethod.user_id == user.id)
    return q.filter(PaymentMethod.is_default == True).first() or q.first()


# ── Product resolution for "buy this" ────────────────────────────────────────

def resolve_target_products(message: str, last_recommended_ids: List[str]) -> List[str]:
    """
    Figure out which products the user wants to buy.

    Priority:
      1. Explicit "all / everything" -> every recommended product.
      2. Product name match within the last recommendations.
      3. A "this / it / that" reference -> all last-recommended products.
    """
    msg = (message or "").lower()
    recommended = [pid for pid in last_recommended_ids if get_product_by_id(pid)]

    if not recommended:
        return []

    if _ALL_REF_RE.search(msg):
        return recommended

    # Name matching
    matched = []
    for pid in recommended:
        product = get_product_by_id(pid)
        name = (product.get("name") or "").lower()
        # match on the full name or any significant word (len > 3) of the name
        words = [w for w in re.findall(r"\w+", name) if len(w) > 3]
        if name and name in msg:
            matched.append(pid)
        elif any(re.search(r"\b" + re.escape(w) + r"\b", msg) for w in words):
            matched.append(pid)
    if matched:
        return matched

    if _THIS_REF_RE.search(msg):
        return recommended

    # Default: if exactly one was recommended, assume that one
    if len(recommended) == 1:
        return recommended

    return recommended


# ── Address parsing (LLM with safe fallback) ─────────────────────────────────

def parse_address(text: str) -> Dict:
    """Parse a free-text / spoken address into structured fields."""
    fallback = {
        "full_name": "",
        "phone": "",
        "line1": text.strip(),
        "line2": "",
        "city": "",
        "state": "",
        "pincode": "",
    }
    # Regex extract pincode (6 digits) and phone (10 digits) as a baseline
    pin = re.search(r"\b(\d{6})\b", text or "")
    phone = re.search(r"\b(\d{10})\b", text or "")
    if pin:
        fallback["pincode"] = pin.group(1)
    if phone and phone.group(1) != fallback["pincode"]:
        fallback["phone"] = phone.group(1)

    try:
        from services.llm_service import _chat_complete

        prompt = (
            "Extract a delivery address from the user's text into JSON with keys: "
            "full_name, phone, line1, line2, city, state, pincode. "
            "Use empty strings for anything not present. Respond ONLY with JSON.\n\n"
            f"Text: {text}"
        )
        content = _chat_complete(
            [{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0,
        ).strip()
        if "```" in content:
            content = content.split("```")[1].replace("json", "", 1).strip()
        data = json.loads(content)
        parsed = {k: str(data.get(k, "") or "").strip() for k in fallback}
        if not parsed.get("line1"):
            parsed["line1"] = text.strip()
        return parsed
    except Exception:
        return fallback


# ── Payment parsing ──────────────────────────────────────────────────────────

def parse_payment_method(text: str) -> Optional[Dict]:
    msg = (text or "").lower()
    if re.search(r"\b(cash|cod|cash on delivery|on delivery)\b", msg):
        return {"type": "cod", "label": "Cash on Delivery", "details": "Pay when delivered"}
    if re.search(r"\b(upi|gpay|google pay|phonepe|phone pe|paytm|bhim)\b", msg):
        return {"type": "upi", "label": "UPI", "details": "UPI payment"}
    if re.search(r"\b(card|credit|debit|visa|mastercard|rupay)\b", msg):
        return {"type": "card", "label": "Card", "details": "Credit / Debit card"}
    if re.search(r"\b(net ?banking|bank)\b", msg):
        return {"type": "netbanking", "label": "Net Banking", "details": "Net banking"}
    if re.search(r"\b(wallet|paytm wallet|amazon pay)\b", msg):
        return {"type": "wallet", "label": "Wallet", "details": "Wallet payment"}
    return None


def save_address(user: User, db: Session, fields: Dict) -> Address:
    # Unset previous defaults
    db.query(Address).filter(Address.user_id == user.id).update({Address.is_default: False})
    addr = Address(user_id=user.id, is_default=True, **fields)
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


def save_payment(user: User, db: Session, fields: Dict) -> PaymentMethod:
    db.query(PaymentMethod).filter(PaymentMethod.user_id == user.id).update(
        {PaymentMethod.is_default: False}
    )
    pm = PaymentMethod(user_id=user.id, is_default=True, **fields)
    db.add(pm)
    db.commit()
    db.refresh(pm)
    return pm


# ── Response builders ────────────────────────────────────────────────────────

def _product_cards(product_ids: List[str]) -> List[Dict]:
    cards = []
    for pid in product_ids:
        p = get_product_by_id(pid)
        if p:
            cards.append(dict(p))
    return cards


def _names(product_ids: List[str]) -> str:
    names = [get_product_by_id(p)["name"] for p in product_ids if get_product_by_id(p)]
    if not names:
        return "your items"
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + f" and {names[-1]}"


def _total(product_ids: List[str]) -> float:
    return sum((get_product_by_id(p) or {}).get("price", 0) for p in product_ids)


def _base_response(message: str, **kwargs) -> Dict:
    resp = {
        "message": message,
        "recommendations": [],
        "total": 0.0,
        "reasoning": "",
        "current_state": "BROWSING",
        "missing_details": [],
        "action": "NONE",
        "checkout_items": [],
        "checkout": {"stage": "", "selected_ids": []},
        "order_id": "",
        "quick_replies": [],
        "speak": True,
        "kit_title": "",
    }
    resp.update(kwargs)
    return resp


# ── Checkout steps ───────────────────────────────────────────────────────────

def _finalize_order(user: User, db: Session, selected_ids: List[str]) -> Dict:
    """Both address + payment are available — create a pending order and redirect."""
    addr = get_default_address(user, db)
    pay = get_default_payment(user, db)
    order = order_service.create_order_from_products(
        user_id=user.id,
        product_ids=selected_ids,
        db=db,
        delivery_address=addr.one_line() if addr else "",
        payment_method=pay.label if pay else "",
        status="pending",
        payment_status="unpaid",
    )
    if not order:
        return _base_response(
            "Hmm, I couldn't find those items in stock. Want to try something else?"
        )
    total = order["total_amount"] + order["delivery_charge"]
    where = (addr.city or "your saved address") if addr else "your address"
    msg = (
        f"Perfect! I've prepared your order for {_names(selected_ids)} — "
        f"total ₹{total:.0f}, delivering to {where}, paying via "
        f"{pay.label if pay else 'your saved method'}. Taking you to the secure "
        f"payment page to confirm."
    )
    return _base_response(
        msg,
        recommendations=_product_cards(selected_ids),
        total=order["total_amount"],
        action="REDIRECT_TO_PAYMENT",
        current_state="CHECKOUT_READY",
        order_id=order["order_id"],
        checkout_items=selected_ids,
        checkout={"stage": "", "selected_ids": []},
    )


def start_checkout(message: str, last_recommended_ids: List[str], user: User, db: Session) -> Dict:
    selected = resolve_target_products(message, last_recommended_ids)
    if not selected:
        return _base_response(
            "Sure — which product would you like to buy? You can tap a product or "
            "tell me its name and I'll get the order started.",
        )

    addr = get_default_address(user, db)
    pay = get_default_payment(user, db)

    if addr and pay:
        # Everything is saved -> go straight to the payment portal
        return _finalize_order(user, db, selected)

    if not addr:
        return _base_response(
            f"Great choice! I'll order {_names(selected)} for you. "
            f"First, where should I deliver it? Please tell me your full delivery "
            f"address including the area and 6-digit pincode.",
            action="ASK_FOR_INFO",
            current_state="COLLECTING_INFO",
            missing_details=["delivery_address"],
            checkout_items=selected,
            checkout={"stage": "await_address", "selected_ids": selected},
        )

    # Has address but no payment method
    return _base_response(
        f"You're all set with delivery! How would you like to pay for "
        f"{_names(selected)}? You can say Cash on Delivery, UPI, or Card.",
        action="ASK_FOR_INFO",
        current_state="COLLECTING_INFO",
        missing_details=["payment_method"],
        checkout_items=selected,
        checkout={"stage": "await_payment", "selected_ids": selected},
        quick_replies=["Cash on Delivery", "UPI", "Card"],
    )


def handle_address(message: str, selected_ids: List[str], user: User, db: Session) -> Dict:
    fields = parse_address(message)
    save_address(user, db, fields)

    pay = get_default_payment(user, db)
    if pay:
        return _finalize_order(user, db, selected_ids)

    return _base_response(
        "Got it, address saved! And how would you like to pay? "
        "Cash on Delivery, UPI, or Card?",
        action="ASK_FOR_INFO",
        current_state="COLLECTING_INFO",
        missing_details=["payment_method"],
        checkout_items=selected_ids,
        checkout={"stage": "await_payment", "selected_ids": selected_ids},
        quick_replies=["Cash on Delivery", "UPI", "Card"],
    )


def handle_payment(message: str, selected_ids: List[str], user: User, db: Session) -> Dict:
    pm = parse_payment_method(message)
    if not pm:
        return _base_response(
            "I didn't catch that. Please choose a payment method: "
            "Cash on Delivery, UPI, or Card.",
            action="ASK_FOR_INFO",
            current_state="COLLECTING_INFO",
            missing_details=["payment_method"],
            checkout_items=selected_ids,
            checkout={"stage": "await_payment", "selected_ids": selected_ids},
            quick_replies=["Cash on Delivery", "UPI", "Card"],
        )
    save_payment(user, db, pm)
    return _finalize_order(user, db, selected_ids)


# ── Main entry point ─────────────────────────────────────────────────────────

def handle_chat(request, user: User, db: Session) -> Dict:
    """
    Single entry point used by the /api/chat route. Decides between the normal
    recommendation flow and the agentic checkout flow.
    """
    message = request.message or ""
    checkout = request.checkout
    stage = checkout.stage if checkout else ""
    selected_ids = checkout.selected_ids if checkout else []

    # Allow the user to bail out of an in-progress checkout
    if stage and is_cancel(message):
        return _base_response(
            "No problem, I've cancelled the checkout. Let me know if you'd like to "
            "look for anything else!"
        )

    if stage == "await_address":
        return handle_address(message, selected_ids, user, db)
    if stage == "await_payment":
        return handle_payment(message, selected_ids, user, db)

    # Not mid-checkout: is this a purchase request?
    if detect_purchase_intent(message):
        return start_checkout(message, request.last_recommended_ids, user, db)

    # Bargain / negotiate intent?
    is_bargain, offered_amount = detect_bargain_intent(message)
    if is_bargain and request.last_recommended_ids:
        from models import Order
        order_count = db.query(Order).filter(
            Order.user_id == user.id, Order.status == "completed"
        ).count()
        # If no amount was parsed, ask the user for their offer
        if offered_amount <= 0:
            return _base_response(
                "I'm open to negotiating! What price did you have in mind for these items?",
                quick_replies=["Tell me your offer"],
            )
        result = negotiate(
            product_ids=request.last_recommended_ids,
            buyer_offer=offered_amount,
            order_count=order_count,
        )
        recs = [dict(p) for p in result.get("counter_items", []) if isinstance(p, dict)]
        resp = _base_response(
            result["message"],
            recommendations=recs,
            total=result["final_price"],
            reasoning=f"Bargain Bot | outcome={result['outcome']} | discount={result['discount_pct']}%",
            quick_replies=(
                [f"Accept ₹{result['final_price']:.0f}", "No thanks", "Show alternatives"]
                if result["outcome"] in ("counter", "accept") else
                ["Show alternatives", "Keep original price"]
            ),
        )
        # If accepted, pre-stage checkout with the negotiated items
        if result["outcome"] == "accept":
            resp["checkout_items"] = [p["id"] for p in recs if "id" in p]
        return resp

    # Emotional / situational care-kit intent?
    situation = detect_situation(message)
    if situation:
        profile = build_user_profile(user, db) or {}
        budget = profile.get("budget_preference") or 1500
        filters = {
            "is_vegetarian": profile.get("is_vegetarian"),
            "is_vegan": profile.get("is_vegan"),
        }
        kit = build_care_kit(situation, budget=budget, filters=filters)
        if kit and kit.get("products"):
            return _base_response(
                kit["message"],
                recommendations=[dict(p) for p in kit["products"]],
                total=kit["total"],
                reasoning=f"Care Kit assembled for situation: {situation}",
                kit_title=kit["kit_title"],
                quick_replies=["Buy the whole kit", "Show me more options"],
            )

    # Default: normal recommendation flow
    from services.llm_service import get_chat_response

    result = get_chat_response(
        message=message,
        history=[h.model_dump() for h in request.history],
        user_profile=build_user_profile(user, db),
        user_id=user.id,
        cart_value=get_cart_value(user, db),
    )
    result.setdefault("current_state", "BROWSING")
    result.setdefault("action", "NONE")
    result["checkout"] = {"stage": "", "selected_ids": []}
    result.setdefault("order_id", "")
    result.setdefault("kit_title", "")
    # Offer a buy quick-reply when products were recommended
    if result.get("recommendations"):
        result.setdefault("quick_replies", ["Buy all of these"])
    return result
