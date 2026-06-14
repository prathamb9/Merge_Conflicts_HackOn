import os
import json
import re
from typing import List, Dict, Any, Optional

# Lazy load products to avoid circular dependency
def get_products_data() -> List[Dict]:
    from .product_service import load_products
    return load_products()

# Check if chromadb is available, otherwise use fallback search
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

_client: Optional[Any] = None
_collection: Optional[Any] = None

def get_rag_collection() -> Any:
    global _client, _collection
    if not CHROMA_AVAILABLE:
        return None
        
    if _collection is None:
        try:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chroma_db")
            _client = chromadb.PersistentClient(path=db_path)
            
            emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            
            _collection = _client.get_or_create_collection(
                name="quickcommerce_products",
                embedding_function=emb_fn
            )
            
            if _collection.count() == 0:
                seed_collection(_collection)
        except Exception as e:
            print(f"Failed to initialize ChromaDB, falling back to Python search: {str(e)}")
            return None
            
    return _collection

def seed_collection(col: Any):
    print("Seeding ChromaDB product embeddings...")
    products = get_products_data()
    
    ids = []
    documents = []
    metadatas = []
    
    for p in products:
        ids.append(p["id"])
        
        veg_str = "vegetarian veg" if p.get("is_vegetarian") else "non-vegetarian"
        vegan_str = "vegan" if p.get("is_vegan") else ""
        protein_str = "high protein gym fitness" if p.get("is_high_protein") else ""
        tags_str = ", ".join(p.get("tags", []))
        
        doc = (
            f"Product Name: {p['name']}. "
            f"Brand: {p['brand']}. "
            f"Category: {p['category']}. "
            f"Subcategory: {p.get('subcategory', '')}. "
            f"Price: {p['price']} INR. "
            f"MRP: {p['mrp']} INR. "
            f"Unit: {p['unit']}. "
            f"Description: {p.get('description', '')}. "
            f"Tags: {tags_str}. "
            f"Diet: {veg_str} {vegan_str} {protein_str}."
        )
        
        documents.append(doc)
        metadatas.append({
            "id": p["id"],
            "category": p["category"],
            "price": float(p["price"]),
            "is_vegetarian": bool(p.get("is_vegetarian", False)),
            "is_vegan": bool(p.get("is_vegan", False)),
            "is_high_protein": bool(p.get("is_high_protein", False)),
            "in_stock": bool(p.get("in_stock", True))
        })
        
    col.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    print(f"ChromaDB seeded successfully with {len(products)} products!")


