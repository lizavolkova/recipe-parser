import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException
from typing import Optional

from app.config import settings
from app.models import Recipe, DebugInfo
from .parsers import RecipeScrapersParser, ExtructParser, parse_with_ai
from .processors import ImageExtractor, RecipeConverter

class RecipeService:
    """Main recipe parsing service - orchestrates different parsing strategies"""
    
    def __init__(self):
        self.recipe_scrapers_parser = RecipeScrapersParser()
        self.extruct_parser = ExtructParser()
    
    @staticmethod
    async def parse_recipe_hybrid(url: str) -> Recipe:
        """Parse recipe using multiple strategies with image-focused approach"""
        service = RecipeService()
        
        try:
            print(f"🔍 Parsing {url} with modular approach...")
            
            # Fetch page once and extract og:image immediately
            response, soup = service._fetch_page(url)
            og_image = ImageExtractor.extract_og_image(soup)
            print(f"🖼️ og:image found: {og_image}")
            
            # STEP 1: Try recipe-scrapers
            print("🔍 Step 1: Trying recipe-scrapers...")
            recipe = service.recipe_scrapers_parser.parse(url)
            if recipe and RecipeConverter.is_complete_recipe(recipe):
                recipe = service._ensure_image(recipe, og_image)
                print("✅ recipe-scrapers successful!")
                return recipe
            
            # STEP 2: Try extruct
            print("🔍 Step 2: Trying extruct...")
            recipe = service.extruct_parser.parse(url, html_content=response.text)
            if recipe:
                recipe = service._ensure_image(recipe, og_image)
                
                if RecipeConverter.is_complete_recipe(recipe):
                    print("✅ extruct successful!")
                    return recipe
                elif RecipeConverter.is_good_enough_recipe(recipe):
                    print("✅ extruct good enough!")
                    return recipe
                else:
                    print("⚠️ extruct data poor quality, trying AI...")
                    extruct_recipe = recipe  # Save for potential return later
            
            # STEP 3: AI fallback
            print("🔍 Step 3: Using AI...")
            ai_recipe = await parse_with_ai(soup, url)
            if ai_recipe:
                ai_recipe = service._ensure_image(ai_recipe, og_image)
                
                if RecipeConverter.is_complete_recipe(ai_recipe):
                    print("✅ AI successful!")
                    return ai_recipe
                elif RecipeConverter.is_good_enough_recipe(ai_recipe):
                    print("✅ AI good enough!")
                    return ai_recipe
            
            # Return best attempt with og:image
            best_recipe = recipe or ai_recipe
            if best_recipe:
                best_recipe = service._ensure_image(best_recipe, og_image)
                print(f"📝 Returning best partial result: {best_recipe.title}")
                return best_recipe
            
            # Last resort - return failure with image
            return Recipe(
                title="Unable to parse recipe",
                description="Could not extract recipe data using any method",
                image=og_image,  # At least return the image
                ingredients=["Could not extract ingredients"],
                instructions=["Could not extract instructions"],
                found_structured_data=False,
                used_ai=False
            )
                
        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=f"Parsing error: {str(e)}")
    
    def _fetch_page(self, url: str):
        """Fetch webpage content"""
        headers = {'User-Agent': settings.USER_AGENT}
        response = requests.get(url, headers=headers, timeout=settings.REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return response, soup
    
    def _ensure_image(self, recipe: Recipe, fallback_image: Optional[str]) -> Recipe:
        """Ensure recipe has an image, using fallback if needed"""
        if not recipe.image and fallback_image:
            recipe.image = fallback_image
            print("✅ Used og:image fallback")
        return recipe
    
    @staticmethod
    def debug_recipe(url: str) -> DebugInfo:
        """Debug endpoint with image info"""
        try:
            service = RecipeService()
            response, soup = service._fetch_page(url)
            og_image = ImageExtractor.extract_og_image(soup)
            
            json_scripts = soup.find_all('script', type='application/ld+json')
            json_scripts_content = []
            
            for i, script in enumerate(json_scripts):
                script_info = {
                    "script_number": i + 1,
                    "has_content": script.string is not None,
                    "content_preview": script.string[:200] if script.string else None
                }
                if i == 0:  # Add image info to first script
                    script_info["og_image_found"] = og_image
                json_scripts_content.append(script_info)
            
            return DebugInfo(
                status="success",
                html_length=len(response.content),
                json_scripts_found=len(json_scripts),
                json_scripts_content=json_scripts_content,
                ai_available=settings.OPENAI_API_KEY != ""
            )
            
        except Exception as e:
            return DebugInfo(
                status="error",
                error=str(e),
                error_type=type(e).__name__
            )
