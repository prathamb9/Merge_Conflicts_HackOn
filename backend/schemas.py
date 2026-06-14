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


class CheckoutState(BaseModel):
    """Conversational checkout state echoed between client and server."""
    stage: str = ""                 # "" | await_address | await_payment | await_confirm
    selected_ids: List[str] = []    # product ids the user is buying


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    last_recommended_ids: List[str] = []   # ids from the most recent recommendation
    checkout: Optional[CheckoutState] = None


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
    # Checkout state management
    current_state: str = "BROWSING"          # BROWSING | COLLECTING_INFO | CHECKOUT_READY
    missing_details: List[str] = []          # e.g. ["delivery_address", "payment_method"]
    action: str = "NONE"                     # NONE | ASK_FOR_INFO | REDIRECT_TO_PAYMENT
    checkout_items: List[str] = []           # Product IDs user wants to buy
    # Agent / voice checkout flow
    checkout: Optional["CheckoutState"] = None   # updated checkout state for the client to echo back
    order_id: str = ""                       # set when an order is created (redirect target)
    quick_replies: List[str] = []            # suggested tappable/spoken replies
    speak: bool = True                       # whether the client should speak this message
    kit_title: str = ""                      # emotional/situational Care Kit title
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


# ── Addresses ─────────────────────────────────────────────────────────────────

class AddressCreate(BaseModel):
    full_name: str = ""
    phone: str = ""
    line1: str
    line2: str = ""
    city: str = ""
    state: str = ""
    pincode: str = ""
    is_default: bool = True


class AddressResponse(BaseModel):
    id: str
    full_name: str
    phone: str
    line1: str
    line2: str
    city: str
    state: str
    pincode: str
    is_default: bool
    one_line: str
    model_config = {"from_attributes": True}


# ── Payment Methods ───────────────────────────────────────────────────────────

class PaymentMethodCreate(BaseModel):
    type: str                 # card | upi | cod | netbanking | wallet
    label: str = ""
    details: str = ""
    is_default: bool = True


class PaymentMethodResponse(BaseModel):
    id: str
    type: str
    label: str
    details: str
    is_default: bool
    model_config = {"from_attributes": True}


# ── Orders ────────────────────────────────────────────────────────────────────

class OrderItemResponse(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price_at_purchase: float
    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: str
    total_amount: float
    delivery_charge: float
    status: str
    delivery_address: str = ""
    payment_method: str = ""
    payment_status: str = "unpaid"
    items: List[OrderItemResponse] = []
    model_config = {"from_attributes": True}


class CreateOrderRequest(BaseModel):
    """Create an order from explicit product ids (used by the agent checkout)."""
    product_ids: List[str] = []
    address_id: str = ""        # optional; defaults to user's default address
    payment_method_id: str = "" # optional; defaults to user's default payment method


class PayOrderRequest(BaseModel):
    payment_method_id: str = ""
