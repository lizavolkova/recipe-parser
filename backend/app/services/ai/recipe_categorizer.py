# backend/app/services/ai/recipe_categorizer.py (Updated with explicit dietary reasoning)
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

HEALTH TAGS - Use SYSTEMATIC analysis for dietary restrictions:
{', '.join(self.HEALTH_TAGS)}

DIETARY ANALYSIS - STEP BY STEP PROCESS:
1. First, list every single ingredient in the recipe
2. For each ingredient, determine if it contains animal products
3. Apply the most specific applicable category

VEGAN INGREDIENTS (NO animal products):
- ALL vegetables, fruits, grains, legumes, nuts, seeds
- Plant oils (olive oil, sesame oil, vegetable oil, peanut oil, coconut oil)
- Plant-based seasonings (soy sauce, vinegar, salt, sugar, spices, herbs)
- Tofu, tempeh, plant-based milks, nutritional yeast
- Garlic, ginger, onions, scallions, chilies, etc.

NON-VEGAN INGREDIENTS (contain animal products):
- Meat: beef, pork, chicken, lamb, etc.
- Dairy: milk, butter, cream, cheese, yogurt, ghee
- Eggs: whole eggs, egg whites, egg yolks
- Seafood: fish, shrimp, crab, lobster, oysters, fish sauce
- Animal-derived: honey, gelatin, lard, bone broth, chicken/beef stock
- Some processed items: worcestershire sauce (often contains anchovies), some wines

DIETARY HIERARCHY (choose the MOST SPECIFIC that applies):
1. VEGAN: Contains ZERO animal products (most restrictive)
2. VEGETARIAN: No meat/seafood but may contain dairy/eggs
3. PESCATARIAN: Contains fish/seafood but no other meat
4. No dietary restriction if contains meat

SYSTEMATIC CHECKING PROCESS:
- Go through EVERY ingredient one by one
- Ask: "Does this ingredient come from an animal?"
- If ALL ingredients are plant-based → VEGAN
- If contains dairy/eggs but no meat/fish → VEGETARIAN  
- If contains fish but no other meat → PESCATARIAN
- BE PRECISE: Don't guess, use the ingredient lists above

DISH TYPES - What type of dish this is (can be multiple):
{', '.join(self.DISH_TYPES)}

CUISINE TYPES - The cultural/regional cooking style:
{', '.join(self.CUISINE_TYPES)}

MEAL TYPES - When this would typically be eaten:
{', '.join(self.MEAL_TYPES)}

SEASONS - When ingredients are typically in season or dish is commonly eaten:
{', '.join(self.SEASONS)}

SEASONAL ASSIGNMENT RULES:
1. DEFAULT to ALL 4 SEASONS unless there are strong seasonal indicators
2. Only assign specific seasons if there are multiple clear seasonal cues (seasonal ingredients + seasonal cooking methods)
3. Generic dishes (curries, pasta, basic proteins) = ALL seasons unless strong seasonal elements
4. Don't assign seasons based on single ingredients unless they're strongly seasonal (like asparagus = spring)

CONSISTENCY REQUIREMENTS:
- Always apply the same logic to the same ingredients
- Use systematic dietary analysis, not guesswork
- Be deterministic - same recipe should always get same categorization
- When uncertain, choose the more conservative/broader category

IMPORTANT RULES:
1. Only use tags from the provided lists
2. Be generous with applicable tags - better to include more relevant tags than miss them
3. For health tags, use SYSTEMATIC ingredient-by-ingredient analysis
4. For seasons, be CONSERVATIVE - default to all 4 seasons unless multiple strong seasonal indicators
5. Only reference ingredients and cooking methods that are ACTUALLY in the recipe
6. Never hallucinate or assume information not provided
7. Always return valid JSON in the exact format requested
8. Base decisions ONLY on actual ingredients, cooking methods, and traditional associations
9. BE CONSISTENT - same input should always produce same output
10. For dietary analysis, be METHODICAL - check every single ingredient against the lists above"""

    def _build_categorization_prompt(self, recipe: Recipe) -> str:
        """Build the user prompt with recipe data"""
        
        # Create a clean ingredient list
        ingredients_text = "\n".join([f"- {ing}" for ing in recipe.ingredients[:15]])  # Limit for token efficiency
        if len(recipe.ingredients) > 15:
            ingredients_text += f"\n... and {len(recipe.ingredients) - 15} more ingredients"
        
        # Create a clean instruction summary
        instructions_text = " ".join(recipe.instructions[:3])[:300] + "..." if recipe.instructions else "No instructions provided"
        
        return f"""Analyze this recipe and categorize it SYSTEMATICALLY and CONSISTENTLY:

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

