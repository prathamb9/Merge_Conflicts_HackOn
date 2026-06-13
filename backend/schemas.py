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
    # Substitution fields
    is_substitute: bool = False
    original_product: str = ""
    substitution_reason: str = ""


class CartOptimization(BaseModel):
    """Proactive suggestions to cross delivery/coupon thresholds."""
    threshold_name: str = ""       # e.g. "Free Delivery" or "₹75 Off Coupon"
    threshold_amount: float = 0
    current_total: float = 0
    gap: float = 0
    suggested_products: List[RecommendedProduct] = []
    savings: float = 0


# ── Amazon Department Taxonomy ────────────────────────────────────────────────

class DepartmentItem(BaseModel):
    """A single product inside a department sub-category."""
    id: str
    formatted_name: str
    price: float
    reason: str = ""
    image_url: str = ""
    brand: str = ""
    unit: str = ""
    rating: float = 4.0
    in_stock: bool = True
    mrp: float = 0
    is_substitute: bool = False
    original_product: str = ""


class DepartmentCategory(BaseModel):
    """A tier-2 sub-category within an Amazon department."""
    name: str
    items: List[DepartmentItem]


class AmazonDepartment(BaseModel):
    """A top-level Amazon-style browse tree department."""
    department: str
    categories: List[DepartmentCategory]


class ChatResponse(BaseModel):
    message: str
    recommendations: List[RecommendedProduct]
    total: float
    reasoning: str
    # Amazon department-grouped view
    amazon_departments: List[AmazonDepartment] = []
    # Existing feature fields
    recipe_mode: bool = False
    skipped_ingredients: List[str] = []
    cart_optimization: Optional[CartOptimization] = None


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
    weight_loss_mode: bool = False
    budget_preference: int = 500
    favorite_categories: List[str] = []


class ProfileResponse(BaseModel):
    is_vegetarian: bool
    is_vegan: bool
    is_high_protein: bool
    weight_loss_mode: bool
    budget_preference: int
    favorite_categories: List[str]


# ── Recipe ────────────────────────────────────────────────────────────────────

class RecipeRequest(BaseModel):
    recipe: str
    servings: int = 2


class RecipeResponse(BaseModel):
    recipe_name: str
    servings: int
    ingredients: List[str]
    skipped_ingredients: List[str]
    matched_products: List[RecommendedProduct]
    total: float
    message: str
