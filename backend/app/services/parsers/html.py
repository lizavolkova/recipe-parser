from bs4 import BeautifulSoup
from app.models import Recipe
from typing import Optional

def parse_html_recipe(soup: BeautifulSoup) -> Recipe:
    """
    Fallback HTML parsing when structured data isn't available
    """
    print("🔍 Trying HTML parsing...")
    
    try:
        title = _extract_title(soup)
        description = _extract_description(soup)
        ingredients = _extract_ingredients(soup)
        instructions = _extract_instructions(soup)
        cuisine, category, keywords = _extract_metadata(soup)
        
        # Ensure we always have valid strings/lists
        if not isinstance(title, str):
            title = "Untitled Recipe"
        if not isinstance(ingredients, list):
            ingredients = []
        if not isinstance(instructions, list):
            instructions = []
        if not isinstance(keywords, list):
            keywords = []
        
        print(f"HTML parsing results: title='{title}', description={bool(description)}, "
              f"ingredients={len(ingredients)}, instructions={len(instructions)}")
        print(f"HTML metadata: cuisine={cuisine}, category={category}, keywords={len(keywords)}")
        
        return Recipe(
            title=title,
            description=description,
            ingredients=ingredients,
            instructions=instructions,
            cuisine=cuisine,
            category=category,
            keywords=keywords,
            found_structured_data=False,
            used_ai=False
        )
        
    except Exception as e:
        print(f"Error in HTML recipe parsing: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return Recipe(
            title="Could not parse recipe",
            description=None,
            ingredients=["Unable to extract ingredients"],
            instructions=["Unable to extract instructions"],
            cuisine=None,
            category=None,
            keywords=[],
            found_structured_data=False,
            used_ai=False
        )

def _extract_title(soup: BeautifulSoup) -> str:
    """Extract recipe title from HTML"""
    title = "Untitled Recipe"
    title_selectors = [
        'h1.entry-title',           # Blog-specific
        'h1.recipe-title', 
        'h1',
        '.recipe-title',
        '.entry-title',
        '[class*="title"]'
    ]
    
    print("Looking for title...")
    for selector in title_selectors:
        try:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                found_title = element.get_text().strip()
                print(f"Found title with selector '{selector}': {found_title}")
                return found_title
        except Exception as e:
            print(f"Error with title selector '{selector}': {e}")
            continue
    
    print(f"No title found, using default: {title}")
    return title

def _extract_ingredients(soup: BeautifulSoup) -> list:
    """Extract ingredients from HTML"""
    ingredients = []
    ingredient_selectors = [
        '.recipe-card-ingredients li',   # More specific
        '.wp-block-recipe-card-ingredients li',
        '.recipe-ingredients li',
        '.ingredients li',
        '[class*="ingredient"] li',
        'ul[class*="ingredient"] li',
        '.recipe-ingredient', 
        '.ingredient', 
        '[class*="ingredient"]',
        'li[class*="ingredient"]',
        # Love and Lemons specific
        '.recipe-summary ul li',
        '.entry-content ul li'
    ]
    
    print("Looking for ingredients...")
    for selector in ingredient_selectors:
        try:
            elements = soup.select(selector)
            if elements:
                candidate_ingredients = []
                for el in elements:
                    text = el.get_text().strip()
                    if text and _is_likely_ingredient(text):
                        candidate_ingredients.append(text)
                
                if candidate_ingredients and len(candidate_ingredients) >= 3:
                    ingredients = candidate_ingredients
                    print(f"Found {len(ingredients)} ingredients with selector '{selector}'")
                    break
        except Exception as e:
            print(f"Error with ingredient selector '{selector}': {e}")
            continue
    
    if not ingredients:
        print("No ingredients found with any selector")
    
    return ingredients

