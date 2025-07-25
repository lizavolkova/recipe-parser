from typing import Optional, List, Dict, Any
from app.models import Recipe
from .image_extractor import ImageExtractor
from .instruction_processor import InstructionProcessor

class RecipeConverter:
    """Handles conversion of various data formats to Recipe objects"""
    
    @staticmethod
    def convert_structured_data_to_recipe(recipe_data: Dict[str, Any]) -> Recipe:
        """Convert structured data (JSON-LD or microdata) to Recipe object"""
        
        # Handle microdata format vs JSON-LD format
        if 'properties' in recipe_data and 'type' in recipe_data:
            print("Converting microdata format")
            data = recipe_data['properties']
        else:
            print("Converting JSON-LD format")
            data = recipe_data
        
        # Extract basic fields with array handling
        title = RecipeConverter._get_value(data, 'name') or 'Untitled Recipe'
        description = RecipeConverter._get_value(data, 'description')
        
        # Extract source information
        source = RecipeConverter._extract_source(data)
        
        # Extract and process ingredients
        ingredients = data.get('recipeIngredient', [])
        if not isinstance(ingredients, list):
            ingredients = []
        ingredients = RecipeConverter._clean_ingredients(ingredients)
        
        # Extract and process instructions
        raw_instructions = data.get('recipeInstructions', [])
        instructions = InstructionProcessor.process_instructions(raw_instructions)
        
        # Extract image
        image = ImageExtractor.extract_from_structured_data(data.get('image'))
        
        # Extract timing and serving info
        prep_time = RecipeConverter._get_value(data, 'prepTime')
        cook_time = RecipeConverter._get_value(data, 'cookTime')
        total_time = RecipeConverter._get_value(data, 'totalTime')
        servings = RecipeConverter._get_value(data, 'recipeYield')
        
        # Extract categorization
        cuisine = RecipeConverter._get_value(data, 'recipeCuisine')
        category = RecipeConverter._get_value(data, 'recipeCategory')
        keywords = RecipeConverter._extract_keywords(data.get('keywords', []))
        
        print(f"Converted recipe: {title} with {len(ingredients)} ingredients, {len(instructions)} instructions")
        print(f"  - source: {source}")
        
        return Recipe(
            title=str(title),
            description=str(description) if description else None,
            image=image,
            source=source,
            ingredients=ingredients,
            instructions=instructions,
            prep_time=str(prep_time) if prep_time else None,
            cook_time=str(cook_time) if cook_time else None,
            servings=str(servings) if servings else None,
            cuisine=str(cuisine) if cuisine else None,
            category=str(category) if category else None,
            keywords=keywords,
            found_structured_data=True,
            used_ai=False
        )
    
    @staticmethod
    def _extract_source(data: Dict[str, Any]) -> Optional[str]:
        """Extract source organization from structured data"""
        
        # Try publisher first (most reliable for organization)
        publisher = data.get('publisher')
        if publisher:
            if isinstance(publisher, dict):
                name = publisher.get('name')
                if name:
                    return str(name)
            elif isinstance(publisher, str):
                return publisher
        
        # Try author (might be organization or person)
        author = data.get('author')
        if author:
            if isinstance(author, dict):
                name = author.get('name')
                if name and not RecipeConverter._looks_like_person_name(str(name)):
                    return str(name)
            elif isinstance(author, str) and not RecipeConverter._looks_like_person_name(author):
                return author
        
        # Try mainEntityOfPage for blog/site name
        main_entity = data.get('mainEntityOfPage')
        if main_entity and isinstance(main_entity, dict):
            site_name = main_entity.get('name')
            if site_name:
                return str(site_name)
        
        return None
    
    @staticmethod
    def _looks_like_person_name(name: str) -> bool:
        """Check if name looks like a person vs organization"""
        name_lower = name.lower().strip()
        
        # Skip if it contains person indicators
        person_indicators = [
            'by ', 'recipe by', 'chef ', 'author:', 'cook:', 'created by'
        ]
        if any(indicator in name_lower for indicator in person_indicators):
            return True
        
        # Skip if it looks like a person's name (First Last pattern)
        words = name.split()
        if len(words) == 2 and all(len(word) > 1 and word[0].isupper() for word in words):
            # Additional check: avoid common blog/organization patterns
            org_words = ['kitchen', 'recipes', 'cooking', 'food', 'blog', 'eats', 'taste', 'flavor']
            if not any(org_word in name_lower for org_word in org_words):
                return True  # Likely "First Last" person name
        
        return False
    
    @staticmethod
    def _get_value(data: Dict[str, Any], field_name: str) -> Optional[str]:
        """Extract value from data, handling arrays"""
        value = data.get(field_name)
        if isinstance(value, list) and value:
            return value[0]
        return value
    
    @staticmethod
    def _clean_ingredients(ingredients: List[Any]) -> List[str]:
        """Clean up ingredients list"""
        cleaned = []
        for ing in ingredients:
            if isinstance(ing, dict):
                # Sometimes ingredients are objects with 'name' or 'text' fields
                ing_text = ing.get('name', ing.get('text', str(ing)))
            else:
                ing_text = str(ing)
            
            if ing_text and len(ing_text.strip()) > 1:
                cleaned.append(ing_text.strip())
        
        return cleaned
    
    @staticmethod
    def _extract_keywords(keywords_data) -> List[str]:
        """Extract and clean keywords"""
        if isinstance(keywords_data, str):
            return [k.strip() for k in keywords_data.split(',') if k.strip()]
        elif isinstance(keywords_data, list):
            cleaned = []
            for keyword in keywords_data:
                if isinstance(keyword, str) and keyword.strip():
                    cleaned.append(keyword.strip())
            return cleaned
        return []
    
    @staticmethod
    def is_complete_recipe(recipe: Recipe) -> bool:
        """Check if recipe has enough data to be considered complete"""
        return (
            recipe and
            recipe.title not in ["Untitled Recipe", "Could not parse recipe"] and
            len(recipe.ingredients) >= 3 and
            len(recipe.instructions) >= 1
        )
    
    @staticmethod
    def is_good_enough_recipe(recipe: Recipe) -> bool:
        """Check if recipe has some useful data, even if not complete"""
        return (
            recipe and
            recipe.title not in ["Untitled Recipe", "Could not parse recipe"] and
            (len(recipe.ingredients) >= 2 or len(recipe.instructions) >= 1)
        )
