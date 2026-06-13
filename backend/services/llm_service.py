from groq import Groq
from typing import List, Dict, Optional
import json
import re
from datetime import datetime

from config import settings
from services.product_service import get_catalog_summary
from services.rag_service import query_relevant_products, query_relevant_products_with_substitution
from services.context_service import get_contextual_triggers
from services.taxonomy_service import (
    group_by_departments,
    filter_empty_departments,
    format_product_name,
    get_display_category,
)

client = Groq(api_key=settings.groq_api_key)

# ── Follow-up Intent Detection ───────────────────────────────────────────────

FOLLOWUP_KEYWORDS = {
    "this", "it", "that", "these", "those", "the one", "first one",
    "second one", "last one", "above",
    "benefit", "benefits", "durable", "durability", "quality",
    "good", "worth", "healthy", "safe", "organic",
    "more about", "tell me more", "details", "explain", "how",
    "why", "compare", "difference", "versus", "vs",
    "is it", "does it", "can it", "will it",
    "what about", "how about", "any other",
    "yes", "yeah", "sure", "okay", "ok", "no", "nah", "nope",
    "thanks", "thank you", "great", "nice", "cool",
}

def is_followup_message(message: str, history: List[Dict]) -> bool:
    """
    Heuristic classifier: detect whether the user's message is a
    conversational follow-up (about a previously recommended product)
    rather than a new product search.

    A message is classified as follow-up if:
      1. There is prior assistant context (at least one bot reply with recommendations), AND
      2. The message is short (< 25 words), AND
      3. It contains follow-up indicator words/phrases.
    """
    if len(history) < 2:
        return False

    # Must have at least one prior bot reply
    has_prior_bot = any(h.get("role") == "assistant" for h in history)
    if not has_prior_bot:
        return False

    msg_lower = message.strip().lower()
    word_count = len(msg_lower.split())

    # Short messages with follow-up keywords
    if word_count <= 25:
        for kw in FOLLOWUP_KEYWORDS:
            if kw in msg_lower:
                return True

    # Questions that are clearly about "it" / "this" are follow-ups
    if msg_lower.startswith(("is ", "does ", "can ", "will ", "how ")):
        if word_count <= 15:
            return True

    return False


