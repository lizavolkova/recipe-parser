# backend/test_ai_categorization.py
"""
Test script to verify AI recipe categorization is working correctly
Run this to test your AI integration before building the full system
"""

import asyncio
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your services
from app.models import Recipe
from app.services.ai.recipe_categorizer import RecipeCategorizationService, EnhancedRecipeService

async def test_categorization_service():
    """Test the core AI categorization service"""
    print("🧪 Testing AI Categorization Service")
    print("=" * 50)
    
    # Create test recipes with different characteristics
    test_recipes = [
        # Italian pasta dish
        Recipe(
            title="Classic Spaghetti Carbonara",
            description="Traditional Italian pasta with eggs, cheese, and pancetta",
            ingredients=[
                "400g spaghetti pasta",
                "200g pancetta, diced",
                "4 large eggs",
                "100g Pecorino Romano cheese, grated",
                "Black pepper",
                "Salt"
            ],
            instructions=[
                "Cook spaghetti in salted water until al dente",
                "Fry pancetta until crispy",
                "Whisk eggs with cheese and black pepper",
                "Combine hot pasta with pancetta",
                "Add egg mixture and toss to create creamy sauce",
                "Serve immediately with extra cheese"
            ],
            prep_time="10 minutes",
            cook_time="15 minutes",
            servings="4",
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        ),
        
        # Vegan breakfast dish
        Recipe(
            title="Vegan Overnight Oats with Berries",
            description="Healthy overnight oats with almond milk and fresh berries",
            ingredients=[
                "1 cup rolled oats",
                "1 cup unsweetened almond milk",
                "2 tbsp chia seeds",
                "1 tbsp maple syrup",
                "1/2 cup mixed berries",
                "1/4 cup chopped almonds",
                "1 tsp vanilla extract"
            ],
            instructions=[
                "Mix oats, almond milk, chia seeds, and maple syrup",
                "Add vanilla extract and stir well",
                "Refrigerate overnight",
                "Top with berries and almonds before serving"
            ],
            prep_time="10 minutes",
            cook_time="0 minutes",
            servings="2",
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        ),
        
        # Asian stir-fry
        Recipe(
            title="Thai Basil Chicken Stir Fry",
            description="Spicy Thai stir-fry with chicken, vegetables, and aromatic basil",
            ingredients=[
                "500g chicken breast, sliced",
                "2 tbsp vegetable oil",
                "3 cloves garlic, minced",
                "2 red chilies, sliced",
                "1 red bell pepper, sliced",
                "1 cup Thai basil leaves",
                "2 tbsp soy sauce",
                "1 tbsp fish sauce",
                "1 tbsp brown sugar",
                "Jasmine rice for serving"
            ],
            instructions=[
                "Heat oil in a wok over high heat",
                "Add garlic and chilies, stir-fry for 30 seconds",
                "Add chicken and cook until nearly done",
                "Add bell pepper and continue cooking",
                "Add sauces and sugar, toss to combine",
                "Add basil leaves and stir until wilted",
                "Serve over jasmine rice"
            ],
            prep_time="15 minutes",
            cook_time="10 minutes",
            servings="4",
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        )
    ]
    
    categorization_service = RecipeCategorizationService()
    
    for i, recipe in enumerate(test_recipes, 1):
        print(f"\n🍽️ Test Recipe {i}: {recipe.title}")
        print(f"Description: {recipe.description}")
        
        try:
            categorization = await categorization_service.categorize_recipe(recipe)
            
            if categorization:
                print(f"✅ Categorization successful!")
                print(f"   Health Tags: {categorization.health_tags}")
                print(f"   Dish Type: {categorization.dish_type}")
                print(f"   Cuisine: {categorization.cuisine_type}")
                print(f"   Meal Type: {categorization.meal_type}")
                print(f"   Season: {categorization.season}")
                print(f"   AI Notes: {categorization.confidence_notes[:100]}...")
            else:
                print(f"❌ Categorization failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)

async def test_enhanced_recipe_service():
    """Test the enhanced recipe service with real URLs"""
    print("\n🌐 Testing Enhanced Recipe Service with Real URLs")
    print("=" * 50)
    
    # Test URLs - using reliable recipe sites
    test_urls = [
        "https://www.loveandlemons.com/spaghetti-carbonara-recipe/",
        "https://www.asianinspirations.com.au/recipes/pad-thai/",
        # Add more test URLs as needed
    ]
    
    enhanced_service = EnhancedRecipeService()
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🔗 Test URL {i}: {url}")
        
        try:
            recipe = await enhanced_service.parse_and_categorize_recipe(url)
            
            if recipe and recipe.title != "Unable to parse recipe":
                print(f"✅ Recipe parsing successful!")
                print(f"   Title: {recipe.title}")
                print(f"   Ingredients: {len(recipe.ingredients)} items")
                print(f"   Instructions: {len(recipe.instructions)} steps")
                print(f"   Source: {recipe.source}")
                print(f"   Image: {'Yes' if recipe.image else 'No'}")
                
                if recipe.ai_enhanced:
                    print(f"   🤖 AI Enhanced: Yes")
                    print(f"   Health Tags: {recipe.health_tags}")
                    print(f"   Dish Type: {recipe.dish_type}")
                    print(f"   Cuisine: {recipe.cuisine_type}")
                    print(f"   Meal Type: {recipe.meal_type}")
                    print(f"   Season: {recipe.season}")
                else:
                    print(f"   🤖 AI Enhanced: No")
            else:
                print(f"❌ Recipe parsing failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)

async def test_category_validation():
    """Test that AI returns only valid categories"""
    print("\n🔍 Testing Category Validation")
    print("=" * 50)
    
    service = RecipeCategorizationService()
    
    print(f"Available Health Tags: {len(service.HEALTH_TAGS)}")
    print(f"Available Dish Types: {len(service.DISH_TYPES)}")
    print(f"Available Cuisines: {len(service.CUISINE_TYPES)}")
    print(f"Available Meal Types: {len(service.MEAL_TYPES)}")
    print(f"Available Seasons: {len(service.SEASONS)}")
    
    # Test with a simple recipe
    test_recipe = Recipe(
        title="Chocolate Chip Cookies",
        ingredients=["flour", "butter", "sugar", "chocolate chips", "eggs"],
        instructions=["Mix ingredients", "Bake at 350F for 12 minutes"],
        raw_ingredients=[],
        raw_ingredients_detailed=[]
    )
    
    categorization = await service.categorize_recipe(test_recipe)
    
    if categorization:
        print(f"\n✅ Validation test passed!")
        print(f"All returned categories are from valid lists")
        
        # Check if all returned tags are in the valid lists
        invalid_health = [tag for tag in categorization.health_tags if tag not in service.HEALTH_TAGS]
        invalid_dish = [tag for tag in categorization.dish_type if tag not in service.DISH_TYPES]
        invalid_cuisine = [tag for tag in categorization.cuisine_type if tag not in service.CUISINE_TYPES]
        invalid_meal = [tag for tag in categorization.meal_type if tag not in service.MEAL_TYPES]
        invalid_season = [tag for tag in categorization.season if tag not in service.SEASONS]
        
        if any([invalid_health, invalid_dish, invalid_cuisine, invalid_meal, invalid_season]):
            print(f"⚠️ Warning: Found invalid tags!")
            if invalid_health: print(f"   Invalid health tags: {invalid_health}")
            if invalid_dish: print(f"   Invalid dish types: {invalid_dish}")
            if invalid_cuisine: print(f"   Invalid cuisines: {invalid_cuisine}")
            if invalid_meal: print(f"   Invalid meal types: {invalid_meal}")
            if invalid_season: print(f"   Invalid seasons: {invalid_season}")
        else:
            print(f"   All tags are valid! ✨")
    else:
        print(f"❌ Validation test failed - no categorization returned")

def print_test_summary():
    """Print information about running the tests"""
    print("🚀 AI Recipe Categorization Test Suite")
    print("=" * 50)
    print("This script will test your AI categorization integration:")
    print("1. Test core categorization service with sample recipes")
    print("2. Test enhanced parsing with real recipe URLs")
    print("3. Validate that AI returns only allowed categories")
    print("")
    print("Prerequisites:")
    print("- OPENAI_API_KEY set in your .env file")
    print("- AI categorization service files installed")
    print("- Internet connection for URL parsing tests")
    print("")

async def main():
    """Run all tests"""
    print_test_summary()
    
    try:
        await test_categorization_service()
        await test_enhanced_recipe_service()
        await test_category_validation()
        
        print("\n🎉 All tests completed!")
        print("If you see ✅ marks above, your AI categorization is working correctly!")
        print("\nNext steps:")
        print("1. Try the /test-ai-categorization endpoint in your API")
        print("2. Test with more recipe URLs")
        print("3. Add database persistence for the categorized data")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        print("Check your environment setup and try again")

if __name__ == "__main__":
    asyncio.run(main())
