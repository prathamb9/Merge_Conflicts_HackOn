from groq import Groq
from typing import List, Dict, Optional
import json
from datetime import datetime

from config import settings
from services.product_service import get_catalog_summary
from services.rag_service import query_relevant_products, query_relevant_products_with_substitution
from services.context_service import get_contextual_triggers

client = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """You are QuickBot, an AI shopping assistant for an online store (like Amazon) that sells a wide variety of products: electronics, smartphones, laptops, fashion, beauty, fragrances, furniture, groceries, accessories and more.

Your job: help users find products using natural language and build an optimised shopping basket within their budget.

You will receive the user's request and the available product catalog. Respond ONLY with valid JSON in exactly this format:
{
  "message": "friendly conversational response in 1-2 sentences",
  "recommendations": [
    {
      "id": "product_id from catalog",
      "name": "exact product name from catalog",
      "price": 99,
      "category": "category name",
      "brand": "brand name",
      "unit": "quantity/unit",
      "reason": "why this product fits the request"
    }
  ],
  "total": 999,
  "reasoning": "brief explanation of your overall selection logic"
}

Rules:
- ONLY recommend products with in_stock: true from the catalog
- BUDGET IS THE PRIMARY CONSTRAINT. The combined total of all recommendations MUST be <= the user's budget, and should use as much of the budget as reasonably possible (aim for 80-100% of the budget).
- SCALE THE NUMBER OF ITEMS WITH THE BUDGET: a larger budget means MORE items. As a guide, recommend roughly 1 item per ₹60-₹100 of budget. Always recommend at least 3 items.
- For a LARGER budget, you may include costlier/premium products; for a SMALLER budget, prefer cheaper/value products so you can fit more items.
- Match the product category to the user's request (e.g. "gift for her" -> jewellery/bags/beauty; "work setup" -> laptops/accessories).
- total = sum of all recommended product prices
- NEVER invent products not in the catalog
- Keep message friendly and conversational (use ₹ for currency)
- Respond ONLY with JSON, no markdown code blocks, no extra text"""


