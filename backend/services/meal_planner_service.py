"""
Weekly Meal Planner -> Auto Shopping List
=========================================
Generates a structured multi-day meal plan via the LLM, maps every ingredient to
real catalog products, then DEDUPLICATES and SCALES quantities across all meals
into a single optimized shopping list.

Public functions:
  - generate_plan(goal, days, servings, preferences) -> full plan + shopping list
  - consolidate_ingredients(ingredient_names, servings) -> shopping list only
        (used when the user edits/removes meals on the client and rebuilds the list)
"""
import json
import re
from collections import defaultdict
from typing import Dict, List, Optional

from config import settings
from services.product_service import load_products


def generate_plan(
    goal: str = "balanced healthy meals",
    days: int = 7,
    servings: int = 2,
    preferences: Optional[Dict] = None,
) -> Dict:
    """Ask the LLM for a structured N-day meal plan."""
    days = max(1, min(7, int(days or 7)))
    pref_bits = []
    if preferences:
        if preferences.get("is_vegetarian"):
            pref_bits.append("vegetarian only")
        if preferences.get("is_vegan"):
            pref_bits.append("vegan only")
        if preferences.get("is_high_protein"):
            pref_bits.append("high-protein")
        if preferences.get("weight_loss_mode"):
            pref_bits.append("low-calorie / weight-loss friendly")
    pref_str = (" Constraints: " + ", ".join(pref_bits) + ".") if pref_bits else ""

    prompt = (
        f"Create a {days}-day meal plan for {servings} people. Goal: {goal}.{pref_str}\n"
        f"For each day include breakfast, lunch and dinner. Keep dishes simple and Indian-friendly.\n"
        f"Respond ONLY with JSON in this exact shape:\n"
        f'{{"days":[{{"day":"Monday","meals":[{{"type":"Breakfast","dish":"Veg Poha",'
        f'"ingredients":["poha","onion","potato","peanuts","turmeric"]}}]}}]}}\n'
        f"Use lowercase single-word or two-word ingredient names. No quantities, no extra text."
    )

    try:
        from services.llm_service import _chat_complete
        content = _chat_complete(
            [{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.4,
        ).strip()
        if "```" in content:
            content = content.split("```")[1].replace("json", "", 1).strip()
        data = json.loads(content)
        plan_days = data.get("days", [])
    except Exception as e:
        print(f"Meal plan LLM error: {e}")
        plan_days = []

    # Attach a stable id to every meal so the client can toggle/remove them
    for di, day in enumerate(plan_days):
        for mi, meal in enumerate(day.get("meals", [])):
            meal["id"] = f"d{di}m{mi}"
            meal["ingredients"] = [str(i).lower().strip() for i in meal.get("ingredients", []) if i]

    # Collect all ingredients and build the consolidated shopping list
    all_ingredients = []
    for day in plan_days:
        for meal in day.get("meals", []):
            all_ingredients.extend(meal.get("ingredients", []))

    shopping = consolidate_ingredients(all_ingredients, servings)

    return {
        "goal": goal,
        "days_count": days,
        "servings": servings,
        "plan": plan_days,
        "shopping_list": shopping["shopping_list"],
        "total": shopping["total"],
        "unmatched": shopping["unmatched"],
    }


# ── Ingredient -> product matching ───────────────────────────────────────────

# common pantry staples that are bought in bulk (don't scale qty with servings)
_STAPLE_HINTS = {"salt", "oil", "turmeric", "masala", "spice", "spices", "sugar",
                 "flour", "atta", "rice", "pepper", "chilli", "chili", "powder"}


def _match_product(ingredient: str, products: List[Dict]) -> Optional[Dict]:
    """Find the best catalog product for an ingredient name."""
    ing = ingredient.lower().strip()
    ing_words = [w for w in re.findall(r"\w+", ing) if len(w) > 2]
    if not ing_words:
        return None

    best = None
    best_score = 0
    for p in products:
        if not p.get("in_stock", True):
            continue
        # Meal ingredients are food — only match grocery items (never kitchen tools etc.)
        if p.get("category") != "groceries":
            continue
        name = p["name"].lower()
        tags = " ".join(p.get("tags", [])).lower()
        hay = f"{name} {tags}"
        score = 0
        for w in ing_words:
            if re.search(r"\b" + re.escape(w) + r"\b", name):
                score += 3
            elif w in name:
                score += 2
            elif w in tags:
                score += 1
        # whole-ingredient exact hit
        if ing in name:
            score += 4
        if score > best_score:
            best_score = score
            best = p
    return best if best_score >= 2 else None


def consolidate_ingredients(ingredient_names: List[str], servings: int = 2) -> Dict:
    """
    Deduplicate ingredients across meals, map each to a product, and sum the
    quantity (number of meals that need it) — scaled lightly by servings.
    """
    products = load_products()

    # Count how many meals reference each ingredient
    freq: Dict[str, int] = defaultdict(int)
    for ing in ingredient_names:
        freq[ing.lower().strip()] += 1

    shopping = []
    unmatched = []
    seen_products = {}

    for ing, count in freq.items():
        product = _match_product(ing, products)
        if not product:
            unmatched.append(ing)
            continue

        # staples → qty 1 regardless; perishables → scale by usage & servings
        is_staple = any(h in ing for h in _STAPLE_HINTS)
        if is_staple:
            qty = 1
        else:
            qty = max(1, round(count * max(1, servings) / 2))

        pid = product["id"]
        if pid in seen_products:
            seen_products[pid]["quantity"] += qty
            if ing not in seen_products[pid]["for_ingredients"]:
                seen_products[pid]["for_ingredients"].append(ing)
        else:
            entry = {
                **product,
                "quantity": qty,
                "for_ingredients": [ing],
            }
            seen_products[pid] = entry
            shopping.append(entry)

    total = sum(p["price"] * p["quantity"] for p in shopping)
    return {
        "shopping_list": shopping,
        "total": round(total, 0),
        "unmatched": unmatched,
    }
