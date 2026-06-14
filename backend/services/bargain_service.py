"""
Bargain Bot — Applied Game Theory & Dynamic Pricing
====================================================
Implements a Stackelberg-inspired negotiation model.

Stackelberg model in this context:
  - Seller (leader) sets a price band [floor, ceiling].
  - Buyer (follower) makes an offer.
  - Agent computes the Nash equilibrium payoff and counters intelligently.

Payoff matrix variables:
  P  = catalogue price (list price)
  C  = estimated cost (floor = P * cost_ratio)
  O  = buyer's offer
  M  = margin = P - C
  B  = buyer's historical purchase probability (1.0 for no history, else order_count/5)

Equilibrium logic:
  - If O >= P           → accept at full price.
  - If O >= P * 0.95    → accept (rounding discount ≤ 5%).
  - If O >= P * 0.90    → counter with P * 0.92 + a high-margin add-on swap.
  - If O >= C * 1.15    → counter with a swap (cheaper variant) that still covers margin.
  - If O >= C           → counter with a bundle add-on that raises revenue above floor.
  - If O < C            → politely decline, explain the floor.
"""
import json
import re
from typing import Dict, List, Optional, Tuple

from services.product_service import get_product_by_id, load_products

# Category-level gross margin estimates (cost as fraction of list price)
CATEGORY_COST_RATIOS: Dict[str, float] = {
    "groceries":          0.60,
    "beauty":             0.45,
    "fragrances":         0.40,
    "skin-care":          0.50,
    "kitchen-accessories": 0.55,
    "furniture":          0.65,
    "home-decoration":    0.50,
    "laptops":            0.78,
    "smartphones":        0.75,
    "tablets":            0.76,
    "mobile-accessories": 0.55,
    "mens-shirts":        0.45,
    "mens-shoes":         0.50,
    "womens-bags":        0.48,
    "womens-dresses":     0.47,
    "womens-shoes":       0.50,
    "womens-jewellery":   0.42,
    "mens-watches":       0.52,
    "womens-watches":     0.52,
    "tops":               0.46,
    "sunglasses":         0.50,
    "sports-accessories": 0.55,
}

# How much we rely on buyer's purchase history when evaluating the offer
HISTORY_WEIGHT = 0.12   # up to 12% additional flexibility for loyal buyers


def _cost_floor(product: Dict) -> float:
    cat = product.get("category", "")
    ratio = CATEGORY_COST_RATIOS.get(cat, 0.60)
    return product["price"] * ratio


def _find_cheaper_swap(product: Dict, max_price: float) -> Optional[Dict]:
    """
    Find a similar in-stock product in the same category that costs ≤ max_price.
    Returns None if no cheaper alternative exists.
    """
    all_products = load_products()
    cat = product.get("category")
    tags = set(product.get("tags", []))
    candidates = []
    for p in all_products:
        if p["id"] == product["id"]:
            continue
        if not p.get("in_stock"):
            continue
        if p["category"] != cat:
            continue
        if p["price"] > max_price:
            continue
        tag_overlap = len(tags & set(p.get("tags", [])))
        candidates.append((p, tag_overlap))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (-x[1], x[0]["price"]))
    return candidates[0][0]


def _find_high_margin_addon(budget_gap: float) -> Optional[Dict]:
    """
    Find a small, high-margin in-stock add-on product (snack, beauty, accessory)
    that costs roughly the `budget_gap` and would push total revenue above floor.
    """
    high_margin_cats = {"beauty", "fragrances", "skin-care", "groceries", "home-decoration"}
    all_products = load_products()
    candidates = []
    for p in all_products:
        if not p.get("in_stock"):
            continue
        if p["category"] not in high_margin_cats:
            continue
        price = p["price"]
        if budget_gap * 0.5 <= price <= budget_gap * 2.0:
            margin_ratio = 1.0 - CATEGORY_COST_RATIOS.get(p["category"], 0.55)
            candidates.append((p, margin_ratio * price))
    if not candidates:
        return None
    candidates.sort(key=lambda x: -x[1])
    return candidates[0][0]


