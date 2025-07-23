import json
from bs4 import BeautifulSoup
from typing import Optional
from app.models import Recipe
from app.utils.helpers import extract_text

def parse_structured_data(soup: BeautifulSoup) -> Optional[Recipe]:
    """
    Try to extract recipe from JSON-LD structured data
    Returns Recipe object if found, None otherwise
    """
    print("🔍 Looking for structured data...")
    
    json_scripts = soup.find_all('script', type='application/ld+json')
    print(f"Found {len(json_scripts)} JSON-LD script tags")
    
    for i, script in enumerate(json_scripts):
        try:
            print(f"Processing JSON-LD script {i+1}")
            
            if script.string is None:
                print(f"Script {i+1} has no content, skipping")
                continue
            
            print(f"Script {i+1} content preview: {script.string[:200]}...")
            
            data = json.loads(script.string)
            print(f"Script {i+1}: JSON parsed successfully")
            
            # Handle @graph format (common in WordPress sites)
            if isinstance(data, dict) and '@graph' in data:
                print("Found @graph structure, extracting items")
                items = data['@graph']
            elif isinstance(data, dict):
                items = [data]
            elif isinstance(data, list):
                items = data
            else:
                print(f"Unknown data structure: {type(data)}")
                continue
            
            print(f"Processing {len(items)} items from script {i+1}")
            
            for j, item in enumerate(items):
                if not isinstance(item, dict):
                    print(f"Item {j+1} is not a dict, skipping: {type(item)}")
                    continue
                    
                at_type = item.get('@type')
                print(f"Checking item {j+1}: @type = {at_type}")
                
                # Log some key fields to help debug
                has_recipe_ingredient = 'recipeIngredient' in item
                has_recipe_instructions = 'recipeInstructions' in item
                has_recipe_category = 'recipeCategory' in item
                has_keywords = 'keywords' in item
                
                print(f"  Item {j+1} fields: recipeIngredient={has_recipe_ingredient}, "
                      f"recipeInstructions={has_recipe_instructions}, "
                      f"recipeCategory={has_recipe_category}, keywords={has_keywords}")
                
                if _is_recipe_item(item):
                    print("✅ Found recipe in structured data!")
                    recipe = _parse_recipe_item(item)
                    print(f"Parsed recipe: {recipe.title}")
                    return recipe
                else:
                    print(f"Item {j+1} is not a recipe")
                        
        except json.JSONDecodeError as e:
            print(f"JSON decode error in script {i+1}: {e}")
            print(f"Script content: {script.string[:500]}...")
            continue
        except Exception as e:
            print(f"Error processing script {i+1}: {e}")
            print(f"Exception type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            continue
    
    print("❌ No recipe found in structured data")
    return None

def _is_recipe_item(item: dict) -> bool:
    """Check if a JSON-LD item represents a recipe"""
    at_type = item.get('@type')
    
    # Prioritize explicit Recipe types
    if at_type == 'Recipe':
        print(f"Found explicit Recipe type")
        return True
    elif isinstance(at_type, list) and 'Recipe' in at_type:
        print(f"Found Recipe in type array: {at_type}")
        return True
    
    # Be more careful about embedded recipe data
    # Only consider it a recipe if it has the core recipe fields AND @type suggests it could be a recipe
    if str(at_type) in ['Article', 'BlogPosting', 'WebPage']:
        if _contains_recipe_data(item):
            # Check if this Article/BlogPosting actually contains recipe fields
            # vs just mentions of recipes
            core_recipe_fields = ['recipeIngredient', 'recipeInstructions']
            has_core_fields = sum(1 for field in core_recipe_fields if field in item and item[field])
            
            if has_core_fields >= 2:
                print(f"Found recipe data embedded in {at_type} object with {has_core_fields} core fields")
                return True
            else:
                print(f"Article/BlogPosting has some recipe fields but missing core recipe data")
                return False
    
    # Fallback for other types that might be recipes
    if 'Recipe' in str(at_type):
        print(f"Found Recipe mention in type: {at_type}")
        return True
    
    return False

def _contains_recipe_data(item: dict) -> bool:
    """Check if an item contains recipe-like data"""
    # Look for recipe-specific fields
    recipe_fields = [
        'recipeIngredient', 'recipeInstructions', 'ingredients', 'instructions',
        'cookTime', 'prepTime', 'recipeYield', 'nutrition'
    ]
    
    # If it has at least 2 recipe fields, it's probably a recipe
    found_fields = sum(1 for field in recipe_fields if field in item and item[field])
    
    if found_fields >= 2:
        print(f"Item has {found_fields} recipe fields: {[f for f in recipe_fields if f in item and item[f]]}")
        return True
    
    # Check nested objects (sometimes recipe data is nested)
    for key, value in item.items():
        if isinstance(value, dict):
            if any(field in value for field in recipe_fields):
                print(f"Found recipe fields in nested object '{key}'")
                return True
        elif isinstance(value, list):
            for nested_item in value:
                if isinstance(nested_item, dict) and any(field in nested_item for field in recipe_fields):
                    print(f"Found recipe fields in nested list item under '{key}'")
                    return True
    
    return False

def _parse_recipe_item(recipe_data: dict) -> Recipe:
    """Parse a recipe item from JSON-LD data"""
    
    # Try multiple possible field names
    def get_field(data, possible_keys, default=None):
        """Try multiple field names and return first found"""
        for key in possible_keys:
            if key in data and data[key]:
                return data[key]
        return default
    
    # Extract title with multiple possible names
    title = get_field(recipe_data, ['name', 'headline', 'title'], 'Untitled Recipe')
    print(f"Structured: Found title: {title}")
    
    # Extract description
    description = get_field(recipe_data, ['description', 'summary'])
    print(f"Structured: Found description: {description[:100] if description else None}...")
    
    # Extract ingredients
    ingredients = []
    raw_ingredients = get_field(recipe_data, ['recipeIngredient', 'ingredients'], [])
    if raw_ingredients:
        ingredients = [extract_text(ing) for ing in raw_ingredients]
    print(f"Structured: Found {len(ingredients)} ingredients")
    if ingredients:
        print(f"Structured: First few ingredients: {ingredients[:3]}")
    
    # Extract instructions with enhanced parsing
    instructions = []
    raw_instructions = get_field(recipe_data, ['recipeInstructions', 'instructions', 'method'], [])
    if raw_instructions:
        instructions = _parse_instructions(raw_instructions)
    
    print(f"Structured: Found {len(instructions)} instructions")
    if instructions:
        print(f"Structured: First instruction: {instructions[0][:100]}...")
    
    # Extract timing and servings
    prep_time = get_field(recipe_data, ['prepTime', 'preparationTime'])
    cook_time = get_field(recipe_data, ['cookTime', 'cookingTime'])
    servings = get_field(recipe_data, ['recipeYield', 'yield', 'servings'])
    
    # Extract new metadata fields
    cuisine = get_field(recipe_data, ['recipeCuisine', 'cuisine'])
    category = get_field(recipe_data, ['recipeCategory', 'category', 'courseType', 'mealType'])
    
    # Extract keywords (can be string or array)
    keywords = []
    raw_keywords = get_field(recipe_data, ['keywords', 'recipeKeyword'])
    if raw_keywords:
        if isinstance(raw_keywords, str):
            # Split comma-separated keywords
            keywords = [k.strip() for k in raw_keywords.split(',') if k.strip()]
        elif isinstance(raw_keywords, list):
            keywords = [str(k).strip() for k in raw_keywords if str(k).strip()]
    
    print(f"Structured: cuisine={cuisine}, category={category}")
    print(f"Structured: keywords={keywords}")
    print(f"Structured: prep_time={prep_time}, cook_time={cook_time}, servings={servings}")
    
    # Convert servings to string if it's a number or list
    if servings is not None:
        if isinstance(servings, list):
            servings = str(servings[0]) if servings else None
        else:
            servings = str(servings)
    
    recipe = Recipe(
        title=title,
        description=description,
        ingredients=ingredients,
        instructions=instructions,
        prep_time=prep_time,
        cook_time=cook_time,
        servings=servings,
        cuisine=cuisine,
        category=category,
        keywords=keywords,
        found_structured_data=True,
        used_ai=False
    )
    
    print(f"Structured: Final recipe - Title: '{recipe.title}', "
          f"Ingredients: {len(recipe.ingredients)}, Instructions: {len(recipe.instructions)}")
    
    return recipe

def _parse_instructions(raw_instructions) -> list:
    """Enhanced instruction parsing to handle various formats"""
    instructions = []
    
    for instruction in raw_instructions:
        if isinstance(instruction, dict):
            # Handle HowToStep format
            if instruction.get('@type') == 'HowToStep':
                text = instruction.get('text', instruction.get('name', ''))
            else:
                text = instruction.get('text', instruction.get('name', ''))
        elif isinstance(instruction, str):
            text = instruction
        else:
            text = str(instruction)
        
        if text:
            # Check if this is a concatenated string with numbered steps
            if _looks_like_concatenated_steps(text):
                # Split on numbered patterns like "1. " "2. " etc.
                split_instructions = _split_numbered_instructions(text)
                instructions.extend(split_instructions)
                print(f"Split concatenated instruction into {len(split_instructions)} steps")
            else:
                instructions.append(text)
    
    return instructions

def _looks_like_concatenated_steps(text: str) -> bool:
    """Check if text looks like multiple numbered steps concatenated together"""
    import re
    
    # Look for patterns like "1. Something 2. Something else"
    pattern = r'\d+\.\s+.*?\d+\.\s+'
    matches = re.findall(pattern, text)
    
    # If we find multiple numbered patterns, it's likely concatenated
    return len(matches) > 0 or text.count('. ') > 2

def _split_numbered_instructions(text: str) -> list:
    """Split concatenated numbered instructions into separate steps"""
    import re
    
    # Split on patterns like "1. ", "2. ", etc.
    # But keep the numbers with their instructions
    parts = re.split(r'(\d+\.\s+)', text)
    
    instructions = []
    current_instruction = ""
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        # If this part looks like a step number
        if re.match(r'^\d+\.\s*$', part):
            # Save the previous instruction if we have one
            if current_instruction:
                instructions.append(current_instruction.strip())
            current_instruction = part
        else:
            # Add this text to the current instruction
            current_instruction += part
    
    # Don't forget the last instruction
    if current_instruction:
        instructions.append(current_instruction.strip())
    
    # Filter out very short or empty instructions
    instructions = [inst for inst in instructions if len(inst.strip()) > 10]
    
    return instructions
