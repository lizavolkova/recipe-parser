from fastapi import APIRouter
from app.models import RecipeURL, Recipe, DebugInfo
from app.services.recipe_service import RecipeService

router = APIRouter()

@router.post("/debug-recipe", response_model=DebugInfo)
def debug_recipe(recipe_url: RecipeURL):
    """Debug endpoint using extruct to show all structured data"""
    url_str = str(recipe_url.url)
    return RecipeService.debug_recipe(url_str)

@router.post("/parse-recipe", response_model=Recipe)
async def parse_recipe(recipe_url: RecipeURL):
    """
    Modern recipe parser: recipe-scrapers → extruct → AI fallback
    """
    print("🔧 ROUTE: Using NEW recipe service")
    url_str = str(recipe_url.url)
    return await RecipeService.parse_recipe_hybrid(url_str)
