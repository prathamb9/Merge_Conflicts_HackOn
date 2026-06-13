from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import json

from database import get_db
from models import User, UserProfile
from schemas import ProfileUpdate, ProfileResponse
from routers.auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    if not profile:
        return ProfileResponse(
            is_vegetarian=False,
            is_vegan=False,
            is_high_protein=False,
            weight_loss_mode=False,
            budget_preference=500,
            favorite_categories=[],
        )

    return ProfileResponse(
        is_vegetarian=profile.is_vegetarian,
        is_vegan=profile.is_vegan,
        is_high_protein=profile.is_high_protein,
        weight_loss_mode=profile.weight_loss_mode,
        budget_preference=profile.budget_preference,
        favorite_categories=json.loads(profile.favorite_categories or "[]"),
    )


@router.put("", response_model=ProfileResponse)
def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    profile.is_vegetarian = data.is_vegetarian
    profile.is_vegan = data.is_vegan
    profile.is_high_protein = data.is_high_protein
    profile.weight_loss_mode = data.weight_loss_mode
    profile.budget_preference = data.budget_preference
    profile.favorite_categories = json.dumps(data.favorite_categories)
    db.commit()
    db.refresh(profile)

    return ProfileResponse(
        is_vegetarian=profile.is_vegetarian,
        is_vegan=profile.is_vegan,
        is_high_protein=profile.is_high_protein,
        weight_loss_mode=profile.weight_loss_mode,
        budget_preference=profile.budget_preference,
        favorite_categories=data.favorite_categories,
    )
