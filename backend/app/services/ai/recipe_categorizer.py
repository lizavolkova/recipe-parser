# backend/app/services/ai/recipe_categorizer.py (FIXED VERSION)
import json
import traceback
from typing import Optional, List, Dict, Any
from app.config import openai_client, settings
from app.models import Recipe, RecipeCategorization
import asyncio

class RecipeCategorizationService:
    """AI-powered recipe categorization service"""
    
    # Reference data for AI prompts
    HEALTH_TAGS = [
        "vegan", "vegetarian", "dairy free", "red meat free", "nut free", 
        "gluten free", "paleo", "keto", "FODMAP free", "pescatarian", 
        "healthy", "whole30"
    ]
    
    DISH_TYPES = [
        "bread", "dessert", "pies and tarts", "salad", "sandwich", "seafood",
        "side dish", "main course", "soup or stew", "curry", "special occasion",
        "starter or appetizer", "sweet", "pasta", "egg", "drink",
        "condiment or sauce", "grilling", "alcohol cocktail", "biscuits and cookies",
        "drinks", "ice cream and custard", "pizza", "preserve", "sheet pan meal",
        "grain bowl", "freezer-friendly"
    ]
    
    CUISINE_TYPES = [
        "american", "asian", "british", "caribbean", "central europe", "chinese",
        "eastern europe", "french", "greek", "indian", "italian", "japanese",
        "korean", "mediterranean", "mexican", "middle eastern", "nordic",
        "south american", "south east asian", "african"
    ]
    
    MEAL_TYPES = [
        "breakfast", "brunch", "lunch", "dinner", "snack", "dessert"
    ]
    
    SEASONS = [
        "spring", "summer", "winter", "autumn"
    ]
    
    async def categorize_recipe(self, recipe: Recipe) -> Optional[RecipeCategorization]:
        """
        Analyze a recipe and return AI-generated categorization
        """
        if not openai_client:
            print("❌ AI categorization requested but OpenAI client not available")
            return None
        
        try:
            print(f"🤖 Starting AI categorization for: {recipe.title}")
            
            prompt = self._build_categorization_prompt(recipe)
            
            response = openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=settings.AI_TEMPERATURE,  # Use configurable temperature
                max_tokens=settings.AI_MAX_TOKENS,
                seed=getattr(settings, 'AI_SEED', 42)  # Use configurable seed for consistency
            )
            
            ai_response = response.choices[0].message.content.strip()
            print(f"🤖 AI categorization response: {ai_response[:200]}...")
            
            return self._parse_categorization_response(ai_response, recipe.title)
            
        except Exception as e:
            print(f"🤖 AI categorization failed: {e}")
            print(f"🤖 Traceback: {traceback.format_exc()}")
            return None
    
    def _get_system_prompt(self) -> str:
        """System prompt that defines the AI's role and capabilities"""
        return f"""You are a culinary expert AI that categorizes recipes with high accuracy and CONSISTENCY. 

Your task is to analyze recipes and categorize them into specific categories. You should be comprehensive but accurate - a recipe can have multiple tags in each category when appropriate.

CRITICAL: ONLY analyze what is actually present in the recipe. Do NOT hallucinate or assume ingredients, cooking methods, or characteristics not explicitly mentioned.

CATEGORY GUIDELINES:

HEALTH TAGS - Use systematic analysis for dietary restrictions:
{', '.join(self.HEALTH_TAGS)}

DIETARY CLASSIFICATION RULES:
- VEGAN: Contains ZERO animal products (vegetables, fruits, grains, legumes, nuts, seeds, plant oils, soy sauce, vinegar, spices, herbs, agave syrup, chili crisp, tofu, tempeh, etc.)
- VEGETARIAN: No meat/seafood but may contain dairy/eggs
- PESCATARIAN: Contains fish/seafood but no other meat
- RED MEAT FREE: No beef, pork, lamb, or other red meat (but may contain poultry/fish)
- DAIRY FREE: No milk, cheese, butter, cream, yogurt, or other dairy products
- If ALL ingredients are plant-based, tag as VEGAN (not vegetarian)

RED MEAT INCLUDES: beef, pork, lamb, mutton, venison, bison, goat
POULTRY INCLUDES: chicken, turkey, duck, etc. (NOT red meat)

HEALTHY TAG CRITERIA - Tag as "healthy" if the dish has:
- Lots of vegetables or fruits as main components
- Lean proteins (fish, chicken, tofu, beans)
- Whole grains or minimal processing
- Limited fried foods or heavy cream sauces
- Balanced nutritional profile

DISH TYPES - What type of dish this is (can be multiple):
{', '.join(self.DISH_TYPES)}

COOKING METHOD DETECTION:
- If recipe mentions grilling, BBQ, or grill pan → include "grilling"
- If served as small portions or before main course → include "starter or appetizer"
- Look for cooking methods in instructions and title

CUISINE TYPES - The cultural/regional cooking style:
{', '.join(self.CUISINE_TYPES)}

CUISINE TAGGING RULES:
- Tag BOTH specific AND broader categories when applicable, but be culturally accurate
- Chinese/Korean/Thai/Vietnamese/Japanese → ALSO tag as "asian"
- Indian/Middle Eastern → Do NOT tag as "asian" (distinct flavor profiles)
- Italian/French/Spanish/Greek → Can tag as "mediterranean" if appropriate
- Examples: "chinese, asian" or "thai, asian" but just "indian" (not "indian, asian")

MEAL TYPES - When this would typically be eaten (can be multiple):
{', '.join(self.MEAL_TYPES)}

MEAL TYPE FLEXIBILITY:
- Many dishes work for multiple meals (lunch AND dinner)
- Consider portion size and ingredients
- Don't be overly restrictive - if it could reasonably be eaten at different times, include multiple tags

SEASONS - When ingredients are typically in season or dish is commonly eaten:
{', '.join(self.SEASONS)}

SEASONAL ASSIGNMENT RULES:
- Consider the main ingredients and dish characteristics
- Cold salads with summer vegetables (cucumber, tomato) = summer primarily
- Warm soups and stews can be autumn AND winter (not just one)
- Light, refreshing dishes = summer
- Hearty, warming dishes = autumn and/or winter
- Fresh spring vegetables = spring
- Many dishes work across multiple seasons - don't be overly restrictive

SEASONAL EXAMPLES:
- Cucumber salad = summer
- Roasted garlic soup = autumn, winter (both)
- Pumpkin soup = autumn
- Asparagus dishes = spring
- Grilled dishes = summer (but can span multiple if hearty)

IMPORTANT RULES:
1. Only use tags from the provided lists
2. Be generous with applicable tags when appropriate - better to include relevant tags than miss them
3. For health tags, systematically check all ingredients and cooking methods
4. For seasons and meal types, don't be overly restrictive - many dishes work across categories
5. Always include broader cuisine categories (asian, mediterranean) alongside specific ones
6. Detect cooking methods from instructions and titles
7. Consider the "healthy" tag generously for vegetable-forward, balanced dishes
8. Only reference ingredients and cooking methods that are ACTUALLY in the recipe
9. Always return valid JSON in the exact format requested
10. BE CONSISTENT - same recipe should always get same categorization
11. If all ingredients are plant-based, tag as VEGAN (not vegetarian)
12. Remember: lamb, beef, pork = red meat; chicken, turkey = poultry (not red meat)"""

    def _build_categorization_prompt(self, recipe: Recipe) -> str:
        """Build the user prompt with recipe data"""
        
        # Create a clean ingredient list
        ingredients_text = "\n".join([f"- {ing}" for ing in recipe.ingredients[:15]])  # Limit for token efficiency
        if len(recipe.ingredients) > 15:
            ingredients_text += f"\n... and {len(recipe.ingredients) - 15} more ingredients"
        
        # Create a clean instruction summary
        instructions_text = " ".join(recipe.instructions[:3])[:300] + "..." if recipe.instructions else "No instructions provided"
        
        return f"""Analyze this recipe and categorize it systematically:

**RECIPE: {recipe.title}**

**DESCRIPTION:** {recipe.description or 'No description provided'}

**INGREDIENTS:**
{ingredients_text}

**COOKING METHOD:** {instructions_text}

**ADDITIONAL CONTEXT:**
- Prep time: {recipe.prep_time or 'Unknown'}
- Cook time: {recipe.cook_time or 'Unknown'}
- Servings: {recipe.servings or 'Unknown'}
- Source: {recipe.source or 'Unknown'}

Return ONLY a JSON object with this exact structure (pay attention to commas):
{{
    "health_tags": ["tag1", "tag2"],
    "dish_type": ["type1", "type2"],
    "cuisine_type": ["cuisine1"],
    "meal_type": ["meal1", "meal2"],
    "season": ["season1"],
    "confidence_notes": "Friendly explanation of why you chose these categories"
}}

JSON FORMATTING REQUIREMENTS:
- CRITICAL: Include commas after every field except the last one
- Use double quotes around all keys and string values
- Use square brackets for arrays, even if empty: []
- Ensure proper comma placement - missing commas will cause parsing errors

CONFIDENCE NOTES STYLE:
- Explain your reasoning in a natural, conversational way
- Focus on what led you to pick specific categories
- Be friendly and approachable, not robotic or overly formal
- Keep it concise but informative about your choices

EXAMPLES OF GOOD CONFIDENCE NOTES:
- "This is vegan since it uses only plant ingredients. Perfect for summer with its cool, refreshing cucumber base."
- "All plant-based ingredients make this vegan. The warming braised cooking method screams winter comfort food."
- "Completely plant-based, so it's vegan. The traditional soy sauce and stir-fry technique point to Asian cuisine."
- "No animal products here, making it vegan. The oats and morning-friendly ingredients make this ideal for breakfast."

IMPORTANT REMINDERS:
- If ALL ingredients are plant-based, tag as VEGAN (not vegetarian)
- Consider dish characteristics for seasonal assignment (cucumber salad = summer)
- Only reference ingredients and cooking methods actually in the recipe
- Be consistent - same recipe should always get same categorization"""

    def _parse_categorization_response(self, ai_response: str, recipe_title: str) -> Optional[RecipeCategorization]:
        """Parse AI response into RecipeCategorization object with robust JSON handling"""
        
        try:
            # Handle JSON wrapped in code blocks
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                json_str = ai_response[json_start:json_end].strip()
            else:
                json_str = ai_response
            
            # Try to parse JSON, with fallback for common formatting issues
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"🤖 Initial JSON parse failed: {e}")
                print(f"🤖 Attempting to fix common JSON issues...")
                
                # Try to fix common issues
                fixed_json = self._fix_common_json_issues(json_str)
                try:
                    data = json.loads(fixed_json)
                    print(f"🤖 JSON fixed and parsed successfully!")
                except json.JSONDecodeError:
                    print(f"🤖 Could not fix JSON formatting")
                    print(f"🤖 Raw response: {ai_response}")
                    return None
            
            # Validate required fields
            required_fields = ['health_tags', 'dish_type', 'cuisine_type', 'meal_type', 'season']
            for field in required_fields:
                if field not in data:
                    print(f"🤖 Missing required field '{field}' in AI response")
                    return None
            
            # Ensure all fields are lists
            for field in required_fields:
                if not isinstance(data[field], list):
                    data[field] = [data[field]] if data[field] else []
            
            # Validate tags against known lists
            data['health_tags'] = self._validate_tags(data['health_tags'], self.HEALTH_TAGS, 'health_tags')
            data['dish_type'] = self._validate_tags(data['dish_type'], self.DISH_TYPES, 'dish_types')
            data['cuisine_type'] = self._validate_tags(data['cuisine_type'], self.CUISINE_TYPES, 'cuisine_types')
            data['meal_type'] = self._validate_tags(data['meal_type'], self.MEAL_TYPES, 'meal_types')
            data['season'] = self._validate_tags(data['season'], self.SEASONS, 'seasons')
            
            # Updated: Only default to all seasons if no valid seasons were returned AND it's not a clearly seasonal dish
            if not data['season']:
                # Check if this might be a seasonal dish that AI missed
                title_lower = recipe_title.lower()
                if any(term in title_lower for term in ['cucumber', 'tomato', 'gazpacho', 'cold soup']):
                    data['season'] = ['summer']
                    print(f"🤖 Applied summer season based on dish characteristics: {recipe_title}")
                elif any(term in title_lower for term in ['pumpkin', 'butternut', 'hot chocolate', 'stew']):
                    data['season'] = ['autumn', 'winter']
                    print(f"🤖 Applied autumn/winter season based on dish characteristics: {recipe_title}")
                else:
                    data['season'] = self.SEASONS.copy()
                    print(f"🤖 No specific seasons identified, defaulting to all seasons: {recipe_title}")
            
            categorization = RecipeCategorization(
                health_tags=data['health_tags'],
                dish_type=data['dish_type'],
                cuisine_type=data['cuisine_type'],
                meal_type=data['meal_type'],
                season=data['season'],
                confidence_notes=data.get('confidence_notes', ''),
                ai_model=settings.AI_MODEL
            )
            
            print(f"✅ AI categorization successful for {recipe_title}")
            print(f"   Health: {categorization.health_tags}")
            print(f"   Dish: {categorization.dish_type}")
            print(f"   Cuisine: {categorization.cuisine_type}")
            print(f"   Meal: {categorization.meal_type}")
            print(f"   Season: {categorization.season}")
            print(f"   Reasoning: {categorization.confidence_notes[:100]}...")
            
            return categorization
            
        except json.JSONDecodeError as e:
            print(f"🤖 JSON decode error: {e}")
            print(f"🤖 Raw response: {ai_response}")
            return None
        except Exception as e:
            print(f"🤖 Error parsing categorization response: {e}")
            return None
    
    def _fix_common_json_issues(self, json_str: str) -> str:
        """Attempt to fix common JSON formatting issues"""
        import re
        
        # Fix missing commas before "confidence_notes"
        json_str = re.sub(r'(\])\s*("confidence_notes")', r'\1,\n    \2', json_str)
        
        # Fix missing commas before any field that starts with a quote
        json_str = re.sub(r'(\]|\})\s*("[\w_]+":)', r'\1,\n    \2', json_str)
        
        # Fix trailing commas before closing brace
        json_str = re.sub(r',\s*\}', r'\n}', json_str)
        
        return json_str
    
    def _validate_tags(self, tags: List[str], valid_tags: List[str], category: str) -> List[str]:
        """Validate and filter tags against known good tags"""
        if not tags:
            return []
        
        # Convert to lowercase for comparison
        valid_tags_lower = [tag.lower() for tag in valid_tags]
        validated = []
        
        for tag in tags:
            tag_lower = tag.lower().strip()
            if tag_lower in valid_tags_lower:
                # Find the original casing from valid_tags
                original_tag = valid_tags[valid_tags_lower.index(tag_lower)]
                validated.append(original_tag)
            else:
                print(f"⚠️ Invalid {category} tag ignored: '{tag}'")
        
        return validated

