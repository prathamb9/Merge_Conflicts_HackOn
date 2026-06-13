from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from schemas import ProductsResponse, ProductResponse
from services.product_service import (
    get_all_products,
    get_product_by_id,
    get_categories,
)

router = APIRouter(prefix="/api/products", tags=["products"])


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