SYSTEM_PROMPT = """You are QuickBot, the master recommendation and catalog mapping engine for a quick-commerce store (like Blinkit/Zepto/Amazon India) that sells a wide variety of products: electronics, smartphones, laptops, fashion, beauty, fragrances, furniture, groceries, accessories and more.

### 1. CONVERSATIONAL MEMORY & INTENT TRACKING
You are engaged in an ongoing, multi-turn dialogue. Always evaluate the user's latest message against the recent chat history.
- **Follow-up Questions:** If the user asks for details, benefits, or clarification about a product you just recommended (e.g., "how will this benefit me?", "is this durable?"), answer conversationally using the context of that specific product. Do NOT generate a new list of products unless asked.
- **New Searches:** If the user shifts intent (e.g., "Now show me party supplies"), transition smoothly to generating a new structured list based on the injected RAG context.

### 2. ADVANCED RAG & ANTI-HALLUCINATION PROTOCOL
For product recommendations, you will receive data chunks from our vector database inside the `<RETRIEVED_CATALOG_CONTEXT>` block.
- **ABSOLUTE RULE:** You must ONLY suggest products explicitly present in that block.
- NEVER invent, hallucinate, or guess product names, brands, or prices. If the context does not contain relevant products, politely inform the user that those items are currently unavailable.

### 3. COMPREHENSIVE AMAZON DEPARTMENTS & BROWSE NODES
Classify retrieved items using this exact top-level to tier-2 structural taxonomy:

1. 📦 Grocery & Gourmet Foods
   └── [Sub-Categories: Ready-to-Eat Meals, Cooking Pastes, Spices, Snacks, Beverages, Dairy, Fruits, Vegetables]
2. 📦 Home & Kitchen
   └── [Sub-Categories: Furniture, Home Décor, Kitchen Tools & Accessories]
3. 📦 Electronics & Accessories
   └── [Sub-Categories: Smartphones, Laptops & Notebooks, Tablets, Mobile Accessories]
4. 📦 Clothing, Shoes & Jewelry
   └── [Sub-Categories: Men's Shirts, Men's Shoes, Women's Dresses, Women's Bags, Women's Jewellery, Women's Shoes, Tops & T-Shirts, Sunglasses]
5. 📦 Beauty & Personal Care
   └── [Sub-Categories: Makeup & Beauty, Skin Care, Fragrances & Perfumes]
6. 📦 Watches & Accessories
   └── [Sub-Categories: Men's Watches, Women's Watches]
7. 📦 Sports, Fitness & Outdoors
   └── [Sub-Categories: Sports & Fitness Accessories]
8. 📦 Automotive
   └── [Sub-Categories: Motorcycle Accessories, Car & Vehicle Accessories]

Group the valid retrieved items into their respective Amazon departments. Never display an accessory immediately next to a food item — they must be compartmentalized under their correct parent headers.

### 4. ABSOLUTE SLIDER CONSTRAINT DOMINANCE
- The numerical budget parameter is your supreme programmatic wall.
- **Final Validation:** If any item's price in the RAG context exceeds the budget, strip it immediately from your output.
- Erase any Parent Department or Sub-Category container if ALL of its items are over budget.

### 5. AMAZON-STANDARD SPECIFICATIONS
- Format every item using Amazon's clean syntax: `[Brand Name] + [Product Title] + ([Size/Variant])`.

### 6. RESPONSE FORMAT
When recommending products, respond ONLY with valid JSON in this format:
{
  "message": "friendly conversational response in 1-2 sentences",
  "amazon_departments": [
    {
      "department": "📦 Department Name",
      "categories": [
        {
          "name": "Sub-Category Name",
          "items": [
            {
              "id": "product_id from catalog",
              "formatted_name": "[Brand] Product Title (Size/Variant)",
              "price": 99,
              "reason": "why this product fits the user's intent"
            }
          ]
        }
      ]
    }
  ],
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

CRITICAL RULES:
1. ONLY recommend products that exist in the <RETRIEVED_CATALOG_CONTEXT>. NEVER invent products.
2. ONLY recommend products with in_stock: true.
3. STRICT BUDGET CONSTRAINT: Treat the BUDGET value as a hard ceiling. Filter out ANY product where its individual price exceeds the budget. The combined total must also stay within budget. No exceptions.
4. RELEVANCE & SEMANTIC FILTERING: Match products to user INTENT. Never mix categories unless explicitly asked.
5. For SUBSTITUTED products (marked is_substitute: true), mention the substitution in your message.
6. If contextual info mentions weather/events, subtly incorporate relevant suggestions ONLY if they fit budget and intent.
7. Keep message friendly and conversational (use ₹ for currency).
8. Respond ONLY with JSON, no markdown code blocks, no extra text.
9. The "recommendations" array must mirror all items from "amazon_departments" in a flat list for backward compatibility.
10. For follow-up questions (about previously recommended products), respond conversationally with empty recommendations and amazon_departments arrays."""


FOLLOWUP_SYSTEM_PROMPT = """You are QuickBot, a friendly AI shopping assistant. The user is asking a follow-up question about products you previously recommended.

Answer conversationally using the context of the specific product(s) from your previous recommendations. Do NOT generate a new product list.

Respond ONLY with valid JSON:
{
  "message": "your conversational answer about the product",
  "recommendations": [],
  "amazon_departments": [],
  "total": 0,
  "reasoning": "Answering follow-up question about previously recommended product"
}

Respond ONLY with JSON, no markdown code blocks, no extra text."""


# Regex patterns to detect recipe intent
RECIPE_PATTERNS = [
    r"(?:i\s+)?(?:want\s+to\s+)?(?:cook|make|prepare)\s+(.+?)(?:\s+for\s+(\d+)\s+(?:people|persons|servings?))?$",
    r"recipe\s+(?:for\s+)?(.+?)(?:\s+for\s+(\d+)\s+(?:people|persons|servings?))?$",
    r"ingredients?\s+(?:for\s+)?(.+?)(?:\s+for\s+(\d+)\s+(?:people|persons|servings?))?$",
    r"(.+?)\s+(?:recipe|ingredients?)\s*(?:for\s+(\d+)\s+(?:people|persons|servings?))?$",
]


