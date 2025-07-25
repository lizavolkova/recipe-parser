# backend/app/routes/recipes.py (Safe version with fallback)
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional
from app.models import (
    RecipeURL, Recipe, DebugInfo, 
    RecipeSearchFilters, RecipeStats, BatchCategorizationRequest,
    BatchCategorizationStatus
)
from app.services.recipe_service import RecipeService

# Create router first (this is what was missing!)
router = APIRouter()

# Try to import AI services, but fall back gracefully if they fail
try:
    from app.services.ai.recipe_categorizer import EnhancedRecipeService, BatchCategorizationService
    AI_AVAILABLE = True
    print("✅ AI services imported successfully")
    enhanced_recipe_service = EnhancedRecipeService()
    batch_service = BatchCategorizationService()
except ImportError as e:
    AI_AVAILABLE = False
    print(f"⚠️ AI services not available: {e}")
    print("📝 Falling back to basic recipe parsing")
    enhanced_recipe_service = None
    batch_service = None
except Exception as e:
    AI_AVAILABLE = False
    print(f"❌ Error importing AI services: {e}")
    enhanced_recipe_service = None
    batch_service = None

@router.post("/debug-recipe", response_model=DebugInfo)
def debug_recipe(recipe_url: RecipeURL):
    """Debug endpoint using extruct to show all structured data"""
    url_str = str(recipe_url.url)
    return RecipeService.debug_recipe(url_str)

@router.post("/parse-recipe", response_model=Recipe)
async def parse_recipe(recipe_url: RecipeURL):
    """
    Parse recipe from URL with AI categorization (if available)
    Falls back to basic parsing if AI services aren't working
    """
    url_str = str(recipe_url.url)
    
    if AI_AVAILABLE and enhanced_recipe_service:
        print("🔧 ROUTE: Using AI-enhanced recipe service")
        try:
            return await enhanced_recipe_service.parse_and_categorize_recipe(url_str)
        except Exception as e:
            print(f"⚠️ AI enhancement failed: {e}")
            print("📝 Falling back to basic parsing")
            return await RecipeService.parse_recipe_hybrid(url_str)
    else:
        print("🔧 ROUTE: Using basic recipe service (AI not available)")
        return await RecipeService.parse_recipe_hybrid(url_str)

@router.post("/categorize-recipe", response_model=Recipe)
async def categorize_existing_recipe(recipe: Recipe):
    """
    Add AI categorization to an already-parsed recipe
    Only works if AI services are available
    """
    if not AI_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="AI categorization service not available. Check your setup."
        )
    
    try:
        from app.services.ai.recipe_categorizer import RecipeCategorizationService
        
        categorization_service = RecipeCategorizationService()
        categorization = await categorization_service.categorize_recipe(recipe)
        
        if not categorization:
            raise HTTPException(status_code=500, detail="AI categorization failed")
        
        # Create enhanced recipe with AI categorization
        enhanced_recipe = Recipe(
            title=recipe.title,
            description=recipe.description,
            image=recipe.image,
            source=recipe.source,
            ingredients=recipe.ingredients,
            instructions=recipe.instructions,
            prep_time=recipe.prep_time,
            cook_time=recipe.cook_time,
            servings=recipe.servings,
            cuisine=recipe.cuisine,
            category=recipe.category,
            keywords=recipe.keywords,
            found_structured_data=recipe.found_structured_data,
            used_ai=True,
            raw_ingredients=getattr(recipe, 'raw_ingredients', []),  # Handle missing field gracefully
            raw_ingredients_detailed=getattr(recipe, 'raw_ingredients_detailed', []),  # Handle missing field gracefully
            
            # Add AI categorization
            health_tags=categorization.health_tags,
            dish_type=categorization.dish_type,
            cuisine_type=categorization.cuisine_type,
            meal_type=categorization.meal_type,
            season=categorization.season,
            ai_confidence_notes=categorization.confidence_notes,
            ai_enhanced=True,
            ai_model_used=categorization.ai_model
        )
        
        return enhanced_recipe
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Categorization error: {str(e)}")