def negotiate(
    product_ids: List[str],
    buyer_offer: float,
    order_count: int = 0,
) -> Dict:
    """
    Core negotiation engine.

    Returns a dict with:
      outcome       : 'accept' | 'counter' | 'decline'
      final_price   : float (the price offered back)
      message       : str  (agent's conversational reply)
      counter_items : list of product dicts to display (may include swap/addon)
      discount_pct  : float (% off list price)
      payoff_data   : dict  (for transparency / debugging)
    """
    # 1. Collect products and compute list total
    products = []
    for pid in product_ids:
        p = get_product_by_id(pid)
        if p and p.get("in_stock"):
            products.append(p)
    if not products:
        return {
            "outcome": "decline",
            "final_price": 0,
            "message": "I couldn't find those products. Want to try something else?",
            "counter_items": [],
            "discount_pct": 0,
            "payoff_data": {},
        }

    list_total = sum(p["price"] for p in products)
    cost_total = sum(_cost_floor(p) for p in products)
    margin     = list_total - cost_total

    # 2. Buyer loyalty adjustment (more purchase history → slightly more flexible)
    loyalty_flex = min(order_count / 10.0, 1.0) * HISTORY_WEIGHT
    effective_floor = cost_total * (1.0 + 0.15 - loyalty_flex)   # 15% above cost, adjusted

    # 3. Payoff computation
    payoff = {
        "list_total":      round(list_total, 2),
        "cost_total":      round(cost_total, 2),
        "margin":          round(margin, 2),
        "loyalty_flex_pct": round(loyalty_flex * 100, 1),
        "effective_floor": round(effective_floor, 2),
        "buyer_offer":     round(buyer_offer, 2),
    }

    names = ", ".join(p["name"] for p in products)

    # ── Decision tree ─────────────────────────────────────────────────────────

    # Full acceptance
    if buyer_offer >= list_total:
        return {
            "outcome": "accept",
            "final_price": list_total,
            "message": f"Deal! You've got {names} at the full list price ₹{list_total:.0f}. Adding to your order now.",
            "counter_items": products,
            "discount_pct": 0,
            "payoff_data": payoff,
        }

    # ≤ 5% below list: round-off discount
    if buyer_offer >= list_total * 0.95:
        disc = round(list_total - buyer_offer, 0)
        return {
            "outcome": "accept",
            "final_price": buyer_offer,
            "message": f"That works! I'll round it down to ₹{buyer_offer:.0f} for you — saving ₹{disc:.0f} on {names}. ✅",
            "counter_items": products,
            "discount_pct": round((1 - buyer_offer / list_total) * 100, 1),
            "payoff_data": payoff,
        }

    # 5–10% below list: counter with marginal concession
    if buyer_offer >= list_total * 0.90:
        counter = round(list_total * 0.92, 0)
        return {
            "outcome": "counter",
            "final_price": counter,
            "message": (
                f"Close! Best I can do is ₹{counter:.0f} for {names} — "
                f"that's an 8% discount off ₹{list_total:.0f}. Want to accept?"
            ),
            "counter_items": products,
            "discount_pct": 8.0,
            "payoff_data": payoff,
        }

    # Offer covers cost + decent margin → counter with a swap
    if buyer_offer >= effective_floor:
        gap = list_total - buyer_offer
        swap = _find_cheaper_swap(products[0], buyer_offer * 0.8) if len(products) == 1 else None
        if swap:
            new_total = round(buyer_offer * 0.97, 0)
            return {
                "outcome": "counter",
                "final_price": new_total,
                "message": (
                    f"I can't hit ₹{buyer_offer:.0f} for {names}, but I can swap it "
                    f"for **{swap['name']}** (₹{swap['price']:.0f}) and give you "
                    f"the bundle for ₹{new_total:.0f}. That's still {round((1-new_total/list_total)*100)}% off!"
                ),
                "counter_items": [swap, *products[1:]],
                "discount_pct": round((1 - new_total / list_total) * 100, 1),
                "payoff_data": {**payoff, "swap": swap["name"]},
            }
        # No swap → offer a high-margin add-on to recover revenue
        addon = _find_high_margin_addon(gap)
        if addon:
            counter = round(buyer_offer + addon["price"] * 0.5, 0)
            return {
                "outcome": "counter",
                "final_price": counter,
                "message": (
                    f"I can do ₹{buyer_offer:.0f} for {names} if you add "
                    f"**{addon['name']}** (₹{addon['price']:.0f}) to the order "
                    f"— total comes to ₹{counter:.0f}. Deal?"
                ),
                "counter_items": [*products, addon],
                "discount_pct": round((1 - buyer_offer / list_total) * 100, 1),
                "payoff_data": {**payoff, "addon": addon["name"]},
            }
        # Plain counter at effective floor
        counter = round(effective_floor, 0)
        return {
            "outcome": "counter",
            "final_price": counter,
            "message": (
                f"The lowest I can go on {names} is ₹{counter:.0f} — "
                f"that's {round((1-counter/list_total)*100)}% off the ₹{list_total:.0f} list price."
            ),
            "counter_items": products,
            "discount_pct": round((1 - counter / list_total) * 100, 1),
            "payoff_data": payoff,
        }

    # Offer below cost floor
    return {
        "outcome": "decline",
        "final_price": round(effective_floor, 0),
        "message": (
            f"I'm afraid ₹{buyer_offer:.0f} is below what I can offer for {names}. "
            f"My absolute best price is ₹{round(effective_floor, 0):.0f}. "
            f"Want to accept that, or would you like a cheaper alternative?"
        ),
        "counter_items": products,
        "discount_pct": round((1 - effective_floor / list_total) * 100, 1),
        "payoff_data": payoff,
    }


