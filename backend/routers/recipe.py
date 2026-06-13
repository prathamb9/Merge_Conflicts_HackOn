from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserProfile
from schemas import RecipeRequest, RecipeResponse, RecommendedProduct
from services.llm_service import handle_recipe_request
from routers.auth import get_current_user

router = APIRouter(prefix="/api/recipe", tags=["recipe"])


@router.post("/parse", response_model=RecipeResponse)
def parse_recipe(
    request: RecipeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Parse a recipe into ingredients, match to catalog products,
    and return a single-click bundle.
    """
    try:
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()

        user_profile = None
        if profile:
            user_profile = {
                "is_vegetarian": profile.is_vegetarian,
                "is_vegan": profile.is_vegan,
                "is_high_protein": profile.is_high_protein,
                "weight_loss_mode": profile.weight_loss_mode,
            }

        result = handle_recipe_request(
            recipe_name=request.recipe,
            servings=request.servings,
            user_profile=user_profile,
            user_id=current_user.id,
            db=db,
        )

        return RecipeResponse(
            recipe_name=request.recipe,
            servings=request.servings,
            ingredients=result.get("skipped_ingredients", []) + [
                r.get("reason", "").replace("Ingredient: ", "")
                for r in result.get("recommendations", [])
            ],
            skipped_ingredients=result.get("skipped_ingredients", []),
            matched_products=[
                RecommendedProduct(**{
                    k: v for k, v in p.items()
                    if k in RecommendedProduct.model_fields
                })
                for p in result.get("recommendations", [])
            ],
            total=result.get("total", 0),
            message=result.get("message", ""),
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Recipe parsing error: {str(e)}"
        )