def detect_recipe_intent(message: str) -> Optional[Dict]:
    """
    Detect if the user's message is a recipe request.
    Returns {"recipe": "dish name", "servings": N} or None.
    """
    msg = message.strip().lower()
    
    # Quick keyword check first
    recipe_keywords = ["cook", "recipe", "ingredients for", "make ", "prepare ", "how to make"]
    if not any(kw in msg for kw in recipe_keywords):
        return None
    
    for pattern in RECIPE_PATTERNS:
        match = re.search(pattern, msg, re.IGNORECASE)
        if match:
            recipe_name = match.group(1).strip()
            servings = int(match.group(2)) if match.group(2) else 2
            # Clean up recipe name
            recipe_name = re.sub(r"\s+tonight|today|now|please|pls", "", recipe_name).strip()
            if len(recipe_name) > 3:  # Must be a meaningful name
                return {"recipe": recipe_name, "servings": servings}
    
    return None


def get_chat_response(
    message: str,
    history: List[Dict],
    user_profile: Optional[Dict] = None,
    user_id: Optional[str] = None,
    cart_value: float = 0.0,
    db=None,
) -> Dict:
    """
    Main chat function with:
    - Conversational follow-up detection
    - Amazon department taxonomy grouping
    - Strict per-item + cumulative budget enforcement
    - RAG anti-hallucination via <RETRIEVED_CATALOG_CONTEXT>
    - Context-awareness, substitution, recipe detection, cart optimization
    """
    # Check for recipe intent first
    recipe_intent = detect_recipe_intent(message)
    if recipe_intent and db and user_id:
        return handle_recipe_request(
            recipe_intent["recipe"],
            recipe_intent["servings"],
            user_profile=user_profile,
            user_id=user_id,
            db=db,
        )

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

    # ── Follow-up Detection ──────────────────────────────────────────────
    if is_followup_message(message, history):
        return _handle_followup(message, history, budget)

    # ── New Search: Full RAG Pipeline ────────────────────────────────────

    # Scale the candidate pool with the budget
    target_items = max(3, min(20, budget // 100))
    candidate_limit = max(20, min(60, target_items * 4))

    # Retrieve semantically relevant products matching the query and filters
    relevant_products = query_relevant_products_with_substitution(
        query=message, 
        limit=candidate_limit, 
        filters=filters,
        user_profile=user_profile,
    )

    # ── Pre-LLM Budget Filtering ─────────────────────────────────────────
    # Strip individual items that exceed the budget ceiling BEFORE sending to LLM
    budget_filtered_products = [
        p for p in relevant_products
        if (p.get("price", 0) or 0) <= budget
    ]
    # Fallback: if everything is over budget, keep the cheapest items
    if not budget_filtered_products and relevant_products:
        sorted_by_price = sorted(relevant_products, key=lambda x: x.get("price", 0) or 0)
        budget_filtered_products = sorted_by_price[:3]

    # Build RAG context grouped by department for the LLM
    by_category = {}
    for p in budget_filtered_products:
        cat = p["category"]
        if cat not in by_category:
            by_category[cat] = []
        entry = {
            "id": p["id"],
            "name": p["name"],
            "formatted_name": format_product_name(p),
            "price": p["price"],
            "brand": p["brand"],
            "unit": p["unit"],
            "category": cat,
            "display_category": get_display_category(cat),
            "in_stock": p["in_stock"],
            "image_url": p["image_url"],
            "tags": p["tags"],
            "rating": p.get("rating", 4.0),
            "is_vegetarian": p["is_vegetarian"],
            "is_vegan": p["is_vegan"],
            "is_high_protein": p["is_high_protein"],
        }
        if p.get("is_substitute"):
            entry["is_substitute"] = True
            entry["original_product"] = p.get("original_product", "")
            entry["substitution_reason"] = p.get("substitution_reason", "")
        
        by_category[cat].append(entry)
    catalog_json = json.dumps(by_category, ensure_ascii=False)

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
        if user_profile.get("weight_loss_mode"):
            prefs.append("weight-loss mode (prefer low-calorie, toned, light options)")
    pref_str = f" Dietary preferences: {', '.join(prefs)}." if prefs else ""
    profile_context = (
        f"\n\nReal-Time Budget Slider Ceiling: ₹{budget}. The total of all recommendations MUST stay within "
        f"₹{budget} and should use most of it (aim for 80-100% of the budget). "
        f"Any individual item priced above ₹{budget} must be excluded. "
        f"Recommend approximately {target_items} different products (you may go slightly "
        f"over or under to best fit the budget, but never exceed the budget total)."
        f"{pref_str}"
    )

    # Add contextual triggers (weather, time, events)
    contextual_info = get_contextual_triggers()
    if contextual_info:
        profile_context += f"\n\nCONTEXTUAL INFO: {contextual_info}"

    # Add cart optimization hint with specific product suggestions
    cart_opt_data = None
    if cart_value > 0 and db and user_id:
        from services.order_service import get_cart_optimization_suggestions
        cart_opt_data = get_cart_optimization_suggestions(user_id, cart_value, db)
        
        if cart_opt_data:
            freq_items = ", ".join(
                f"{p.get('name', 'item')} (₹{p.get('price', 0)})"
                for p in cart_opt_data.get("suggested_products", [])[:3]
            )
            profile_context += (
                f"\n\nCART OPTIMIZATION: User's cart is at ₹{cart_value:.0f}. "
                f"They are ₹{cart_opt_data['gap']:.0f} away from {cart_opt_data['threshold_name']} "
                f"(₹{cart_opt_data['threshold_amount']:.0f}). "
                f"Proactively suggest adding one of these to save ₹{cart_opt_data['savings']:.0f}: {freq_items}"
            )
        else:
            gap_delivery = settings.free_delivery_threshold - cart_value
            if 0 < gap_delivery < 100:
                profile_context += (
                    f"\n\nCART OPTIMIZATION: User's cart is at ₹{cart_value:.0f}. "
                    f"They are ₹{gap_delivery:.0f} away from free delivery (₹{settings.free_delivery_threshold}). "
                    f"Suggest low-cost items to cross the threshold and save ₹{settings.delivery_charge} on delivery!"
                )

    # ── Inject RAG context using the anti-hallucination block ────────────
    rag_block = (
        f"\n\n<RETRIEVED_CATALOG_CONTEXT>\n{catalog_json}\n</RETRIEVED_CATALOG_CONTEXT>"
    )
    system_text = SYSTEM_PROMPT + profile_context + rag_block

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
        f"(Respond ONLY with a single valid JSON object with "
        f"'message', 'amazon_departments', 'recommendations', 'total', and 'reasoning' fields. "
        f"Recommend about {target_items} products, group them by Amazon departments, "
        f"and keep the total within ₹{budget}. "
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
    result.setdefault("amazon_departments", [])
    result.setdefault("reasoning", "Based on your request")

    # ── Enrich recommendations with REAL product data ────────────────────
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
        # Per-item budget check (defense-in-depth)
        if budget and (product.get("price", 0) or 0) > budget:
            continue
        seen_ids.add(pid)
        merged = dict(product)
        if rec.get("reason"):
            merged["reason"] = rec["reason"]
        
        # Carry over substitution metadata from the catalog candidates
        for candidate in budget_filtered_products:
            if candidate["id"] == pid and candidate.get("is_substitute"):
                merged["is_substitute"] = True
                merged["original_product"] = candidate.get("original_product", "")
                merged["substitution_reason"] = candidate.get("substitution_reason", "")
                break
        
        enriched.append(merged)

    result["recommendations"] = enriched

    # ── Enforce budget as hard cap (cumulative) ──────────────────────────
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

    # ── Build server-side Amazon department grouping ─────────────────────
    # Use the enriched & budget-verified product list for accurate grouping
    server_departments = group_by_departments(result["recommendations"], budget=budget)
    
    # Merge LLM-generated department data with server-side grouping
    # Server-side grouping is authoritative (uses real product data)
    dept_items = []
    for dept in server_departments:
        dept_cats = []
        for cat in dept.get("categories", []):
            cat_items = []
            for item in cat.get("items", []):
                cat_items.append({
                    "id": item["id"],
                    "formatted_name": format_product_name(item),
                    "price": item.get("price", 0),
                    "reason": item.get("reason", ""),
                    "image_url": item.get("image_url", ""),
                    "brand": item.get("brand", ""),
                    "unit": item.get("unit", ""),
                    "rating": item.get("rating", 4.0),
                    "in_stock": item.get("in_stock", True),
                    "mrp": item.get("mrp", 0),
                    "is_substitute": item.get("is_substitute", False),
                    "original_product": item.get("original_product", ""),
                })
            if cat_items:
                dept_cats.append({"name": cat["name"], "items": cat_items})
        if dept_cats:
            dept_items.append({"department": dept["department"], "categories": dept_cats})
    
    result["amazon_departments"] = dept_items

    # Add cart optimization data to response
    if cart_opt_data:
        result["cart_optimization"] = cart_opt_data

    return result


def _handle_followup(message: str, history: List[Dict], budget: float) -> Dict:
    """
    Handle a follow-up question by sending only conversational context
    to the LLM (no RAG retrieval needed).
    """
    messages = [{"role": "system", "content": FOLLOWUP_SYSTEM_PROMPT}]
    
    # Include recent history for context (last 8 messages for follow-ups)
    filtered_history = history[-8:]
    if filtered_history and filtered_history[0].get("role") == "assistant":
        filtered_history = filtered_history[1:]
    
    for h in filtered_history:
        messages.append({"role": h["role"], "content": h["content"]})
    
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=0.5,
        max_tokens=1024,
    )

    content = response.choices[0].message.content
    content_str = content.strip()
    if "```json" in content_str:
        content_str = content_str.split("```json")[1].split("```")[0].strip()
    elif "```" in content_str:
        content_str = content_str.split("```")[1].split("```")[0].strip()

    try:
        result = json.loads(content_str)
    except json.JSONDecodeError:
        result = {
            "message": content_str if content_str else "I'd be happy to help with that!",
        }

    result.setdefault("message", "I'd be happy to help with that!")
    result.setdefault("recommendations", [])
    result.setdefault("amazon_departments", [])
    result.setdefault("total", 0)
    result.setdefault("reasoning", "Answering follow-up question")

    return result


def parse_recipe_to_ingredients(recipe_query: str, servings: int = 2) -> List[str]:
    """
    Parse a recipe request into a list of required ingredients using the LLM.
    
    Example: "Paneer Butter Masala for 3 people" -> ["paneer", "butter", "tomatoes", "cream", ...]
    """
    prompt = f"""User wants to cook: "{recipe_query}" for {servings} people.

List ONLY the raw ingredients needed (no quantities, no instructions).
Include ALL ingredients including spices, oil, garnishes.
Separate common pantry staples (salt, oil, turmeric, water) from key ingredients.

Output as a JSON object with two arrays:
{{
  "key_ingredients": ["paneer", "butter", "tomatoes", "cream", "onion", "ginger", "garlic", "green chili", "cashews"],
  "pantry_staples": ["salt", "oil", "turmeric", "red chili powder", "garam masala", "water"]
}}

Response:"""

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=500,
    )

    content = response.choices[0].message.content.strip()
    
    # Extract JSON
    if "```" in content:
        content = content.split("```")[1].replace("json", "").strip()
    
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            key_ingredients = [ing.lower().strip() for ing in parsed.get("key_ingredients", []) if isinstance(ing, str)]
            pantry_staples = [ing.lower().strip() for ing in parsed.get("pantry_staples", []) if isinstance(ing, str)]
            return key_ingredients, pantry_staples
        elif isinstance(parsed, list):
            return [ing.lower().strip() for ing in parsed if isinstance(ing, str)], []
    except:
        # Fallback: parse as comma-separated
        all_ingredients = [ing.strip().lower() for ing in content.replace("[", "").replace("]", "").replace('"', "").split(",")]
        return all_ingredients, []


