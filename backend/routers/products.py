from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from schemas import ProductsResponse, ProductResponse
from services.product_service import (
    get_all_products,
    get_product_by_id,
    get_categories,
)
from services.taxonomy_service import (
    CATEGORY_TO_DEPARTMENT,
    CATEGORY_DISPLAY_NAMES,
    DEPARTMENT_ORDER,
)

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/departments")
def list_departments():
    """Return all categories grouped under Amazon department headers."""
    categories = get_categories()
    
    dept_map = {}
    for cat in categories:
        dept = CATEGORY_TO_DEPARTMENT.get(cat, "📦 Other")
        display = CATEGORY_DISPLAY_NAMES.get(cat, cat.replace("-", " ").title())
        if dept not in dept_map:
            dept_map[dept] = []
        dept_map[dept].append({"slug": cat, "label": display})
    
    # Return in canonical order
    result = []
    for dept_name in DEPARTMENT_ORDER:
        if dept_name in dept_map:
            result.append({
                "department": dept_name,
                "categories": dept_map[dept_name],
            })
    
    return {"departments": result}


@router.get("/categories")
def list_categories():
    return {"categories": get_categories()}


@router.get("", response_model=ProductsResponse)
def list_products(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    result = get_all_products(category=category, search=search, page=page, limit=limit)
    return ProductsResponse(**result)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str):
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
