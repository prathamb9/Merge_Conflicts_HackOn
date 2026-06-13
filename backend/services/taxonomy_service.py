"""
Amazon India Browse Tree Taxonomy Service

Maps the 24 internal catalog categories to 8 Amazon-style top-level departments
with tier-2 sub-categories.  Provides grouping, budget-filtering, and
Amazon-standard product naming utilities.
"""
from typing import List, Dict, Any, Optional


# ── Category → Department Mapping ────────────────────────────────────────────

CATEGORY_TO_DEPARTMENT: Dict[str, str] = {
    # 📦 Grocery & Gourmet Foods
    "groceries": "📦 Grocery & Gourmet Foods",

    # 📦 Home & Kitchen
    "furniture": "📦 Home & Kitchen",
    "home-decoration": "📦 Home & Kitchen",
    "kitchen-accessories": "📦 Home & Kitchen",

    # 📦 Electronics & Accessories
    "smartphones": "📦 Electronics & Accessories",
    "laptops": "📦 Electronics & Accessories",
    "tablets": "📦 Electronics & Accessories",
    "mobile-accessories": "📦 Electronics & Accessories",

    # 📦 Clothing, Shoes & Jewelry
    "mens-shirts": "📦 Clothing, Shoes & Jewelry",
    "mens-shoes": "📦 Clothing, Shoes & Jewelry",
    "womens-dresses": "📦 Clothing, Shoes & Jewelry",
    "womens-bags": "📦 Clothing, Shoes & Jewelry",
    "womens-jewellery": "📦 Clothing, Shoes & Jewelry",
    "womens-shoes": "📦 Clothing, Shoes & Jewelry",
    "tops": "📦 Clothing, Shoes & Jewelry",
    "sunglasses": "📦 Clothing, Shoes & Jewelry",

    # 📦 Beauty & Personal Care
    "beauty": "📦 Beauty & Personal Care",
    "skin-care": "📦 Beauty & Personal Care",
    "fragrances": "📦 Beauty & Personal Care",

    # 📦 Sports, Fitness & Outdoors
    "sports-accessories": "📦 Sports, Fitness & Outdoors",

    # 📦 Automotive
    "motorcycle": "📦 Automotive",
    "vehicle": "📦 Automotive",

    # 📦 Watches & Accessories
    "mens-watches": "📦 Watches & Accessories",
    "womens-watches": "📦 Watches & Accessories",
}

# Human-readable sub-category labels for each internal category slug
CATEGORY_DISPLAY_NAMES: Dict[str, str] = {
    "groceries": "Grocery & Gourmet",
    "furniture": "Furniture",
    "home-decoration": "Home Décor",
    "kitchen-accessories": "Kitchen Tools & Accessories",
    "smartphones": "Smartphones",
    "laptops": "Laptops & Notebooks",
    "tablets": "Tablets",
    "mobile-accessories": "Mobile Accessories",
    "mens-shirts": "Men's Shirts",
    "mens-shoes": "Men's Shoes",
    "womens-dresses": "Women's Dresses",
    "womens-bags": "Women's Bags & Handbags",
    "womens-jewellery": "Women's Jewellery",
    "womens-shoes": "Women's Shoes",
    "tops": "Tops & T-Shirts",
    "sunglasses": "Sunglasses",
    "beauty": "Makeup & Beauty",
    "skin-care": "Skin Care",
    "fragrances": "Fragrances & Perfumes",
    "sports-accessories": "Sports & Fitness Accessories",
    "motorcycle": "Motorcycle Accessories",
    "vehicle": "Car & Vehicle Accessories",
    "mens-watches": "Men's Watches",
    "womens-watches": "Women's Watches",
}

# Canonical ordering of departments for consistent output
DEPARTMENT_ORDER = [
    "📦 Grocery & Gourmet Foods",
    "📦 Home & Kitchen",
    "📦 Electronics & Accessories",
    "📦 Clothing, Shoes & Jewelry",
    "📦 Beauty & Personal Care",
    "📦 Watches & Accessories",
    "📦 Sports, Fitness & Outdoors",
    "📦 Automotive",
    "📦 Other",
]


def get_department(category: str) -> str:
    """Return the Amazon department name for a catalog category."""
    return CATEGORY_TO_DEPARTMENT.get(category.lower(), "📦 Other")


def get_display_category(category: str) -> str:
    """Return a human-friendly sub-category label."""
    return CATEGORY_DISPLAY_NAMES.get(category.lower(), category.replace("-", " ").title())


def format_product_name(product: Dict) -> str:
    """
    Format a product using Amazon's clean syntax:
    [Brand] Product Title (Size/Variant)
    """
    brand = product.get("brand", "")
    name = product.get("name", "")
    unit = product.get("unit", "")

    # Avoid duplicating the brand if it already starts the name
    if name.lower().startswith(brand.lower()):
        formatted = name
    else:
        formatted = f"{brand} {name}" if brand else name

    if unit:
        formatted += f" ({unit})"

    return formatted


def group_by_departments(
    products: List[Dict],
    budget: Optional[float] = None,
) -> List[Dict]:
    """
    Group a flat product list into the Amazon department → sub-category hierarchy.

    Each department dict has:
      - department: str (emoji + name)
      - categories: list of {name: str, items: list of product dicts}

    If `budget` is provided, individual items exceeding it are stripped.
    Empty departments/categories are pruned automatically.
    """
    # Phase 1: bucket products into department → category → items
    dept_map: Dict[str, Dict[str, List[Dict]]] = {}

    for p in products:
        price = p.get("price", 0) or 0

        # Budget: strip individual items that exceed the ceiling
        if budget is not None and price > budget:
            continue

        category = p.get("category", "other")
        department = get_department(category)
        display_cat = get_display_category(category)

        if department not in dept_map:
            dept_map[department] = {}
        if display_cat not in dept_map[department]:
            dept_map[department][display_cat] = []

        dept_map[department][display_cat].append(p)

    # Phase 2: build ordered output, skipping empty departments
    result = []
    for dept_name in DEPARTMENT_ORDER:
        if dept_name not in dept_map:
            continue
        categories = []
        for cat_name, items in dept_map[dept_name].items():
            if items:
                categories.append({
                    "name": cat_name,
                    "items": items,
                })
        if categories:
            result.append({
                "department": dept_name,
                "categories": categories,
            })

    return result


def filter_empty_departments(
    departments: List[Dict],
    budget: float,
) -> List[Dict]:
    """
    Post-LLM safety net: strip any department/category where ALL items
    exceed the budget ceiling.  Returns a pruned copy.
    """
    pruned = []
    for dept in departments:
        kept_cats = []
        for cat in dept.get("categories", []):
            kept_items = [
                item for item in cat.get("items", [])
                if (item.get("price", 0) or 0) <= budget
            ]
            if kept_items:
                kept_cats.append({**cat, "items": kept_items})
        if kept_cats:
            pruned.append({**dept, "categories": kept_cats})
    return pruned