def get_chat_response(
    message: str,
    history: List[Dict],
    user_profile: Optional[Dict] = None,
    user_id: Optional[str] = None,
    cart_value: float = 0.0,
) -> Dict:
    """
    Main chat function with context-awareness, substitution, and cart optimization.
    """
    # Get active dietary filters from user profile
    filters = {}
    budget = 500
    if user_profile:
        filters = {
            "is_vegetarian": user_profile.get("is_vegetarian"),
            "is_vegan": user_profile.get("is_vegan"),
            "is_high_protein": user_profile.get("is_high_protein")
        }
        budget = user_profile.get("budget_preference") or 500

    # Scale the candidate pool with the budget
    target_items = max(3, min(20, budget // 2500))
    candidate_limit = max(20, min(60, target_items * 4))

    # Retrieve semantically relevant products matching the query and filters
    # This automatically handles out-of-stock substitutions
    relevant_products = query_relevant_products_with_substitution(
        query=message, 
        limit=candidate_limit, 
        filters=filters
    )
    
    # Group results by category for clean LLM context
    by_category = {}
    for p in relevant_products:
        cat = p["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append({
            "id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "brand": p["brand"],
            "unit": p["unit"],
            "in_stock": p["in_stock"],
            "image_url": p["image_url"],
            "tags": p["tags"],
            "is_vegetarian": p["is_vegetarian"],
            "is_vegan": p["is_vegan"],
            "is_high_protein": p["is_high_protein"],
        })
    catalog = json.dumps(by_category, ensure_ascii=False)

    # Build contextual profile string
    profile_context = ""
    prefs = []
    if user_profile:
        if user_profile.get("is_vegetarian"):
            prefs.append("vegetarian")
        if user_profile.get("is_vegan"):
            prefs.append("vegan")
        if user_profile.get("is_high_protein"):
            prefs.append("high-protein diet")
    pref_str = f" Dietary preferences: {', '.join(prefs)}." if prefs else ""
    profile_context = (
        f"\n\nUSER BUDGET: ₹{budget}. The total of all recommendations MUST stay within "
        f"₹{budget} and should use most of it (aim for 80-100% of the budget). "
        f"Recommend approximately {target_items} different products (you may go slightly "
        f"over or under to best fit the budget, but never exceed the budget total)."
        f"{pref_str}"
    )

    # Add contextual triggers (weather, time, events)
    contextual_info = get_contextual_triggers()
    if contextual_info:
        profile_context += f"\n\nCONTEXTUAL INFO: {contextual_info}"

    # Add cart optimization hint if close to threshold
    if cart_value > 0:
        gap = settings.free_delivery_threshold - cart_value
        if 0 < gap < 100:
            profile_context += (
                f"\n\nCART OPTIMIZATION: User's cart is at ₹{cart_value:.0f}. "
                f"They are ₹{gap:.0f} away from free delivery (₹{settings.free_delivery_threshold}). "
                f"Proactively suggest low-cost items they might need to cross the threshold "
                f"and save ₹{settings.delivery_charge} on delivery!"
            )

    system_text = SYSTEM_PROMPT + profile_context + f"\n\nPRODUCT CATALOG (JSON):\n{catalog}"

    # Build message history for Groq (limit to last 6 messages)
    messages = [{"role": "system", "content": system_text}]
    filtered_history = history[-6:]
    if filtered_history and filtered_history[0].get("role") == "assistant":
        filtered_history = filtered_history[1:]
        
    for h in filtered_history:
        messages.append({"role": h["role"], "content": h["content"]})

    # Reinforce JSON format on current turn
    user_turn = (
        f"{message}\n\n"
        f"(Respond ONLY with a single valid JSON object in the required format with "
        f"'message', 'recommendations', 'total', and 'reasoning' fields. Recommend about "
        f"{target_items} products and keep the total within ₹{budget}. "
        f"Do not include any text outside the JSON.)"
    )
    messages.append({"role": "user", "content": user_turn})

    # Call Groq API
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=0.3,
        max_tokens=4096,
    )

    content = response.choices[0].message.content
    
    # Clean JSON extraction
    content_str = content.strip()
    if "```json" in content_str:
        content_str = content_str.split("```json")[1].split("```")[0].strip()
    elif "```" in content_str:
        content_str = content_str.split("```")[1].split("```")[0].strip()

    try:
        result = json.loads(content_str)
    except json.JSONDecodeError as e:
        print(f"LLM JSON parse error: {e}. Raw content: {content_str[:200]}")
        result = {}

    # Ensure required fields exist
    result.setdefault("message", "Here are my recommendations for you!")
    result.setdefault("recommendations", [])
    result.setdefault("reasoning", "Based on your request")

    # Enrich recommendations with REAL product data from the catalog
    from services.product_service import get_product_by_id

    enriched = []
    seen_ids = set()
    for rec in result["recommendations"]:
        pid = rec.get("id")
        if not pid or pid in seen_ids:
            continue
        product = get_product_by_id(pid)
        if not product:
            continue
        if not product.get("in_stock", True):
            continue
        seen_ids.add(pid)
        merged = dict(product)
        if rec.get("reason"):
            merged["reason"] = rec["reason"]
        enriched.append(merged)

    result["recommendations"] = enriched

    # Enforce budget as hard cap
    if budget and enriched:
        kept = []
        running = 0
        for item in enriched:
            price = item.get("price", 0) or 0
            if running + price <= budget:
                kept.append(item)
                running += price
        if not kept:
            cheapest = min(enriched, key=lambda x: x.get("price", 0) or 0)
            kept = [cheapest]
            running = cheapest.get("price", 0) or 0
        result["recommendations"] = kept
        result["total"] = running
    else:
        result["total"] = sum(r.get("price", 0) for r in enriched)

    return result


def parse_recipe_to_ingredients(recipe_query: str, servings: int = 2) -> List[str]:
    """
    Parse a recipe request into a list of required ingredients using the LLM.
    
    Example: "Paneer Butter Masala for 3 people" -> ["paneer", "butter", "tomatoes", "cream", ...]
    """
    prompt = f"""User wants to cook: "{recipe_query}" for {servings} people.

List ONLY the raw ingredients needed (no quantities, no instructions).
Output as a simple JSON array of ingredient names in lowercase.

Example output: ["paneer", "butter", "tomatoes", "cream", "garam masala", "kasuri methi"]

Response:"""

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=500,
    )

    content = response.choices[0].message.content.strip()
    
    # Extract JSON array
    if "```" in content:
        content = content.split("```")[1].replace("json", "").strip()
    
    try:
        ingredients = json.loads(content)
        return [ing.lower().strip() for ing in ingredients if isinstance(ing, str)]
    except:
        # Fallback: parse as comma-separated
        return [ing.strip().lower() for ing in content.replace("[", "").replace("]", "").replace('"', "").split(",")]
