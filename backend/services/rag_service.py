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
    (["snack", "snacks", "munch", "chips"], ["groceries"], ["desserts", "beverages"]),
    (["drink", "drinks", "beverage", "beverages", "soda", "water", "thirsty"], ["groceries"], ["beverages"]),
    (["fruit", "fruits"], ["groceries"], ["fruits"]),
    (["vegetable", "vegetables", "veggie", "veggies", "veg"], ["groceries"], ["vegetables"]),
    (["meat", "chicken", "beef", "fish", "seafood", "protein", "non-veg", "nonveg"], ["groceries"], ["meat", "seafood", "health supplements"]),
    (["grocery", "groceries", "kitchen food", "cooking", "oil", "rice"], ["groceries"], ["cooking essentials", "grains"]),
    (["pet", "dog", "cat", "puppy", "kitten"], ["groceries"], ["pet supplies", "dog food", "cat food"]),
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
    (["bike", "motorcycle", "motorbike"], ["motorcycle"], []),
    (["car", "vehicle", "automobile"], ["vehicle"], []),
    (["gift for her", "gift her", "her birthday", "girlfriend", "wife"], ["womens-jewellery", "womens-bags", "beauty", "fragrances", "womens-dresses"], []),
    (["gift for him", "gift him", "boyfriend", "husband"], ["mens-watches", "mens-shoes", "mens-shirts", "fragrances"], []),
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


def find_substitute(out_of_stock_product: Dict, filters: Optional[Dict] = None) -> Optional[Dict]:
    """
    Find the best semantic substitute for an out-of-stock product.
    
    Matches by:
    1. Same category
    2. Similar tags
    3. Similar price range (±30%)
    4. Respects dietary filters
    """
    products = get_products_data()
    original_price = out_of_stock_product.get("price", 0)
    original_category = out_of_stock_product.get("category", "")
    original_tags = set(out_of_stock_product.get("tags", []))
    
    candidates = []
    for p in products:
        # Must be in stock
        if not p.get("in_stock", True):
            continue
        
        # Must not be the same product
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
        
        # Score the similarity
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
        
        if score > 0:
            candidates.append((p, score))
    
    if not candidates:
        return None
    
    # Return the best match
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def query_relevant_products_with_substitution(
    query: str, 
    limit: int = 15,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict]:
    """
    Enhanced version that automatically substitutes out-of-stock products.
    """
    # Get initial results
    results = query_relevant_products(query, limit, filters)
    
    # Apply substitution logic
    final_results = []
    for p in results:
        if not p.get("in_stock", True):
            substitute = find_substitute(p, filters)
            if substitute:
                substitute["is_substitute"] = True
                substitute["original_product"] = p["name"]
                final_results.append(substitute)
        else:
            final_results.append(p)
    
    return final_results
