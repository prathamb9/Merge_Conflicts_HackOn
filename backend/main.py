from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine
import models
from routers import auth, chat, products, cart, profile, recipe, addresses, payments, orders, bargain, pairing, meal_plan, group

# Create all DB tables on startup
models.Base.metadata.create_all(bind=engine)

# Apply non-destructive column migrations for pre-existing tables
from database import run_migrations
run_migrations()

app = FastAPI(
    title="QuickCommerce AI",
    description="AI-powered quick commerce shopping assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(profile.router)
app.include_router(recipe.router)
app.include_router(addresses.router)
app.include_router(payments.router)
app.include_router(orders.router)
app.include_router(bargain.router)
app.include_router(pairing.router)
app.include_router(meal_plan.router)
app.include_router(group.router)


@app.get("/")
def root():
    return {
        "message": "QuickCommerce AI API is running 🚀",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