def detect_bargain_intent(message: str) -> Tuple[bool, float]:
    """
    Returns (is_bargain_request, offered_amount).

    Conservative: only treats a message as a price negotiation when it contains an
    EXPLICIT bargaining phrase. Product-search / filter queries (which often contain
    a number and the word "budget", e.g. "show me fruits within my ₹8000 budget")
    are NEVER treated as bargains.
    """
    msg = (message or "").lower()

    # 1. If the message is clearly a product search / filter, it's NOT a bargain.
    new_search_signals = (
        "show", "recommend", "suggest", "option", "within my", "within ₹",
        "looking for", "find me", "more product", "more option", "give me some",
        "i need", "i want some", "browse", "list ", "what do you have",
    )
    if any(s in msg for s in new_search_signals):
        return False, 0.0

    # 2. Explicit bargaining phrases.
    bargain_phrases = [
        r"\bcan you do (?:it|this|that)?\b", r"\bdo it for\b", r"\bmake it\b",
        r"\bhow about\b", r"\bi(?:'ll| will| would| can)? pay\b", r"\bi can pay\b", r"\bgive (?:me|it) for\b",
        r"\blet'?s do\b", r"\bbest price\b", r"\bany discount\b",
        r"\bgive me a discount\b", r"\bbargain\b", r"\bnegotiat", r"\bhaggle\b",
        r"\blower (?:the )?price\b", r"\btoo expensive\b", r"\bcheaper deal\b",
    ]
    matched = any(re.search(p, msg) for p in bargain_phrases)
    if not matched:
        return False, 0.0

    # 3. Extract an offered amount if present (≥ 2 digits to avoid quantities like "2").
    amt = re.search(r"(?:[₹]|rs\.?\s*)?(\d{2,7})\b", msg)
    offer = float(amt.group(1)) if amt else 0.0
    return True, offer

