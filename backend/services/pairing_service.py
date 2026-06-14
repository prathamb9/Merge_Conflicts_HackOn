"""
Graph-Traversal "Perfect Pairing" Engine
=========================================
Models the product catalog as a directed weighted graph where edges represent
"frequently bought together / naturally complementary" relationships.

Graph structure:
  - Node  = product_id
  - Edge  = (source_id, target_id, weight)  where weight ∈ [0, 1]
             representing purchase-pair probability / recipe linkage strength.

Algorithm:
  - Adjacency list built once at import time and cached in memory.
  - When a product (or cart) triggers a query, we run a priority-queue BFS
    (best-first, not exhaustive) over the graph starting from all seed nodes,
    collecting the top-k highest-weight neighbours that:
      • are in stock
      • are NOT already in the seed set
      • pass any active dietary/preference filters

This outperforms standard vector similarity for complementary discovery because
two products can be semantically distant yet form a perfect pairing (e.g.
"Nachos" and "Salsa" have very different embeddings but a 0.95 edge weight).
"""
import heapq
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from services.product_service import load_products, get_product_by_id

# ---------------------------------------------------------------------------
# Edge definitions  —  (source_tag_or_id, target_tag_or_id, weight)
# Tags are more maintainable than raw IDs; we expand them at build time.
# ---------------------------------------------------------------------------
TAG_EDGE_TEMPLATES: List[Tuple[str, str, float]] = [
    # ── Snacks / beverages ────────────────────────────────────────────────
    ("snacks",      "beverages",    0.92),
    ("nachos",      "condiments",   0.95),
    ("chips",       "beverages",    0.90),
    ("popcorn",     "beverages",    0.88),
    ("snacks",      "desserts",     0.75),

    # ── Breakfast cluster ─────────────────────────────────────────────────
    ("dairy",       "grains",       0.88),
    ("dairy",       "fruits",       0.80),
    ("coffee",      "dairy",        0.93),
    ("grains",      "condiments",   0.70),

    # ── Cooking cluster ───────────────────────────────────────────────────
    ("vegetables",  "cooking essentials", 0.87),
    ("meat",        "vegetables",   0.85),
    ("seafood",     "vegetables",   0.83),
    ("condiments",  "grains",       0.72),

    # ── Electronics ecosystem ─────────────────────────────────────────────
    ("smartphones", "mobile-accessories", 0.95),
    ("laptops",     "mobile-accessories", 0.88),
    ("tablets",     "mobile-accessories", 0.87),

    # ── Fashion bundles ───────────────────────────────────────────────────
    ("men's shirts","men's shoes",   0.80),
    ("men's t-shirts","men's shoes", 0.78),
    ("clothing",    "footwear",      0.75),
    ("women's dresses", "heels",     0.85),
    ("women's dresses", "handbag",   0.82),
    ("handbags",    "jewellery",     0.78),
    ("earrings",    "necklace",      0.90),

    # ── Beauty / skincare routine ─────────────────────────────────────────
    ("mascara",     "eyeliner",      0.90),
    ("foundation",  "face powder",   0.88),
    ("lipstick",    "lip gloss",     0.82),
    ("face wash",   "toner",         0.88),
    ("serum",       "cream",         0.85),
    ("sunscreen",   "serum",         0.80),

    # ── Kitchen workflow ──────────────────────────────────────────────────
    ("kitchen tools", "cookware",   0.83),
    ("blenders",    "kitchen appliances", 0.78),
    ("kitchen appliances", "cookware", 0.80),

    # ── Sports / fitness bundle ───────────────────────────────────────────
    ("yoga",        "gym",           0.88),
    ("fitness",     "sports equipment", 0.85),
    ("gym",         "health supplements", 0.90),
    ("health supplements", "dairy", 0.72),

    # ── Decor clusters ────────────────────────────────────────────────────
    ("candles",     "home decor",   0.82),
    ("lighting",    "home decor",   0.78),

    # ── Watch / jewellery ─────────────────────────────────────────────────
    ("watches",     "jewellery",    0.75),
    ("luxury watches", "fragrances", 0.70),
]

# ---------------------------------------------------------------------------
# Build the adjacency graph at module load time
# ---------------------------------------------------------------------------
_graph: Dict[str, List[Tuple[float, str]]] = defaultdict(list)  # pid -> [(weight, pid)]
_built = False


def _build_graph() -> None:
    global _built
    products = load_products()

    # Map tag -> list of product_ids
    tag_to_pids: Dict[str, List[str]] = defaultdict(list)
    for p in products:
        for t in p.get("tags", []):
            tag_to_pids[t.lower()].append(p["id"])
        # also index by category for broad matches
        tag_to_pids[p["category"].lower()].append(p["id"])

    def resolve(key: str) -> List[str]:
        k = key.lower()
        return list(set(tag_to_pids.get(k, [])))

    for src_key, tgt_key, weight in TAG_EDGE_TEMPLATES:
        src_pids = resolve(src_key)
        tgt_pids = resolve(tgt_key)
        for src in src_pids:
            for tgt in tgt_pids:
                if src != tgt:
                    _graph[src].append((weight, tgt))

    # Deduplicate and keep only the max-weight edge for each (src, tgt) pair
    for pid in list(_graph.keys()):
        seen: Dict[str, float] = {}
        for w, tgt in _graph[pid]:
            if tgt not in seen or w > seen[tgt]:
                seen[tgt] = w
        _graph[pid] = [(w, tgt) for tgt, w in seen.items()]

    _built = True