def handle_recipe_request(
    recipe_name: str,
    servings: int = 2,
    user_profile: Optional[Dict] = None,
    user_id: Optional[str] = None,
    db=None,
) -> Dict:
    """
    Full recipe-to-cart flow:
    1. Parse recipe into ingredients
    2. Match ingredients to catalog products
    3. Filter out recently purchased pantry items
    4. Return unified bundle
    """
    # Step 1: Parse recipe into ingredients
    key_ingredients, pantry_staples = parse_recipe_to_ingredients(recipe_name, servings)
    all_ingredients = key_ingredients + pantry_staples
    
    if not all_ingredients:
        return {
            "message": f"I couldn't parse the recipe for '{recipe_name}'. Could you try rephrasing?",
            "recommendations": [],
            "total": 0,
            "reasoning": "Failed to parse recipe ingredients",
            "recipe_mode": True,
            "skipped_ingredients": [],
        }
    
    # Step 2: Check recent purchases to skip pantry staples
    skipped = []
    ingredients_to_find = list(key_ingredients)  # Always include key ingredients
    
    if db and user_id:
        from services.order_service import get_recent_purchase_ids
        from services.product_service import get_product_by_id
        
        recent_ids = get_recent_purchase_ids(user_id, db, days=14)
        
        # For pantry staples, check if user bought them recently
        for staple in pantry_staples:
            # Check if any recent purchase matches this staple
            found_recent = False
            for pid in recent_ids:
                product = get_product_by_id(pid)
                if product and staple in product["name"].lower():
                    found_recent = True
                    break
            
            if found_recent:
                skipped.append(staple)
            else:
                ingredients_to_find.append(staple)
    else:
        # No order history — include all ingredients
        ingredients_to_find = all_ingredients
    
    # Step 3: Find matching products for each ingredient
    filters = {}
    if user_profile:
        filters = {
            "is_vegetarian": user_profile.get("is_vegetarian"),
            "is_vegan": user_profile.get("is_vegan"),
            "is_high_protein": user_profile.get("is_high_protein"),
        }
    
    matched_products = []
    seen_ids = set()
    unmatched = []
    
    for ingredient in ingredients_to_find:
        # Search for each ingredient in the catalog
        results = query_relevant_products(
            query=ingredient,
            limit=3,
            filters=filters,
        )
        
        # Pick the best match
        found = False
        for p in results:
            if p["id"] not in seen_ids and p.get("in_stock", True):
                # Check if the product is actually related to the ingredient
                name_lower = p["name"].lower()
                desc_lower = p.get("description", "").lower()
                tags_lower = [t.lower() for t in p.get("tags", [])]
                
                if (ingredient in name_lower or
                    ingredient in desc_lower or
                    ingredient in " ".join(tags_lower) or
                    any(word in name_lower for word in ingredient.split())):
                    seen_ids.add(p["id"])
                    p_copy = dict(p)
                    p_copy["reason"] = f"Ingredient: {ingredient}"
                    matched_products.append(p_copy)
                    found = True
                    break
        
        if not found:
            unmatched.append(ingredient)
    
    total = sum(p.get("price", 0) for p in matched_products)
    
    # Build a friendly response
    skipped_msg = ""
    if skipped:
        skipped_msg = f" I've skipped {', '.join(skipped)} since you bought them recently."
    
    unmatched_msg = ""
    if unmatched:
        unmatched_msg = f" Note: I couldn't find {', '.join(unmatched)} in our store."
    
    message = (
        f"🍳 Here's your recipe bundle for **{recipe_name}** (serves {servings})! "
        f"Found {len(matched_products)} ingredients.{skipped_msg}{unmatched_msg}"
    )
    
    return {
        "message": message,
        "recommendations": matched_products,
        "total": total,
        "reasoning": f"Recipe-to-Cart: Parsed '{recipe_name}' into {len(all_ingredients)} ingredients, "
                     f"matched {len(matched_products)} from catalog, skipped {len(skipped)} recent purchases.",
        "recipe_mode": True,
        "skipped_ingredients": skipped,
    }
