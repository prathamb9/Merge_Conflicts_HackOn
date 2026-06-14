from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    payment_methods = relationship("PaymentMethod", back_populates="user", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="cart_items")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    is_vegetarian = Column(Boolean, default=False)
    is_vegan = Column(Boolean, default=False)
    is_high_protein = Column(Boolean, default=False)
    weight_loss_mode = Column(Boolean, default=False)
    budget_preference = Column(Integer, default=500)
    favorite_categories = Column(Text, default="[]")

    user = relationship("User", back_populates="profile")


class Order(Base):
    """Stores completed orders for order history and frequency analysis"""
    __tablename__ = "orders"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    delivery_charge = Column(Float, default=0.0)
    status = Column(String, default="completed")  # completed, cancelled, pending
    # Checkout / fulfilment details
    delivery_address = Column(Text, default="")        # snapshot of address used
    payment_method = Column(String, default="")        # snapshot of payment label used
    payment_status = Column(String, default="unpaid")  # unpaid | paid
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Individual items within an order"""
    __tablename__ = "order_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    product_id = Column(String, nullable=False)
    product_name = Column(String, nullable=False)  # Store name for history
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)  # Lock price at time of order
    
    order = relationship("Order", back_populates="items")


class Address(Base):
    """Saved delivery addresses for a user."""
    __tablename__ = "addresses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    full_name = Column(String, default="")
    phone = Column(String, default="")
    line1 = Column(String, nullable=False)          # house / street
    line2 = Column(String, default="")              # area / landmark
    city = Column(String, default="")
    state = Column(String, default="")
    pincode = Column(String, default="")
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="addresses")

    def one_line(self) -> str:
        parts = [self.line1, self.line2, self.city, self.state, self.pincode]
        return ", ".join(p for p in parts if p)


class PaymentMethod(Base):
    """Saved payment methods for a user (demo / mock — no real card data)."""
    __tablename__ = "payment_methods"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)           # card | upi | cod | netbanking | wallet
    label = Column(String, default="")              # e.g. "Visa •••• 4242", "user@upi", "Cash on Delivery"
    details = Column(String, default="")            # masked / non-sensitive detail
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="payment_methods")


# ── Group / Shared Cart (real-time consensus shopping) ────────────────────────

class GroupSession(Base):
    """A shared shopping session multiple people can join via a short code."""
    __tablename__ = "group_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, index=True, nullable=False)   # short share code
    name = Column(String, default="Group Cart")
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    members = relationship("GroupMember", back_populates="session", cascade="all, delete-orphan")
    items = relationship("GroupItem", back_populates="session", cascade="all, delete-orphan")


class GroupMember(Base):
    """A participant in a group session (their dietary prefs feed consensus)."""
    __tablename__ = "group_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("group_sessions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    display_name = Column(String, default="Guest")
    is_vegetarian = Column(Boolean, default=False)
    is_vegan = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("GroupSession", back_populates="members")


class GroupItem(Base):
    """A product proposed in a group session, with vote tracking."""
    __tablename__ = "group_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("group_sessions.id"), nullable=False)
    product_id = Column(String, nullable=False)
    product_name = Column(String, default="")
    added_by = Column(String, default="")              # member display name
    votes = Column(Text, default="[]")                 # JSON list of member ids who upvoted
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("GroupSession", back_populates="items")
