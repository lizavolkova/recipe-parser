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
                recipe = service._ensure_image_and_source(recipe, og_image, url)
                print("✅ recipe-scrapers successful!")
                return recipe
            
            # STEP 2: Try extruct
            print("🔍 Step 2: Trying extruct...")
            recipe = service.extruct_parser.parse(url, html_content=response.text)
            if recipe:
                recipe = service._ensure_image_and_source(recipe, og_image, url)
                
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
                ai_recipe = service._ensure_image_and_source(ai_recipe, og_image, url)
                
                if RecipeConverter.is_complete_recipe(ai_recipe):
                    print("✅ AI successful!")
                    return ai_recipe
                elif RecipeConverter.is_good_enough_recipe(ai_recipe):
                    print("✅ AI good enough!")
                    return ai_recipe
            
            # Return best attempt with og:image and source
            best_recipe = recipe or ai_recipe
            if best_recipe:
                best_recipe = service._ensure_image_and_source(best_recipe, og_image, url)
                print(f"📝 Returning best partial result: {best_recipe.title}")
                return best_recipe
            
            # Last resort - return failure with image and source
            fallback_source = service._extract_source_from_url(url)
            return Recipe(
                title="Unable to parse recipe",
                description="Could not extract recipe data using any method",
                image=og_image,  # At least return the image
                source=fallback_source,  # At least return the source
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
    
    def _ensure_image_and_source(self, recipe: Recipe, fallback_image: Optional[str], url: str) -> Recipe:
        """Ensure recipe has an image and source, using fallbacks if needed"""
        # Ensure image
        if not recipe.image and fallback_image:
            recipe.image = fallback_image
            print("✅ Used og:image fallback")
        
        # Ensure source - extract from URL if not found
        if not recipe.source:
            recipe.source = self._extract_source_from_url(url)
            if recipe.source:
                print(f"✅ Used URL-based source: {recipe.source}")
        
        return recipe
    
    def _extract_source_from_url(self, url: str) -> Optional[str]:
        """Extract source name from URL as fallback"""
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Manual mapping for common recipe sites
            domain_mapping = {
                'loveandlemons.com': 'Love and Lemons',
                'asianinspirations.com.au': 'Asian Inspirations',
                'allrecipes.com': 'Allrecipes',
                'foodnetwork.com': 'Food Network',
                'tasteofhome.com': 'Taste of Home',
                'epicurious.com': 'Epicurious',
                'simplyrecipes.com': 'Simply Recipes',
                'seriouseats.com': 'Serious Eats',
                'buzzfeed.com': 'BuzzFeed',
                'delish.com': 'Delish',
                'foodandwine.com': 'Food & Wine',
                'bonappetit.com': 'Bon Appétit',
            }
            
            if domain in domain_mapping:
                return domain_mapping[domain]
            
            # Generic conversion: remove .com/.org/etc and make readable
            domain_parts = domain.split('.')
            if domain_parts:
                base_name = domain_parts[0]
                # Split on common separators and capitalize
                words = base_name.replace('-', ' ').replace('_', ' ').split()
                return ' '.join(word.capitalize() for word in words)
            
        except Exception:
            pass
        
        return None
    
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