# Enhanced recipe service integration (no changes needed)
class EnhancedRecipeService:
    """Enhanced recipe service that includes AI categorization"""
    
    def __init__(self):
        from app.services.parsers import RecipeScrapersParser, ExtructParser
        from app.services.processors import ImageExtractor
        
        self.recipe_scrapers_parser = RecipeScrapersParser()
        self.extruct_parser = ExtructParser()
        self.categorization_service = RecipeCategorizationService()
    
    async def parse_and_categorize_recipe(self, url: str) -> Recipe:
        """
        Parse recipe from URL and add AI categorization
        Integrates with existing parsing pipeline
        """
        # Import here to avoid circular imports
        from app.services.recipe_service import RecipeService
        
        try:
            print(f"🔍 Starting enhanced recipe parsing for: {url}")
            
            # Step 1: Use existing parsing pipeline
            recipe = await RecipeService.parse_recipe_hybrid(url)
            
            if not recipe or recipe.title == "Unable to parse recipe":
                print("❌ Base recipe parsing failed, skipping categorization")
                return recipe
            
            # Step 2: Add AI categorization
            categorization = await self.categorization_service.categorize_recipe(recipe)
            
            if categorization:
                # Enhance the recipe with categorization data
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
                    cuisine=recipe.cuisine,  # Keep original if any
                    category=recipe.category,  # Keep original if any
                    keywords=recipe.keywords,
                    found_structured_data=recipe.found_structured_data,
                    used_ai=True,  # Mark as AI-enhanced
                    raw_ingredients=getattr(recipe, 'raw_ingredients', []),  # Handle missing field gracefully
                    raw_ingredients_detailed=getattr(recipe, 'raw_ingredients_detailed', []),  # Handle missing field gracefully
                    
                    # Add new categorization fields
                    health_tags=categorization.health_tags,
                    dish_type=categorization.dish_type,
                    cuisine_type=categorization.cuisine_type,
                    meal_type=categorization.meal_type,
                    season=categorization.season,
                    ai_confidence_notes=categorization.confidence_notes,
                    ai_enhanced=True,
                    ai_model_used=categorization.ai_model
                )
                
                print(f"✅ Recipe successfully enhanced with AI categorization")
                return enhanced_recipe
            else:
                print("⚠️ AI categorization failed, returning base recipe")
                return recipe
                
        except Exception as e:
            print(f"❌ Enhanced recipe parsing failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

# Batch categorization for existing recipes (no changes needed)
class BatchCategorizationService:
    """Service for categorizing existing recipes in bulk"""
    
    def __init__(self):
        self.categorization_service = RecipeCategorizationService()
    
    async def categorize_recipes_batch(self, recipes: List[Recipe], batch_size: int = 5) -> List[Recipe]:
        """
        Categorize multiple recipes with rate limiting
        """
        enhanced_recipes = []
        
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            print(f"🔄 Processing batch {i//batch_size + 1} ({len(batch)} recipes)")
            
            # Process batch
            batch_tasks = [
                self.categorization_service.categorize_recipe(recipe) 
                for recipe in batch
            ]
            
            categorizations = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Apply categorizations
            for recipe, categorization in zip(batch, categorizations):
                if isinstance(categorization, RecipeCategorization):
                    enhanced_recipe = self._apply_categorization(recipe, categorization)
                    enhanced_recipes.append(enhanced_recipe)
                else:
                    print(f"⚠️ Categorization failed for {recipe.title}")
                    enhanced_recipes.append(recipe)
            
            # Rate limiting - be nice to the API
            if i + batch_size < len(recipes):
                print("⏳ Rate limiting pause...")
                await asyncio.sleep(2)
        
        return enhanced_recipes
    
    def _apply_categorization(self, recipe: Recipe, categorization: RecipeCategorization) -> Recipe:
        """Apply categorization to a recipe"""
        return Recipe(
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
            
            # Enhanced fields
            health_tags=categorization.health_tags,
            dish_type=categorization.dish_type,
            cuisine_type=categorization.cuisine_type,
            meal_type=categorization.meal_type,
            season=categorization.season,
            ai_confidence_notes=categorization.confidence_notes,
            ai_enhanced=True,
            ai_model_used=categorization.ai_model
        )
