from typing import Optional, List, Dict, Any
import extruct
from app.models import Recipe
from .base import BaseParser
from ..processors.recipe_converter import RecipeConverter

class ExtructParser(BaseParser):
    """Parser using extruct library for structured data extraction"""
    
    @property
    def name(self) -> str:
        return "extruct"
    
    def can_parse(self, url: str) -> bool:
        """extruct can attempt to parse any URL"""
        return True
    
    def parse(self, url: str, html_content: str = None, **kwargs) -> Optional[Recipe]:
        """Parse recipe using extruct for structured data"""
        if not html_content:
            raise ValueError("ExtructParser requires html_content parameter")
        
        try:
            # Extract all structured data formats
            data = extruct.extract(
                html_content, 
                base_url=url,
                syntaxes=['json-ld', 'microdata', 'rdfa']
            )
            
            print(f"extruct found: {len(data.get('json-ld', []))} JSON-LD items, "
                  f"{len(data.get('microdata', []))} microdata items")
            
            # Find recipes in the extracted data
            recipes = self._find_all_recipes(data)
            
            if recipes:
                print(f"Found {len(recipes)} recipe(s) in structured data")
                return self._select_best_recipe(recipes)
            
            return None
            
        except Exception as e:
            print(f"extruct failed: {e}")
            return None
    
    def _find_all_recipes(self, structured_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find all recipe objects in extruct data"""
        recipes = []
        
        # Look in JSON-LD data
        for json_ld_item in structured_data.get('json-ld', []):
            recipes.extend(self._find_recipes_recursive(json_ld_item))
        
        # Look in microdata
        for microdata_item in structured_data.get('microdata', []):
            if 'Recipe' in str(microdata_item.get('type', '')):
                recipes.append(microdata_item)
        
        # Look in RDFa data  
        for rdfa_item in structured_data.get('rdfa', []):
            recipes.extend(self._find_recipes_recursive(rdfa_item))
        
        return recipes
    
    def _find_recipes_recursive(self, obj: Any) -> List[Dict[str, Any]]:
        """Recursively find Recipe objects in JSON-LD data"""
        recipes = []
        
        def traverse(data):
            if isinstance(data, dict):
                at_type = data.get('@type')
                if at_type:
                    # Check for Recipe type
                    if (at_type == 'Recipe' or 
                        (isinstance(at_type, list) and 'Recipe' in at_type) or
                        'Recipe' in str(at_type)):
                        recipes.append(data)
                
                # Handle @graph structures
                if '@graph' in data:
                    for item in data['@graph']:
                        traverse(item)
                
                # Traverse nested objects
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        traverse(value)
                        
            elif isinstance(data, list):
                for item in data:
                    traverse(item)
        
        traverse(obj)
        return recipes
    
    def _select_best_recipe(self, recipes: List[Dict[str, Any]]) -> Optional[Recipe]:
        """Select the best recipe from candidates"""
        
        # Try to find a complete recipe first
        for recipe_data in recipes:
            recipe = RecipeConverter.convert_structured_data_to_recipe(recipe_data)
            if RecipeConverter.is_complete_recipe(recipe):
                print(f"✅ Found complete recipe: {recipe.title}")
                return recipe
        
        # If no complete recipe, return the best "good enough" one
        for recipe_data in recipes:
            recipe = RecipeConverter.convert_structured_data_to_recipe(recipe_data)
            if RecipeConverter.is_good_enough_recipe(recipe):
                print(f"✅ Found good enough recipe: {recipe.title}")
                return recipe
        
        # If nothing is good enough, return the first one anyway
        if recipes:
            recipe = RecipeConverter.convert_structured_data_to_recipe(recipes[0])
            print(f"⚠️ Returning incomplete recipe: {recipe.title}")
            return recipe
        
        return None