def get_graph():
    if not _built:
        _build_graph()
    return _graph


# ---------------------------------------------------------------------------
# BFS traversal
# ---------------------------------------------------------------------------

def find_pairings(
    seed_ids: List[str],
    k: int = 6,
    filters: Optional[Dict] = None,
) -> List[Dict]:
    """
    Run a best-first BFS from `seed_ids` through the product graph.
    Returns up to `k` recommended companion products, sorted by relevance score.

    The score combines graph edge weight + product rating (as a tie-breaker).
    """
    graph = get_graph()
    seed_set: Set[str] = set(seed_ids)
    visited: Set[str] = set(seed_ids)

    # Max-heap (negate weight for min-heap in Python)
    # Heap items: (-score, product_id, hop_depth)
    heap: List[Tuple[float, str, int]] = []
    for sid in seed_ids:
        for weight, neighbour in graph.get(sid, []):
            if neighbour not in visited:
                heapq.heappush(heap, (-weight, neighbour, 1))

    results: List[Dict] = []
    seen_pushed: Set[str] = set()

    while heap and len(results) < k:
        neg_score, pid, depth = heapq.heappop(heap)
        if pid in visited:
            continue
        visited.add(pid)

        product = get_product_by_id(pid)
        if not product or not product.get("in_stock", True):
            continue

        # Dietary / preference filters
        if filters:
            if filters.get("is_vegetarian") and not product.get("is_vegetarian"):
                continue
            if filters.get("is_vegan") and not product.get("is_vegan"):
                continue

        # Boost score with rating (0..5 → 0..0.05 normalised addition)
        score = (-neg_score) + product.get("rating", 3.0) * 0.01

        results.append({
            **product,
            "pairing_score": round(score, 3),
            "pairing_reason": _explain(seed_ids, pid),
        })

        # Continue BFS up to depth 2
        if depth < 2:
            for weight, neighbour in graph.get(pid, []):
                if neighbour not in visited and neighbour not in seen_pushed:
                    hop_score = score * weight * 0.7  # decay across hops
                    heapq.heappush(heap, (-hop_score, neighbour, depth + 1))
                    seen_pushed.add(neighbour)

    results.sort(key=lambda x: -x["pairing_score"])
    return results[:k]


def _explain(seed_ids: List[str], target_id: str) -> str:
    """Generate a human-readable pairing reason."""
    target = get_product_by_id(target_id)
    if not target:
        return "Frequently bought together"
    seeds = [get_product_by_id(s) for s in seed_ids if get_product_by_id(s)]
    if not seeds:
        return f"Pairs great with your selection"
    seed_names = ", ".join(s["name"] for s in seeds[:2])
    return f"Often bought with {seed_names}"


# ---------------------------------------------------------------------------
# Cluster builder: groups pairings by category into visual "clusters"
# ---------------------------------------------------------------------------

def build_pairing_cluster(seed_ids: List[str], filters: Optional[Dict] = None) -> Dict:
    """
    Returns a structured 'pairing cluster' ready for the frontend:
    {
      "seed_products": [...],
      "cluster_label": "Party Night Bundle 🎉",
      "categories": [
        { "name": "Beverages", "products": [...] },
        ...
      ],
      "total_add_on_price": 450
    }
    """
    pairings = find_pairings(seed_ids, k=8, filters=filters)
    seeds    = [p for pid in seed_ids if (p := get_product_by_id(pid))]

    by_cat: Dict[str, List[Dict]] = defaultdict(list)
    for p in pairings:
        by_cat[p["category"]].append(p)

    from services.taxonomy_service import CATEGORY_DISPLAY_NAMES
    categories = []
    for cat, prods in by_cat.items():
        categories.append({
            "name": CATEGORY_DISPLAY_NAMES.get(cat, cat.replace("-", " ").title()),
            "products": prods,
        })

    total_add = sum(p["price"] for p in pairings)
    label = _cluster_label(seeds, pairings)

    return {
        "seed_products": seeds,
        "cluster_label": label,
        "categories": categories,
        "total_add_on_price": round(total_add, 0),
        "products": pairings,  # flat list for easy rendering
    }


def _cluster_label(seeds: List[Dict], pairings: List[Dict]) -> str:
    """Heuristic label based on seed categories."""
    if not seeds:
        return "Perfect Pairings ✨"
    cats = set(s.get("category", "") for s in seeds)
    if cats & {"groceries"}:
        tags = set(t for s in seeds for t in s.get("tags", []))
        if "snacks" in tags:
            return "Snack Party Bundle 🍿"
        if "meat" in tags or "seafood" in tags:
            return "Complete Meal Bundle 🍽️"
        if "fruits" in tags:
            return "Fresh & Healthy Combo 🥗"
        return "Grocery Bundle 🛒"
    if cats & {"smartphones", "laptops", "tablets"}:
        return "Tech Ecosystem Bundle 📱"
    if cats & {"beauty", "skin-care", "fragrances"}:
        return "Beauty Routine Bundle 💄"
    if cats & {"womens-dresses", "tops", "womens-bags"}:
        return "Complete Outfit Bundle 👗"
    if cats & {"sports-accessories"}:
        return "Fitness Starter Pack 💪"
    return "Perfect Pairings ✨"