# Maps user-intent keywords to the categories and tags that actually exist in the
# Amazon-style catalog. When a query contains any of the trigger words on the left,
# products in the listed categories / with the listed tags get a strong relevance boost.
INTENT_MAP = [
    # (trigger words, target categories, target tags)
    (["breakfast", "morning", "cereal", "oats", "egg", "eggs", "milk", "coffee", "tea", "juice", "honey", "bread", "butter"],
     ["groceries"], ["dairy", "beverages", "fruits", "coffee", "condiments", "grains"]),
    (["snack", "snacks", "munch", "chips", "biscuit", "biscuits", "cookies", "namkeen"],
     ["groceries"], ["desserts", "beverages"]),
    (["drink", "drinks", "beverage", "beverages", "soda", "water", "thirsty", "cold drink", "cola", "pepsi", "coke"],
     ["groceries"], ["beverages"]),
    (["fruit", "fruits"], ["groceries"], ["fruits"]),
    (["vegetable", "vegetables", "veggie", "veggies", "veg", "sabzi"], ["groceries"], ["vegetables"]),
    (["meat", "chicken", "beef", "fish", "seafood", "protein", "non-veg", "nonveg"], ["groceries"], ["meat", "seafood", "health supplements"]),
    (["grocery", "groceries", "kitchen food", "cooking", "oil", "rice", "atta", "flour", "dal", "spice", "spices", "masala"],
     ["groceries"], ["cooking essentials", "grains"]),
    (["pet", "dog", "cat", "puppy", "kitten"], ["groceries"], ["pet supplies", "dog food", "cat food"]),
    (["dessert", "sweet", "sweets", "ice cream", "chocolate", "cake"], ["groceries"], ["desserts"]),
    (["healthy", "diet", "weight loss", "low calorie", "fitness", "salad"], ["groceries"], ["fruits", "vegetables", "health supplements"]),
    (["phone", "smartphone", "smartphones", "mobile", "iphone", "android", "cell"], ["smartphones", "mobile-accessories"], []),
    (["laptop", "laptops", "notebook", "computer", "macbook", "work setup", "workstation"], ["laptops"], []),
    (["tablet", "tablets", "ipad"], ["tablets"], []),
    (["charger", "cable", "case", "cover", "powerbank", "accessory", "accessories", "earphone", "headphone"], ["mobile-accessories"], []),
    (["watch", "watches", "smartwatch"], ["mens-watches", "womens-watches"], []),
    (["shoe", "shoes", "sneaker", "sneakers", "footwear"], ["mens-shoes", "womens-shoes"], []),
    (["shirt", "shirts", "tshirt", "t-shirt", "tee", "top", "tops", "clothing", "clothes", "apparel"], ["mens-shirts", "tops"], []),
    (["dress", "dresses", "gown", "frock"], ["womens-dresses"], []),
    (["bag", "bags", "handbag", "purse", "backpack"], ["womens-bags"], []),
    (["jewellery", "jewelry", "ring", "necklace", "earring", "earrings", "bracelet"], ["womens-jewellery"], []),
    (["perfume", "perfumes", "fragrance", "fragrances", "cologne", "scent"], ["fragrances"], []),
    (["makeup", "cosmetic", "cosmetics", "lipstick", "mascara", "beauty"], ["beauty"], []),
    (["skincare", "skin", "cream", "moisturizer", "serum", "lotion"], ["skin-care", "beauty"], []),
    (["sunglass", "sunglasses", "shades", "goggles"], ["sunglasses"], []),
    (["furniture", "sofa", "bed", "chair", "table", "desk"], ["furniture"], []),
    (["decor", "decoration", "home decor", "vase", "painting"], ["home-decoration"], []),
    (["kitchen", "utensil", "utensils", "cookware", "knife", "pan"], ["kitchen-accessories"], []),
    (["sport", "sports", "fitness", "gym", "workout", "exercise", "ball", "cricket", "football"], ["sports-accessories"], []),
    (["gift for her", "gift her", "her birthday", "girlfriend", "wife"], ["womens-jewellery", "womens-bags", "beauty", "fragrances", "womens-dresses"], []),
    (["gift for him", "gift him", "boyfriend", "husband"], ["mens-watches", "mens-shoes", "mens-shirts", "fragrances"], []),
    # Recipe / cooking intent → groceries
    (["cook", "recipe", "make", "prepare", "ingredient", "ingredients"], ["groceries"], ["cooking essentials", "vegetables", "dairy", "meat", "fruits", "condiments"]),
    # Party / match day intent
    (["party", "match", "ipl", "cricket", "game night", "movie night", "celebration"],
     ["groceries"], ["beverages", "desserts"]),
    # Chai / tea time
    (["chai", "tea time", "pakoda", "samosa", "evening snack"],
     ["groceries"], ["beverages", "desserts"]),
]

STOP_WORDS = {
    "need", "for", "a", "an", "under", "rupees", "rs", "inr", "in", "the", "and",
    "or", "of", "to", "i", "want", "me", "some", "get", "buy", "show", "give",
    "please", "with", "my", "is", "are", "looking", "find", "something", "budget",
    "rupee", "price", "good", "best", "nice", "rs.", "within",
    # Gender qualifiers are handled separately (see GENDER_WORDS) so they don't
    # get treated as strong product-name keywords (e.g. "perfume for men").
    "men", "women", "man", "woman", "male", "female", "ladies", "gents", "boy",
    "girl", "boys", "girls", "his", "her", "him",
}

