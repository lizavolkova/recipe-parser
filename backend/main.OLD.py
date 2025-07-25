from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import requests
from bs4 import BeautifulSoup
import json
import traceback
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Create the FastAPI application instance
app = FastAPI(
    title="Recipe Parser API", 
    version="1.0.0",
    description="An AI-powered recipe parser that extracts structured data from recipe URLs"
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

openai_client = None
if os.getenv('OPENAI_API_KEY'):
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    print("✅ OpenAI client initialized")
else:
    print("ℹ️ No OpenAI API key found - AI fallback disabled")

# Pydantic models for request/response validation
class RecipeURL(BaseModel):
    url: HttpUrl

class Recipe(BaseModel):
    title: str
    ingredients: List[str]
    instructions: List[str]
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    servings: Optional[str] = None
    found_structured_data: bool = False
    used_ai: bool = False 

@app.get("/")
def read_root():
    """Basic hello world endpoint"""
    return {"message": "Hello, Recipe Parser!"}

@app.get("/health")
def health_check():
    """Health check endpoint - useful for monitoring"""
    return {"status": "healthy"}

@app.post("/debug-recipe")
def debug_recipe(recipe_url: RecipeURL):
    """Debug endpoint to see what's in the HTML"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(str(recipe_url.url), headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find JSON-LD scripts
        json_scripts = soup.find_all('script', type='application/ld+json')
        
        debug_info = {
            "status": "success",
            "html_length": len(response.content),
            "json_scripts_found": len(json_scripts),
            "json_scripts_content": [],
            "ai_available": openai_client is not None
        }
        
        for i, script in enumerate(json_scripts):
            script_info = {
                "script_number": i + 1,
                "has_content": script.string is not None,
                "content_preview": script.string[:200] if script.string else None
            }
            debug_info["json_scripts_content"].append(script_info)
        
        return debug_info
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }

def is_recipe_complete(recipe: Recipe) -> bool:
    """Check if we extracted a complete, usable recipe"""
    return (
        recipe.title != "Untitled Recipe" and
        recipe.title != "Could not parse recipe" and
        len(recipe.ingredients) >= 3 and  # At least 3 ingredients
        len(recipe.instructions) >= 2     # At least 2 steps
    )

@app.post("/parse-recipe", response_model=Recipe)
def parse_recipe_structured(recipe_url: RecipeURL):
    """
    Parse a recipe URL and try to extract structured data first
    This teaches us about JSON-LD and microdata formats
    """
    try:
        # Fetch the webpage
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        print(f"Fetching URL: {recipe_url.url}")
        response = requests.get(str(recipe_url.url), headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        print("HTML parsed successfully")
        
        # Step 1: Try to find JSON-LD structured data
        print("Looking for JSON-LD script tags...")
        json_scripts = soup.find_all('script', type='application/ld+json')
        print(f"Found {len(json_scripts)} JSON-LD script tags")
        
        for i, script in enumerate(json_scripts):
            try:
                print(f"Processing JSON-LD script {i+1}")
                
                # Check if script has content
                if script.string is None:
                    print(f"Script {i+1} has no content, skipping")
                    continue
                
                print(f"Script {i+1} content preview: {script.string[:100]}...")
                
                # Try to parse JSON
                print(f"Attempting to parse JSON from script {i+1}")
                data = json.loads(script.string)
                print(f"JSON parsed successfully for script {i+1}")
                
                # Handle both single objects and arrays
                print(f"Data type: {type(data)}")
                items = [data] if isinstance(data, dict) else data
                print(f"Processing {len(items)} items")
                
                for j, item in enumerate(items):
                    print(f"Checking item {j+1}: @type = {item.get('@type')}")
                    
                    # Improved recipe detection to handle arrays
                    at_type = item.get('@type')
                    is_recipe = False
                    
                    if at_type == 'Recipe':
                        # Simple string match
                        is_recipe = True
                        print(f"  Found Recipe (string match)")
                    elif isinstance(at_type, list) and 'Recipe' in at_type:
                        # Array contains 'Recipe'
                        is_recipe = True
                        print(f"  Found Recipe (in array: {at_type})")
                    elif 'Recipe' in str(at_type):
                        # Fallback: Recipe appears in string representation
                        is_recipe = True
                        print(f"  Found Recipe (string contains: {str(at_type)})")
                    
                    if is_recipe:
                        print("✅ Recipe detected! Processing...")
                        return parse_structured_recipe(item, found_structured_data=True)
                    else:
                        print(f"  ❌ Not a recipe: {at_type}")
                        
            except json.JSONDecodeError as e:
                print(f"JSON decode error in script {i+1}: {e}")
                continue
            except Exception as e:
                print(f"Error processing script {i+1}: {e}")
                print(f"Exception type: {type(e)}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
                continue
        
        # Step 2: If no structured data, try basic HTML parsing
        print("Finished checking JSON-LD scripts, no recipe found")
        print("Starting HTML parsing fallback")
        return parse_html_recipe(soup, found_structured_data=False)
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Parsing error: {str(e)}")

def parse_structured_recipe(recipe_data: dict, found_structured_data: bool) -> Recipe:
    """
    Parse recipe from JSON-LD structured data
    This shows how to handle inconsistent data formats
    """
    def extract_text(item):
        """Helper function to extract text from various formats"""
        if isinstance(item, str):
            return item
        elif isinstance(item, dict):
            return item.get('text', str(item))
        elif isinstance(item, list):
            return [extract_text(i) for i in item]
        return str(item)
    
    # Extract ingredients
    ingredients = []
    if 'recipeIngredient' in recipe_data:
        raw_ingredients = recipe_data['recipeIngredient']
        ingredients = [extract_text(ing) for ing in raw_ingredients]
    
    # Extract instructions
    instructions = []
    if 'recipeInstructions' in recipe_data:
        for instruction in recipe_data['recipeInstructions']:
            if isinstance(instruction, dict):
                text = instruction.get('text', instruction.get('name', ''))
            else:
                text = str(instruction)
            if text:
                instructions.append(text)
    
    return Recipe(
        title=recipe_data.get('name', 'Untitled Recipe'),
        ingredients=ingredients,
        instructions=instructions,
        prep_time=recipe_data.get('prepTime', ''),
        cook_time=recipe_data.get('cookTime', ''),
        servings=str(recipe_data.get('recipeYield', '')),
        found_structured_data=found_structured_data
    )

def parse_html_recipe(soup: BeautifulSoup, found_structured_data: bool) -> Recipe:
    """
    Fallback HTML parsing when structured data isn't available
    This teaches us about CSS selectors and HTML parsing strategies
    """
    try:
        # Try to find title
        title = "Untitled Recipe"
        title_selectors = ['h1', '.recipe-title', '.entry-title', '[class*="title"]']
        
        print("Looking for title...")
        for selector in title_selectors:
            try:
                element = soup.select_one(selector)
                if element and element.get_text().strip():
                    title = element.get_text().strip()
                    print(f"Found title with selector '{selector}': {title}")
                    break
            except Exception as e:
                print(f"Error with title selector '{selector}': {e}")
                continue
        
        # Try to find ingredients
        ingredients = []
        ingredient_selectors = [
            '.recipe-ingredient', 
            '.ingredient', 
            '[class*="ingredient"]',
            'li[class*="ingredient"]'
        ]
        
        print("Looking for ingredients...")
        for selector in ingredient_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    ingredients = [el.get_text().strip() for el in elements if el.get_text().strip()]
                    if ingredients:  # Only break if we actually found ingredients
                        print(f"Found {len(ingredients)} ingredients with selector '{selector}'")
                        break
            except Exception as e:
                print(f"Error with ingredient selector '{selector}': {e}")
                continue
        
        # Try to find instructions
        instructions = []
        instruction_selectors = [
            '.recipe-instruction', 
            '.instruction', 
            '.method',
            '[class*="instruction"]',
            'ol li', 
            'ul li'
        ]
        
        print("Looking for instructions...")
        for selector in instruction_selectors:
            try:
                elements = soup.select(selector)
                if elements and len(elements) > 2:  # Probably instructions if there are several
                    instructions = [el.get_text().strip() for el in elements if el.get_text().strip()]
                    if instructions:  # Only break if we actually found instructions
                        print(f"Found {len(instructions)} instructions with selector '{selector}'")
                        break
            except Exception as e:
                print(f"Error with instruction selector '{selector}': {e}")
                continue
        
        print(f"Final result - Title: '{title}', Ingredients: {len(ingredients)}, Instructions: {len(instructions)}")
        
        return Recipe(
            title=title,
            ingredients=ingredients,
            instructions=instructions,
            found_structured_data=found_structured_data
        )
        
    except Exception as e:
        print(f"Error in parse_html_recipe: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        # Return a basic recipe even if parsing fails
        return Recipe(
            title="Could not parse recipe",
            ingredients=["Unable to extract ingredients"],
            instructions=["Unable to extract instructions"],
            found_structured_data=found_structured_data
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
