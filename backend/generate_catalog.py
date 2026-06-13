"""
Generate a rich, Amazon-like product catalog from the free DummyJSON API.

DummyJSON (https://dummyjson.com) is a free, no-auth API with ~194 products
across 24 categories (smartphones, laptops, fragrances, furniture, watches,
sunglasses, groceries, etc.) WITH real product images hosted on their CDN.

This script fetches all products and writes them into backend/data/products.json
in the schema this app expects, so cart / chat / RAG keep working unchanged.
"""
import json
import os
import urllib.request

OUT_PATH = os.path.join(os.path.dirname(__file__), "data", "products.json")
API_URL = "https://dummyjson.com/products?limit=0"

# DummyJSON prices are in USD. Convert to realistic INR so the store reflects
# real-world Indian pricing.
USD_TO_INR = 83

# Categories to exclude (vehicles are too niche/expensive for a general store)
EXCLUDE_CATEGORIES = {"vehicle", "motorcycle"}

# Categories that are food/grocery -> mark as vegetarian-friendly so dietary
# filters in the chat don't hide the whole catalog.
FOOD_CATEGORIES = {"groceries"}


# Home appliances to add (DummyJSON doesn't have these essential categories).
# Prices are in INR, realistic for the Indian market.
HOME_APPLIANCES = [
    {
        "id": "h001", "name": "Samsung 55\" 4K UHD Smart LED TV", "category": "home-appliances",
        "subcategory": "televisions", "price": 54999, "mrp": 64999, "brand": "Samsung",
        "stock": 25, "tags": ["tv", "smart tv", "4k", "samsung", "led"],
        "rating": 4.5, "desc": "55-inch 4K Ultra HD Smart LED TV with HDR and built-in Alexa"
    },
    {
        "id": "h002", "name": "LG 43\" Full HD Smart LED TV", "category": "home-appliances",
        "subcategory": "televisions", "price": 32999, "mrp": 39999, "brand": "LG",
        "stock": 30, "tags": ["tv", "smart tv", "full hd", "lg"],
        "rating": 4.3, "desc": "43-inch Full HD Smart LED TV with webOS and ThinQ AI"
    },
    {
        "id": "h003", "name": "Samsung 253L Frost Free Refrigerator", "category": "home-appliances",
        "subcategory": "refrigerators", "price": 24990, "mrp": 29990, "brand": "Samsung",
        "stock": 18, "tags": ["fridge", "refrigerator", "frost free", "samsung"],
        "rating": 4.4, "desc": "253L 2-door frost-free double door refrigerator with stabilizer-free operation"
    },
    {
        "id": "h004", "name": "LG 190L Single Door Refrigerator", "category": "home-appliances",
        "subcategory": "refrigerators", "price": 14990, "mrp": 17990, "brand": "LG",
        "stock": 22, "tags": ["fridge", "refrigerator", "single door", "lg"],
        "rating": 4.2, "desc": "190L single door refrigerator with smart inverter compressor"
    },
    {
        "id": "h005", "name": "Whirlpool 7.5kg Fully Automatic Washing Machine", "category": "home-appliances",
        "subcategory": "washing-machines", "price": 18999, "mrp": 23999, "brand": "Whirlpool",
        "stock": 20, "tags": ["washing machine", "fully automatic", "whirlpool"],
        "rating": 4.3, "desc": "7.5kg fully-automatic top load washing machine with in-built heater"
    },
    {
        "id": "h006", "name": "IFB 6kg Front Load Washing Machine", "category": "home-appliances",
        "subcategory": "washing-machines", "price": 26990, "mrp": 32990, "brand": "IFB",
        "stock": 15, "tags": ["washing machine", "front load", "ifb"],
        "rating": 4.5, "desc": "6kg front load washing machine with Aqua Energie water softener"
    },
    {
        "id": "h007", "name": "Daikin 1.5 Ton 3 Star Split AC", "category": "home-appliances",
        "subcategory": "air-conditioners", "price": 35990, "mrp": 42990, "brand": "Daikin",
        "stock": 12, "tags": ["ac", "air conditioner", "split ac", "daikin"],
        "rating": 4.6, "desc": "1.5 ton 3-star inverter split AC with PM 2.5 filter"
    },
    {
        "id": "h008", "name": "Voltas 1 Ton 2 Star Split AC", "category": "home-appliances",
        "subcategory": "air-conditioners", "price": 28990, "mrp": 34990, "brand": "Voltas",
        "stock": 16, "tags": ["ac", "air conditioner", "split ac", "voltas"],
        "rating": 4.2, "desc": "1 ton 2-star split AC with copper condenser"
    },
    {
        "id": "h009", "name": "Samsung 28L Convection Microwave Oven", "category": "home-appliances",
        "subcategory": "microwaves", "price": 12990, "mrp": 15990, "brand": "Samsung",
        "stock": 28, "tags": ["microwave", "convection", "oven", "samsung"],
        "rating": 4.4, "desc": "28L convection microwave with ceramic enamel cavity"
    },
    {
        "id": "h010", "name": "LG 20L Solo Microwave Oven", "category": "home-appliances",
        "subcategory": "microwaves", "price": 6490, "mrp": 7990, "brand": "LG",
        "stock": 35, "tags": ["microwave", "solo", "oven", "lg"],
        "rating": 4.1, "desc": "20L solo microwave oven with I-wave technology"
    },
    {
        "id": "h011", "name": "Bajaj Majesty 2000W Induction Cooktop", "category": "home-appliances",
        "subcategory": "cooktops", "price": 2499, "mrp": 3499, "brand": "Bajaj",
        "stock": 40, "tags": ["induction", "cooktop", "bajaj"],
        "rating": 4.0, "desc": "2000W induction cooktop with automatic voltage regulator"
    },
    {
        "id": "h012", "name": "Prestige Iris 750W Mixer Grinder", "category": "home-appliances",
        "subcategory": "mixer-grinders", "price": 3599, "mrp": 4999, "brand": "Prestige",
        "stock": 45, "tags": ["mixer", "grinder", "prestige"],
        "rating": 4.3, "desc": "750W mixer grinder with 3 stainless steel jars"
    },
    {
        "id": "h013", "name": "Philips Daily Collection HD9218 Air Fryer", "category": "home-appliances",
        "subcategory": "air-fryers", "price": 8999, "mrp": 12995, "brand": "Philips",
        "stock": 22, "tags": ["air fryer", "philips", "healthy cooking"],
        "rating": 4.5, "desc": "4.1L air fryer with rapid air technology"
    },
    {
        "id": "h014", "name": "Kent Grand Plus RO Water Purifier", "category": "home-appliances",
        "subcategory": "water-purifiers", "price": 16999, "mrp": 22000, "brand": "Kent",
        "stock": 18, "tags": ["water purifier", "ro", "kent"],
        "rating": 4.4, "desc": "8L RO+UV+UF water purifier with TDS controller"
    },
    {
        "id": "h015", "name": "Dyson V8 Cordless Vacuum Cleaner", "category": "home-appliances",
        "subcategory": "vacuum-cleaners", "price": 35900, "mrp": 42900, "brand": "Dyson",
        "stock": 10, "tags": ["vacuum cleaner", "cordless", "dyson"],
        "rating": 4.7, "desc": "Cordless stick vacuum with up to 40 minutes runtime"
    },
]