# Gender intent -> the categories that match that gender. Used for a mild boost only.
GENDER_WORDS = {
    "men": "mens", "man": "mens", "male": "mens", "gents": "mens",
    "boy": "mens", "boys": "mens", "his": "mens", "him": "mens",
    "women": "womens", "woman": "womens", "female": "womens", "ladies": "womens",
    "girl": "womens", "girls": "womens", "her": "womens",
}


def python_fallback_search(
    query: str,
    limit: int = 15,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict]:
    """
    Pure Python relevance search over the catalog. No external DB / ML required.

    Relevance is driven by keyword matches and an intent->category map. Rating is used
    ONLY as a tie-breaker between already-relevant products, so unrelated high-rated
    items (e.g. shirts for a "breakfast" query) never surface.
    """
    products = get_products_data()
    q = query.lower()
    query_tokens = set(re.findall(r"\w+", q))
    keywords = query_tokens - STOP_WORDS
    if not keywords:
        keywords = query_tokens - GENDER_WORDS.keys()
        if not keywords:
            keywords = query_tokens

    # Resolve query intent -> boosted categories / tags
    boosted_categories: set = set()
    boosted_tags: set = set()
    for triggers, cats, tags in INTENT_MAP:
        if any(t in q for t in triggers):
            boosted_categories.update(cats)
            boosted_tags.update(tags)

    # Detect gender preference (e.g. "for men" -> prefer mens-* categories)
    gender_pref: Optional[str] = None
    for token in query_tokens:
        if token in GENDER_WORDS:
            gender_pref = GENDER_WORDS[token]
            break

    scored_products = []
    for p in products:
        if not p.get("in_stock", True):
            continue

        if filters:
            if filters.get("is_vegetarian") and not p.get("is_vegetarian", False):
                continue
            if filters.get("is_vegan") and not p.get("is_vegan", False):
                continue
            if filters.get("is_high_protein") and not p.get("is_high_protein", False):
                continue

        name = p["name"].lower()
        brand = p["brand"].lower()
        category = p["category"].lower()
        description = p.get("description", "").lower()
        tags = [t.lower() for t in p.get("tags", [])]

        # Relevance score (does NOT include rating).
        relevance = 0.0

        # 1. Direct keyword matches
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", name):
                relevance += 10.0
            elif kw in name:
                relevance += 5.0
            if kw in category:
                relevance += 6.0
            if kw in tags:
                relevance += 6.0
            if kw in brand:
                relevance += 4.0
            if kw in description:
                relevance += 1.5

        # 2. Intent-based category / tag boost (the strongest, most reliable signal)
        if category in boosted_categories:
            relevance += 20.0
        if any(t in boosted_tags for t in tags):
            relevance += 10.0

        # 3. Gender preference: boost the requested gender's categories and penalise
        #    the opposite gender, so "shoes for men" prefers mens-shoes over womens-shoes.
        if gender_pref and relevance > 0:
            opposite = "womens" if gender_pref == "mens" else "mens"
            if category.startswith(gender_pref):
                relevance += 10.0
            elif category.startswith(opposite):
                relevance -= 12.0

        # 4. Dietary intent boost
        if any(w in q for w in ("gym", "protein", "fitness", "workout")) and p.get("is_high_protein"):
            relevance += 8.0

        if relevance > 0:
            # Rating only breaks ties among relevant items.
            final_score = relevance + float(p.get("rating", 4.0)) * 0.1
            scored_products.append((p, final_score))

    scored_products.sort(key=lambda x: x[1], reverse=True)

    # If the query matched nothing at all (e.g. gibberish), fall back to top-rated
    # in-stock products so the assistant can still respond with something.
    if not scored_products:
        in_stock = [p for p in products if p.get("in_stock", True)]
        in_stock.sort(key=lambda p: float(p.get("rating", 0)), reverse=True)
        return in_stock[:limit]

    return [item[0] for item in scored_products[:limit]]