def _extract_instructions(soup: BeautifulSoup) -> list:
    """Extract cooking instructions from HTML"""
    instructions = []
    instruction_selectors = [
        '.recipe-card-instructions li',
        '.wp-block-recipe-card-instructions li',
        '.recipe-instructions li',
        '.instructions ol li',
        '.recipe-method li',
        '[class*="instruction"] li',
        'ol[class*="instruction"] li',
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
            if elements:
                candidate_instructions = []
                for el in elements:
                    text = el.get_text().strip()
                    if _is_likely_instruction(text):
                        candidate_instructions.append(text)
                
                if candidate_instructions and len(candidate_instructions) >= 3:
                    instructions = candidate_instructions
                    print(f"Found {len(instructions)} instructions with selector '{selector}'")
                    break
        except Exception as e:
            print(f"Error with instruction selector '{selector}': {e}")
            continue
    
    return instructions

def _is_likely_ingredient(text: str) -> bool:
    """Filter out non-ingredient text"""
    text = text.strip().lower()
    
    # Skip if too short or too long
    if len(text) < 3 or len(text) > 200:
        return False
    
    # Skip obvious non-ingredients
    skip_phrases = [
        'recipe', 'print', 'save', 'share', 'ingredients', 
        'instructions', 'method', 'preparation', 'cook time',
        'prep time', 'servings', 'difficulty', 'course',
        'cuisine', 'author', 'published', 'updated', 'notes',
        'nutrition', 'calories', 'course', 'keyword'
    ]
    
    if any(phrase in text for phrase in skip_phrases):
        return False
    
    # Skip if it's just a single word (likely a label)
    if len(text.split()) == 1 and text not in ['eggs', 'flour', 'sugar', 'butter', 'salt']:
        return False
    
    # Ingredients usually have quantities/measurements
    ingredient_indicators = [
        'cup', 'cups', 'tablespoon', 'teaspoon', 'pound', 'ounce',
        'gram', 'kg', 'ml', 'liter', 'inch', 'clove', 'slice',
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
        'tsp', 'tbsp', 'lb', 'oz', '/', '-'
    ]
    
    return any(indicator in text for indicator in ingredient_indicators)

def _is_likely_instruction(text: str) -> bool:
    """Filter out non-instruction text"""
    text = text.strip()
    
    # Skip if too short
    if len(text) < 15:
        return False
    
    # Skip obvious non-instructions
    skip_phrases = [
        'instructions', 'pie crust', 'roasted pumpkin puree',
        'butterscotch sauce', 'pumpkin pie filling'
    ]
    
    if any(phrase.lower() in text.lower() for phrase in skip_phrases):
        return False
    
    # Instructions usually start with action words or numbers
    action_words = [
        'heat', 'mix', 'add', 'combine', 'stir', 'bake', 'cook',
        'place', 'remove', 'set', 'let', 'allow', 'serve',
        'preheat', 'whisk', 'fold', 'pour', 'spread', 'cover',
        'in', 'begin', 'cut', 'scoop', 'roll', 'grease',
        'switch', 'sprinkle', 'turn'
    ]
    
    first_word = text.split()[0].lower().rstrip('.,')
    
    # Check if starts with number (like "1. Heat oven...")
    if first_word[0].isdigit():
        return True
    
    # Check if starts with action word
    if first_word in action_words:
        return True
    
def _extract_description(soup: BeautifulSoup) -> Optional[str]:
    """Extract recipe description from HTML"""
    description_selectors = [
        '.recipe-description',
        '.recipe-summary',
        '.entry-summary', 
        '.post-excerpt',
        '.description',
        'meta[name="description"]',
        'meta[property="og:description"]',
        '.recipe-card-description',
        '.wp-block-recipe-card-summary'
    ]
    
    print("Looking for description...")
    for selector in description_selectors:
        try:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element and element.get('content'):
                    description = element.get('content').strip()
                    print(f"Found description in meta tag '{selector}': {description[:100]}...")
                    return description
            else:
                element = soup.select_one(selector)
                if element and element.get_text().strip():
                    description = element.get_text().strip()
                    print(f"Found description with selector '{selector}': {description[:100]}...")
                    return description
        except Exception as e:
            print(f"Error with description selector '{selector}': {e}")
            continue
    
    print("No description found")
    return None

def _extract_metadata(soup: BeautifulSoup) -> tuple:
    """Extract cuisine, category, and keywords from HTML"""
    
    # Extract cuisine
    cuisine = None
    cuisine_selectors = [
        '.recipe-cuisine',
        '.cuisine',
        '[class*="cuisine"]',
        'meta[property="recipe:cuisine"]'
    ]
    
    for selector in cuisine_selectors:
        try:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element and element.get('content'):
                    cuisine = element.get('content').strip()
                    break
            else:
                element = soup.select_one(selector)
                if element and element.get_text().strip():
                    cuisine = element.get_text().strip()
                    break
        except Exception:
            continue
    
    # Extract category
    category = None
    category_selectors = [
        '.recipe-category',
        '.category',
        '.course',
        '[class*="category"]',
        '[class*="course"]',
        'meta[property="recipe:category"]'
    ]
    
    for selector in category_selectors:
        try:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element and element.get('content'):
                    category = element.get('content').strip()
                    break
            else:
                element = soup.select_one(selector)
                if element and element.get_text().strip():
                    category = element.get_text().strip()
                    break
        except Exception:
            continue
    
    # Extract keywords from various sources
    keywords = []
    keyword_sources = [
        ('meta[name="keywords"]', 'content'),
        ('meta[property="article:tag"]', 'content'),
        ('.recipe-tags a', 'text'),
        ('.tags a', 'text'),
        ('.post-tags a', 'text'),
        ('[class*="tag"] a', 'text')
    ]
    
    for selector, attr in keyword_sources:
        try:
            if attr == 'content':
                element = soup.select_one(selector)
                if element and element.get('content'):
                    # Split comma-separated keywords
                    kw_text = element.get('content')
                    keywords.extend([k.strip() for k in kw_text.split(',') if k.strip()])
            else:  # text
                elements = soup.select(selector)
                for el in elements:
                    text = el.get_text().strip()
                    if text and text not in keywords:
                        keywords.append(text)
        except Exception:
            continue
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw.lower() not in seen:
            seen.add(kw.lower())
            unique_keywords.append(kw)
    
    # print(f"HTML metadata extracted: cuisine={cuisine}, category={category}, keywords={len(unique_keywords)}")
    print(f"HTML metadata extracted")

    return cuisine, category, unique_keywords