@router.get("/search", response_model=List[Recipe])
async def search_recipes(
    # Text search
    q: Optional[str] = Query(None, description="Search query"),
    
    # AI categorization filters (now standard)
    health: Optional[str] = Query(None, description="Health tags (comma-separated)"),
    dish: Optional[str] = Query(None, description="Dish types (comma-separated)"),
    cuisine: Optional[str] = Query(None, description="Cuisine types (comma-separated)"),
    meal: Optional[str] = Query(None, description="Meal types (comma-separated)"),
    season: Optional[str] = Query(None, description="Seasons (comma-separated)"),
    
    # Other filters
    max_prep: Optional[int] = Query(None, description="Max prep time in minutes"),
    max_cook: Optional[int] = Query(None, description="Max cook time in minutes"),
    has_image: Optional[bool] = Query(None, description="Has image"),
    
    # Pagination
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Advanced recipe search with AI categorization filters
    """
    # Parse comma-separated filter values
    filters = RecipeSearchFilters(
        query=q,
        health_tags=health.split(",") if health else [],
        dish_type=dish.split(",") if dish else [],
        cuisine_type=cuisine.split(",") if cuisine else [],
        meal_type=meal.split(",") if meal else [],
        season=season.split(",") if season else [],
        max_prep_time=max_prep,
        max_cook_time=max_cook,
        has_image=has_image,
        limit=limit,
        offset=offset
    )
    
    # TODO: Implement actual database search
    raise HTTPException(
        status_code=501, 
        detail="Recipe search not yet implemented. Need database integration first!"
    )

@router.get("/categories", response_model=dict)
async def get_available_categories():
    """
    Get all available categorization options for filtering
    """
    if not AI_AVAILABLE:
        # Return empty categories if AI not available
        return {
            "health_tags": [],
            "dish_types": [],
            "cuisine_types": [],
            "meal_types": [],
            "seasons": [],
            "ai_available": False
        }
    
    try:
        from app.services.ai.recipe_categorizer import RecipeCategorizationService
        service = RecipeCategorizationService()
        
        return {
            "health_tags": service.HEALTH_TAGS,
            "dish_types": service.DISH_TYPES,
            "cuisine_types": service.CUISINE_TYPES,
            "meal_types": service.MEAL_TYPES,
            "seasons": service.SEASONS,
            "ai_available": True
        }
    except Exception as e:
        return {
            "health_tags": [],
            "dish_types": [],
            "cuisine_types": [],
            "meal_types": [],
            "seasons": [],
            "ai_available": False,
            "error": str(e)
        }

@router.get("/stats", response_model=RecipeStats)
async def get_recipe_stats():
    """
    Get statistics about recipe categorization
    """
    # TODO: Implement with actual database queries
    return RecipeStats(
        total_recipes=0,
        ai_enhanced_count=0,
        ai_enhancement_percentage=0.0,
        top_health_tags=[],
        top_cuisines=[],
        top_dish_types=[],
        seasonal_distribution={"spring": 0, "summer": 0, "autumn": 0, "winter": 0}
    )

@router.post("/debug-ai-categorization", response_model=dict)
async def debug_ai_categorization(recipe_url: RecipeURL):
    """
    Debug endpoint to see exactly what the AI is thinking during categorization
    Useful for identifying why dietary tags might be wrong
    """
    if not AI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="AI categorization service not available"
        )
    
    try:
        from app.services.ai.recipe_categorizer import EnhancedRecipeService
        
        # Parse the recipe first
        enhanced_service = EnhancedRecipeService()
        recipe = await enhanced_service.parse_and_categorize_recipe(str(recipe_url.url))
        
        return {
            "recipe_title": recipe.title,
            "ingredients_analyzed": recipe.ingredients,
            "ai_categorization": {
                "health_tags": recipe.health_tags,
                "dish_type": recipe.dish_type,
                "cuisine_type": recipe.cuisine_type,
                "meal_type": recipe.meal_type,
                "season": recipe.season,
                "ai_confidence_notes": recipe.ai_confidence_notes,
                "ai_enhanced": recipe.ai_enhanced,
                "ai_model_used": recipe.ai_model_used
            },
            "debug_info": {
                "ingredient_count": len(recipe.ingredients),
                "should_be_vegan_if": "All ingredients appear to be plant-based (vegetables, oils, spices, etc.)",
                "check_for_animal_products": "Look for: meat, dairy, eggs, fish, honey, gelatin in ingredients above"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")

@router.post("/test-ai-categorization", response_model=Recipe)
async def test_ai_categorization():
    """
    Test endpoint to verify AI categorization is working correctly
    """
    if not AI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="AI categorization service not available. Check your OpenAI API key and setup."
        )
    
    try:
        from app.services.ai.recipe_categorizer import RecipeCategorizationService
        
        # Create a test recipe - a generic curry that should be all seasons
        test_recipe = Recipe(
            title="Creamy Coconut Curry",
            description="A rich and flavorful curry with coconut milk and spices",
            ingredients=[
                "1 can coconut milk",
                "2 tbsp curry powder",
                "1 onion, diced",
                "3 cloves garlic, minced",
                "1 tbsp ginger, minced",
                "1 can diced tomatoes",
                "1 tsp turmeric",
                "1 tsp garam masala",
                "Salt and pepper",
                "Fresh cilantro for garnish"
            ],
            instructions=[
                "Sauté onion, garlic, and ginger in oil until fragrant",
                "Add curry powder and spices, cook for 1 minute", 
                "Add diced tomatoes and coconut milk",
                "Simmer for 15-20 minutes until thickened",
                "Season with salt and pepper",
                "Garnish with fresh cilantro before serving"
            ],
            prep_time="10 minutes",
            cook_time="20 minutes",
            servings="4",
            raw_ingredients=[],  # Initialize the required field
            raw_ingredients_detailed=[]  # Initialize the required field
        )
        
        # Categorize it
        categorization_service = RecipeCategorizationService()
        categorization = await categorization_service.categorize_recipe(test_recipe)
        
        if not categorization:
            raise HTTPException(status_code=500, detail="AI categorization test failed")
        
        # Return enhanced recipe
        test_recipe.health_tags = categorization.health_tags
        test_recipe.dish_type = categorization.dish_type
        test_recipe.cuisine_type = categorization.cuisine_type
        test_recipe.meal_type = categorization.meal_type
        test_recipe.season = categorization.season
        test_recipe.ai_confidence_notes = categorization.confidence_notes
        test_recipe.ai_enhanced = True
        
        return test_recipe
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI test failed: {str(e)}")

@router.get("/ai-status", response_model=dict)
async def get_ai_status():
    """
    Check AI service status - useful for debugging
    """
    return {
        "ai_services_available": AI_AVAILABLE,
        "enhanced_service_loaded": enhanced_recipe_service is not None,
        "batch_service_loaded": batch_service is not None,
        "message": "AI services working correctly" if AI_AVAILABLE else "AI services not available - check your setup"
    }

# Background task storage (in production, use Redis or database)
batch_tasks = {}

@router.post("/batch-categorize", response_model=dict)
async def start_batch_categorization(
    request: BatchCategorizationRequest,
    background_tasks: BackgroundTasks
):
    """
    Start batch categorization of existing recipes (if AI available)
    """
    if not AI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="AI categorization service not available"
        )
    
    import uuid
    
    task_id = str(uuid.uuid4())
    batch_tasks[task_id] = BatchCategorizationStatus(
        status="in_progress",
        total_recipes=0,
        processed_count=0,
        success_count=0,
        error_count=0
    )
    
    # Add background task
    background_tasks.add_task(
        run_batch_categorization,
        task_id,
        request
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": "Batch categorization started in background"
    }

@router.get("/batch-categorize/{task_id}", response_model=BatchCategorizationStatus)
async def get_batch_status(task_id: str):
    """
    Get status of batch categorization task
    """
    if task_id not in batch_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return batch_tasks[task_id]

async def run_batch_categorization(task_id: str, request: BatchCategorizationRequest):
    """
    Background task for batch categorization
    """
    try:
        # TODO: Get recipes from database based on request
        batch_tasks[task_id].status = "completed"
        batch_tasks[task_id].total_recipes = 0
        batch_tasks[task_id].processed_count = 0
        batch_tasks[task_id].success_count = 0
        
    except Exception as e:
        batch_tasks[task_id].status = "failed"
        batch_tasks[task_id].errors.append(str(e))