Return ONLY a JSON object with this exact structure:
{{
    "health_tags": ["tag1", "tag2"],
    "dish_type": ["type1", "type2"],
    "cuisine_type": ["cuisine1"],
    "meal_type": ["meal1", "meal2"],
    "season": ["season1", "season2", "season3", "season4"],
    "confidence_notes": "MUST include detailed dietary analysis explanation"
}}

MANDATORY DIETARY ANALYSIS PROCESS (MUST be included in confidence_notes):

STEP 1: List every single ingredient from the recipe
STEP 2: For each ingredient, explicitly state whether it's PLANT-BASED or ANIMAL-BASED
STEP 3: Justify your final dietary classification

FORMAT YOUR DIETARY ANALYSIS EXACTLY LIKE THIS in confidence_notes:
"Dietary Analysis: [ingredient 1] = plant-based, [ingredient 2] = plant-based, [ingredient 3] = plant-based, etc. 
Since ALL ingredients are plant-based, this recipe is VEGAN."

OR if not vegan:
"Dietary Analysis: [ingredient 1] = plant-based, [ingredient 2] = ANIMAL-BASED (contains dairy/eggs/meat), etc. 
Since [specific ingredient] contains [specific animal product], this recipe is VEGETARIAN, not vegan."

CRITICAL RULES FOR DIETARY CLASSIFICATION:
- If you tag as VEGETARIAN instead of VEGAN, you MUST explicitly identify which ingredient contains animal products
- If you cannot identify any animal products but still tag as VEGETARIAN, explain why
- Common plant-based ingredients that are NOT animal products:
  * Soy sauce (fermented soybeans - VEGAN)
  * All vegetable oils (olive, sesame, peanut, etc. - VEGAN)
  * Rice vinegar (plant-based - VEGAN)
  * Sugar (plant-based - VEGAN)
  * All vegetables, fruits, nuts, seeds, spices, herbs (VEGAN)
  * Tofu, tempeh (plant-based - VEGAN)

EXAMPLES OF PROPER DIETARY ANALYSIS:
Example 1: "Dietary Analysis: cucumbers = plant-based, sesame oil = plant-based, soy sauce = plant-based, rice vinegar = plant-based, garlic = plant-based. Since ALL ingredients are plant-based, this recipe is VEGAN."

Example 2: "Dietary Analysis: pasta = plant-based, tomatoes = plant-based, parmesan cheese = ANIMAL-BASED (contains dairy). Since parmesan cheese contains dairy, this recipe is VEGETARIAN, not vegan."

CRITICAL INSTRUCTIONS FOR SEASONAL ASSIGNMENT:
- DEFAULT to ALL 4 SEASONS unless there are multiple strong seasonal indicators
- Only assign specific seasons if there are several clear seasonal cues together
- Generic dishes (curries, pasta, basic proteins, stews, salads) = ALL seasons unless strong seasonal elements

ACCURACY REQUIREMENTS:
- Only reference ingredients that are actually listed in the recipe
- Only reference cooking methods that are actually described in the instructions  
- Do not hallucinate or assume any information not provided
- BE CONSISTENT - this exact recipe should always get the same categorization
- MOST IMPORTANTLY: If you tag as VEGETARIAN, you MUST explain exactly which ingredient contains animal products and why

Remember:
- Include ALL applicable tags for each category
- For health_tags, you MUST provide step-by-step ingredient analysis in confidence_notes
- For seasons, be CONSERVATIVE - default to all 4 seasons for generic dishes
- Base decisions ONLY on actual recipe content, never assume or hallucinate
- CONSISTENCY IS CRITICAL - same recipe must always get same result
- MANDATORY: Your confidence_notes must include the detailed dietary analysis format shown above"""

    def _parse_categorization_response(self, ai_response: str, recipe_title: str) -> Optional[RecipeCategorization]:
        """Parse AI response into RecipeCategorization object"""
        
        try:
            # Handle JSON wrapped in code blocks
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                json_str = ai_response[json_start:json_end].strip()
            else:
                json_str = ai_response
            
            data = json.loads(json_str)
            
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
            
            # Conservative approach: default to all seasons if none specified or if validation removed all
            if not data['season']:
                data['season'] = self.SEASONS.copy()
                print(f"🤖 No specific seasons identified, defaulting to all seasons (conservative approach): {recipe_title}")
            
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

# Enhanced recipe service integration
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

# Batch categorization for existing recipes
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
