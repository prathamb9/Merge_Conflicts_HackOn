"""
Group / Shared Cart — Real-Time Consensus Engine
================================================
Given a group session's members (with dietary prefs) and the proposed items
(with votes), this resolves the group into a recommended final cart:

  - ranks items by votes (descending)
  - detects DIETARY CONFLICTS (e.g. a non-veg item when a vegetarian/vegan
    member is present) and suggests a compatible swap from the same category
  - produces a friendly, agent-style consensus summary

Rule-based (deterministic) so it is fast and reliable — no LLM dependency.
"""
import json
import random
import string
from typing import Dict, List, Optional

from services.product_service import get_product_by_id, load_products


def generate_code(n: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


def _find_veg_alternative(product: Dict, need_vegan: bool) -> Optional[Dict]:
    """Find an in-stock veg/vegan product in the same category at a similar price.
    For meat/seafood items, prefer protein-rich veg alternatives (paneer, soya, etc.)."""
    products = load_products()
    cat = product.get("category")
    price = product.get("price", 0)
    tags = set(product.get("tags", []))
    is_protein_swap = bool(tags & {"meat", "seafood"}) or product.get("is_high_protein")
    candidates = []
    for p in products:
        if p["id"] == product["id"] or not p.get("in_stock", True):
            continue
        if p["category"] != cat:
            continue
        if need_vegan and not p.get("is_vegan"):
            continue
        if not p.get("is_vegetarian"):
            continue
        overlap = len(tags & set(p.get("tags", [])))
        # Boost protein-rich veg options when replacing meat/seafood
        protein_boost = 2 if (is_protein_swap and p.get("is_high_protein")) else 0
        price_diff = abs(p.get("price", 0) - price)
        candidates.append((p, overlap + protein_boost, price_diff))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (-x[1], x[2]))
    return candidates[0][0]


def resolve_consensus(members: List, items: List) -> Dict:
    """
    members: list of GroupMember
    items:   list of GroupItem
    Returns a consensus dict for the frontend.
    """
    has_vegetarian = any(m.is_vegetarian or m.is_vegan for m in members)
    has_vegan = any(m.is_vegan for m in members)
    member_count = max(1, len(members))

    resolved = []
    conflicts = []

    # Rank items by vote count
    def vote_count(it):
        try:
            return len(json.loads(it.votes or "[]"))
        except Exception:
            return 0

    sorted_items = sorted(items, key=vote_count, reverse=True)

    for it in sorted_items:
        product = get_product_by_id(it.product_id)
        if not product:
            continue
        votes = vote_count(it)
        entry = {
            "item_id": it.id,
            "product": product,
            "votes": votes,
            "added_by": it.added_by,
            "status": "approved",
            "note": "",
        }

        # Dietary conflict detection
        is_conflict = False
        if has_vegan and not product.get("is_vegan"):
            is_conflict = True
            need_vegan = True
        elif has_vegetarian and not product.get("is_vegetarian"):
            is_conflict = True
            need_vegan = False

        if is_conflict:
            alt = _find_veg_alternative(product, need_vegan)
            diet_label = "vegan" if (has_vegan and not product.get("is_vegan")) else "vegetarian"
            if alt:
                entry["status"] = "swapped"
                entry["note"] = (
                    f"{product['name']} isn't {diet_label}-friendly — swapped to "
                    f"{alt['name']} so everyone can enjoy it."
                )
                entry["suggested_alternative"] = alt
                conflicts.append({
                    "original": product,
                    "alternative": alt,
                    "reason": f"A {diet_label} member is in the group",
                })
            else:
                entry["status"] = "flagged"
                entry["note"] = f"{product['name']} isn't {diet_label}-friendly and no good swap was found."
                conflicts.append({
                    "original": product,
                    "alternative": None,
                    "reason": f"A {diet_label} member is in the group",
                })

        resolved.append(entry)

    # Build the recommended final cart (use swaps where present)
    final_cart = []
    total = 0.0
    for r in resolved:
        if r["status"] == "flagged":
            continue
        prod = r.get("suggested_alternative") or r["product"]
        final_cart.append({**prod, "votes": r["votes"]})
        total += prod.get("price", 0)

    # Consensus message
    veg_note = ""
    if has_vegan:
        veg_note = " I kept everything 100% vegan since a vegan member is in the group."
    elif has_vegetarian:
        veg_note = " I kept everything vegetarian-friendly for the group."

    if not resolved:
        message = "No items yet — start adding products and the group can vote on them!"
    elif conflicts:
        message = (
            f"I resolved {len(conflicts)} dietary conflict(s) so everyone's happy.{veg_note} "
            f"Here's the group-approved cart of {len(final_cart)} items (₹{total:.0f})."
        )
    else:
        message = (
            f"Great consensus! All {len(final_cart)} items work for the whole group "
            f"(₹{total:.0f}).{veg_note}"
        )

    return {
        "resolved_items": resolved,
        "conflicts": conflicts,
        "final_cart": final_cart,
        "final_total": round(total, 0),
        "member_count": member_count,
        "has_vegetarian": has_vegetarian,
        "has_vegan": has_vegan,
        "message": message,
    }
