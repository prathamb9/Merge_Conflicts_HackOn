from pydantic import BaseModel
from typing import List, Optional


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# ── Products ──────────────────────────────────────────────────────────────────

class ProductResponse(BaseModel):
    id: str
    name: str
    category: str
    subcategory: str
    price: float
    mrp: float
    unit: str
    brand: str
    in_stock: bool
    stock_quantity: int
    image_url: str
    tags: List[str]
    rating: float
    description: str
    is_vegetarian: bool
    is_vegan: bool
    is_high_protein: bool


class ProductsResponse(BaseModel):
    products: List[ProductResponse]
    total: int


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


class RecommendedProduct(BaseModel):
    id: str
    name: str
    price: float
    mrp: float = 0
    category: str
    subcategory: str = ""
    brand: str
    unit: str
    image_url: str
    in_stock: bool = True
    rating: float = 4.0
    reason: str = ""


class ChatResponse(BaseModel):
    message: str
    recommendations: List[RecommendedProduct]
    total: float
    reasoning: str


# ── Cart ──────────────────────────────────────────────────────────────────────

class CartItemAdd(BaseModel):
    product_id: str
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    product_id: str
    quantity: int
    product: Optional[ProductResponse] = None
    subtotal: float


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total: float


# ── Profile ───────────────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    is_vegetarian: bool = False
    is_vegan: bool = False
    is_high_protein: bool = False
    budget_preference: int = 500
    favorite_categories: List[str] = []


class ProfileResponse(BaseModel):
    is_vegetarian: bool
    is_vegan: bool
    is_high_protein: bool
    budget_preference: int
    favorite_categories: List[str]