def query_relevant_products(
    query: str, 
    limit: int = 15,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict]:
    """
    Retrieve products using ChromaDB if available, otherwise fallback to Python search.
    """
    col = get_rag_collection()
    if col is not None:
        try:
            # Map filters to ChromaDB metadata
            where = {}
            if filters:
                if filters.get("is_vegetarian"):
                    where["is_vegetarian"] = True
                if filters.get("is_vegan"):
                    where["is_vegan"] = True
                if filters.get("is_high_protein"):
                    where["is_high_protein"] = True
                    
            results = col.query(
                query_texts=[query],
                n_results=limit,
                where=where if where else None
            )
            
            from .product_service import get_product_by_id
            matched_products = []
            if results and results["ids"] and len(results["ids"][0]) > 0:
                for p_id in results["ids"][0]:
                    p = get_product_by_id(p_id)
                    if p:
                        matched_products.append(p)
                return matched_products
        except Exception as e:
            print(f"ChromaDB query failed, falling back to Python search: {str(e)}")
            
    # Fallback to pure Python search
    return python_fallback_search(query, limit, filters)


def find_smart_substitute(
    out_of_stock_product: Dict,
    filters: Optional[Dict] = None,
    user_profile: Optional[Dict] = None,
) -> Optional[Dict]:
    """
    Find the best semantic substitute for an out-of-stock product.
    
    Uses ChromaDB vector similarity when available, with profile-aware
    filtering (e.g., weight_loss_mode shifts full-cream → toned milk).
    
    Falls back to category/tag/price matching if ChromaDB is unavailable.
    """
    original_name = out_of_stock_product.get("name", "")
    original_category = out_of_stock_product.get("category", "")
    original_price = out_of_stock_product.get("price", 0)
    original_tags = set(out_of_stock_product.get("tags", []))
    original_desc = out_of_stock_product.get("description", "")
    
    # Build a rich semantic query for ChromaDB
    weight_loss = user_profile.get("weight_loss_mode", False) if user_profile else False
    
    # Adjust search query based on user profile
    search_query = f"{original_name} {original_category} {' '.join(original_tags)}"
    substitution_reason = ""
    
    if weight_loss:
        # Shift preferences for weight-loss users
        WEIGHT_LOSS_SHIFTS = {
            "full cream": ("toned", "low fat", "skimmed"),
            "cream": ("light", "low fat"),
            "sugar": ("sugar free", "stevia", "zero sugar"),
            "fried": ("baked", "air fried", "grilled"),
            "regular": ("diet", "light", "zero"),
            "whole": ("multigrain", "oats"),
            "ice cream": ("frozen yogurt", "sorbet"),
        }
        name_lower = original_name.lower()
        desc_lower = original_desc.lower()
        
        for trigger, replacements in WEIGHT_LOSS_SHIFTS.items():
            if trigger in name_lower or trigger in desc_lower:
                search_query += " " + " ".join(replacements)
                substitution_reason = f"Healthier alternative for weight-loss preference (shifted from '{trigger}' to '{'/'.join(replacements)}')"
                break
        
        if not substitution_reason:
            search_query += " healthy low calorie diet light"
            substitution_reason = "Selected healthier option for weight-loss preference"
    
    # Try ChromaDB vector search first
    col = get_rag_collection()
    if col is not None:
        try:
            # Build ChromaDB filter: in_stock + dietary constraints
            where_conditions = [{"in_stock": True}]
            if filters:
                if filters.get("is_vegetarian"):
                    where_conditions.append({"is_vegetarian": True})
                if filters.get("is_vegan"):
                    where_conditions.append({"is_vegan": True})
            
            where = {"$and": where_conditions} if len(where_conditions) > 1 else where_conditions[0]
            
            results = col.query(
                query_texts=[search_query],
                n_results=10,
                where=where
            )
            
            if results and results["ids"] and len(results["ids"][0]) > 0:
                from .product_service import get_product_by_id
                
                for pid in results["ids"][0]:
                    if pid == out_of_stock_product["id"]:
                        continue
                    candidate = get_product_by_id(pid)
                    if candidate and candidate.get("in_stock", True):
                        # Apply dietary filters
                        if filters:
                            if filters.get("is_vegetarian") and not candidate.get("is_vegetarian"):
                                continue
                            if filters.get("is_vegan") and not candidate.get("is_vegan"):
                                continue
                        
                        candidate["is_substitute"] = True
                        candidate["original_product"] = original_name
                        candidate["substitution_reason"] = (
                            substitution_reason or
                            f"Best semantic match for '{original_name}' (out of stock)"
                        )
                        return candidate
        except Exception as e:
            print(f"ChromaDB substitute search failed: {e}")
    
    # Fallback: Python-based scoring
    products = get_products_data()
    candidates = []
    for p in products:
        if not p.get("in_stock", True):
            continue
        if p["id"] == out_of_stock_product["id"]:
            continue
        
        # Apply dietary filters
        if filters:
            if filters.get("is_vegetarian") and not p.get("is_vegetarian", False):
                continue
            if filters.get("is_vegan") and not p.get("is_vegan", False):
                continue
            if filters.get("is_high_protein") and not p.get("is_high_protein", False):
                continue
        
        score = 0.0
        
        # Same category = high priority
        if p["category"] == original_category:
            score += 20.0
        
        # Tag overlap
        product_tags = set(p.get("tags", []))
        common_tags = original_tags & product_tags
        score += len(common_tags) * 5.0
        
        # Price similarity (within ±30%)
        price_diff = abs(p["price"] - original_price) / (original_price or 1)
        if price_diff < 0.3:
            score += 10.0 * (1 - price_diff)
        
        # Name word overlap (semantic proxy)
        original_words = set(original_name.lower().split())
        candidate_words = set(p["name"].lower().split())
        name_overlap = len(original_words & candidate_words)
        score += name_overlap * 3.0
        
        # Weight-loss preference: boost lower-calorie/healthier alternatives
        if weight_loss:
            p_name_lower = p["name"].lower()
            for kw in ("toned", "skimmed", "low fat", "light", "diet", "zero", "sugar free", "oats", "multigrain"):
                if kw in p_name_lower:
                    score += 8.0
                    break
        
        if score > 0:
            candidates.append((p, score))
    
    if not candidates:
        return None
    
    candidates.sort(key=lambda x: x[1], reverse=True)
    best = dict(candidates[0][0])
    best["is_substitute"] = True
    best["original_product"] = original_name
    best["substitution_reason"] = (
        substitution_reason or
        f"Closest match for '{original_name}' (same category, similar price)"
    )
    return best


def query_relevant_products_with_substitution(
    query: str, 
    limit: int = 15,
    filters: Optional[Dict[str, Any]] = None,
    user_profile: Optional[Dict] = None,
) -> List[Dict]:
    """
    Enhanced version that automatically substitutes out-of-stock products
    with profile-aware semantic alternatives.
    """
    # Get initial results
    results = query_relevant_products(query, limit, filters)
    
    # Apply substitution logic
    final_results = []
    seen_ids = set()
    for p in results:
        if not p.get("in_stock", True):
            substitute = find_smart_substitute(p, filters, user_profile)
            if substitute and substitute["id"] not in seen_ids:
                seen_ids.add(substitute["id"])
                final_results.append(substitute)
        else:
            if p["id"] not in seen_ids:
                seen_ids.add(p["id"])
                final_results.append(p)
    
    return final_results
