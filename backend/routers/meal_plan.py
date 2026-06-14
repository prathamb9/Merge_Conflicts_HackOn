from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json

from database import get_db
from models import User, UserProfile
from routers.auth import get_current_user
from services.meal_planner_service import generate_plan, consolidate_ingredients

router = APIRouter(prefix="/api/meal-plan", tags=["meal-plan"])


def _profile_prefs(user: User, db: Session) -> dict:
    p = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not p:
        return {}
    return {
        "is_vegetarian": p.is_vegetarian,
        "is_vegan": p.is_vegan,
        "is_high_protein": p.is_high_protein,
        "weight_loss_mode": p.weight_loss_mode,
    }


class PlanRequest(BaseModel):
    goal: str = "balanced healthy meals"
    days: int = 7
    servings: int = 2


class ConsolidateRequest(BaseModel):
    """Rebuild the shopping list after the user edits/removes meals."""
    ingredients: List[str]
    servings: int = 2


@router.post("")
def create_plan(
    data: PlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prefs = _profile_prefs(current_user, db)
    return generate_plan(
        goal=data.goal,
        days=data.days,
        servings=data.servings,
        preferences=prefs,
    )


@router.post("/consolidate")
def rebuild_shopping_list(
    data: ConsolidateRequest,
    current_user: User = Depends(get_current_user),
):
    """Used when the user removes meals on the client and rebuilds the list."""
    return consolidate_ingredients(data.ingredients, data.servings)
