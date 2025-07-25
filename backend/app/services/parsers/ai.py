import json
import traceback
from typing import Optional
from app.config import openai_client, settings
from app.models import Recipe
from app.utils.helpers import extract_main_content

async def parse_with_ai(soup, url: str) -> Optional[Recipe]:
    """Use AI to extract recipe information from HTML content"""
    
    if not openai_client:
        print("AI parsing requested but OpenAI client not available")
        return None
    
    try:
        print("🤖 Attempting AI parsing...")
        
        # Extract and clean content
        content = extract_main_content(soup)
        
        # Truncate content if too long to save on API costs
        if len(content) > settings.MAX_CONTENT_LENGTH:
            content = content[:settings.MAX_CONTENT_LENGTH] + "..."
        
        prompt = _build_extraction_prompt(content)
        
        response = openai_client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a recipe extraction expert. Extract recipe data accurately from webpage content."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.AI_TEMPERATURE,
            max_tokens=settings.AI_MAX_TOKENS
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"🤖 AI response: {ai_response[:200]}...")
        
        return _parse_ai_response(ai_response)
        
    except Exception as e:
        print(f"🤖 AI parsing failed: {e}")
        print(f"🤖 Traceback: {traceback.format_exc()}")
        return None

def _build_extraction_prompt(content: str) -> str:
    """Build the prompt for AI recipe extraction"""
    return f"""
    Extract recipe information from this webpage content. Return ONLY a JSON object with the following structure:

    {{
        "title": "Recipe name (string)",
        "description": "Brief recipe description (string or null)",
        "image": "Main recipe image URL (string or null)",
        "source": "Source organization/blog name like 'Love and Lemons' or 'Food Network' (string or null)",
        "ingredients": ["ingredient 1", "ingredient 2", ...],
        "instructions": ["step 1", "step 2", ...],
        "prep_time": "preparation time if mentioned (string or null)",
        "cook_time": "cooking time if mentioned (string or null)",
        "servings": "number of servings if mentioned (string or null)",
        "cuisine": "cuisine type like Italian, Mexican, Asian (string or null)",
        "category": "meal category like dinner, appetizer, dessert (string or null)",
        "keywords": ["keyword1", "keyword2", ...] (array of relevant tags/keywords)
    }}

    Important rules:
    1. Only extract actual recipe ingredients and cooking instructions
    2. Ignore: navigation menus, comments, advertisements, author bio, related recipes
    3. Each ingredient should include quantity and ingredient name
    4. Each instruction should be a complete cooking step
    5. For image: extract the main recipe photo URL (look for high-quality images, avoid icons/logos)
    6. For source: extract the ORGANIZATION/BLOG name (e.g., "Love and Lemons", "Asian Inspirations", "Food Network"), NOT individual person names
    7. For cuisine: identify the cooking style (Italian, Chinese, Mexican, etc.)
    8. For category: identify meal type (breakfast, lunch, dinner, appetizer, dessert, snack, etc.)
    9. For keywords: extract relevant cooking terms, dietary restrictions, techniques
    10. If you cannot find a clear recipe, return null
    11. Return only valid JSON, no additional text

    Webpage content:
    {content}
    """

def _parse_ai_response(ai_response: str) -> Optional[Recipe]:
    """Parse the AI response into a Recipe object"""
    
    # Check if AI determined this is not a recipe
    if ai_response.lower() == 'null' or not ai_response:
        print("🤖 AI determined this is not a recipe")
        return None
    
    try:
        recipe_data = json.loads(ai_response)
    except json.JSONDecodeError:
        # Sometimes AI wraps JSON in code blocks
        if "```json" in ai_response:
            json_start = ai_response.find("```json") + 7
            json_end = ai_response.find("```", json_start)
            json_str = ai_response[json_start:json_end].strip()
            try:
                recipe_data = json.loads(json_str)
            except json.JSONDecodeError:
                print(f"🤖 Failed to parse AI response as JSON: {ai_response}")
                return None
        else:
            print(f"🤖 Failed to parse AI response as JSON: {ai_response}")
            return None
    
    # Validate the response structure
    required_fields = ['title', 'ingredients', 'instructions']
    if not all(field in recipe_data for field in required_fields):
        print(f"🤖 AI response missing required fields: {recipe_data}")
        return None
    
    # Ensure keywords is a list
    keywords = recipe_data.get('keywords', [])
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(',') if k.strip()]
    elif not isinstance(keywords, list):
        keywords = []
    
    # Create Recipe object
    ai_recipe = Recipe(
        title=recipe_data.get('title', 'AI Extracted Recipe'),
        description=recipe_data.get('description'),
        image=recipe_data.get('image'),
        ingredients=recipe_data.get('ingredients', []),
        instructions=recipe_data.get('instructions', []),
        prep_time=recipe_data.get('prep_time'),
        cook_time=recipe_data.get('cook_time'),
        servings=recipe_data.get('servings'),
        cuisine=recipe_data.get('cuisine'),
        category=recipe_data.get('category'),
        keywords=keywords,
        found_structured_data=False,
        used_ai=True
    )
    
    print(f"🤖 AI extracted: {ai_recipe.title} with {len(ai_recipe.ingredients)} ingredients")
    print(f"🤖 AI metadata: cuisine={ai_recipe.cuisine}, category={ai_recipe.category}, keywords={len(ai_recipe.keywords)}")
    print(f"🤖 AI image: {ai_recipe.image}")
    return ai_recipe