def fetch_products():
    print(f"Fetching products from {API_URL} ...")
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("products", [])


def transform(p):
    price = round(float(p.get("price", 0)) * USD_TO_INR)
    discount = float(p.get("discountPercentage", 0) or 0)
    # Derive an MRP from the discount so the UI can show a strike-through price.
    mrp = round(price / (1 - discount / 100)) if discount > 0 else price
    category = p.get("category", "misc")
    stock = int(p.get("stock", 0) or 0)
    is_food = category in FOOD_CATEGORIES

    return {
        "id": f"p{p['id']}",
        "name": p.get("title", "Unknown"),
        "category": category,
        "subcategory": category,
        "price": price,
        "mrp": mrp,
        "unit": "1 pc",
        "brand": p.get("brand") or "Generic",
        "in_stock": stock > 0,
        "stock_quantity": stock,
        "image_url": p.get("thumbnail") or (p.get("images") or [""])[0],
        "tags": p.get("tags", []) or [category],
        "rating": round(float(p.get("rating", 4.0) or 4.0), 1),
        "description": p.get("description", ""),
        "is_vegetarian": True if is_food else True,
        "is_vegan": True if is_food else False,
        "is_high_protein": False,
    }


def main():
    raw = fetch_products()
    products = [transform(p) for p in raw]
    out = {"products": products}
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    cats = sorted(set(p["category"] for p in products))
    print(f"Wrote {len(products)} products to {OUT_PATH}")
    print(f"Categories ({len(cats)}): {', '.join(cats)}")


if __name__ == "__main__":
    main()
