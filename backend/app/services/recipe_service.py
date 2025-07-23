import extruct
import requests
from recipe_scrapers import scrape_me
from bs4 import BeautifulSoup
from fastapi import HTTPException
from typing import Optional

from app.config import settings
from app.models import Recipe, DebugInfo
from app.services.parsers.ai import parse_with_ai
from app.utils.helpers import extract_main_content

class RecipeService:
    """Simplified recipe service using mature libraries"""
    
    @staticmethod
    async def parse_recipe_hybrid(url: str) -> Recipe:
        """
        New hybrid approach: recipe-scrapers → extruct → AI fallback
        """
        try:
            print(f"🔍 Parsing {url} with library-first approach...")
            
            # Get the page content once and extract fallback image immediately
            headers = {'User-Agent': settings.USER_AGENT}
            response = requests.get(url, headers=headers, timeout=settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            fallback_image = RecipeService._extract_fallback_image(soup, url)
            print(f"🖼️ Fallback image found: {fallback_image}")
            
            # STEP 1: Try recipe-scrapers (handles 100+ sites automatically)
            print("🔍 Step 1: Trying recipe-scrapers...")
            recipe = RecipeService._try_recipe_scrapers(url)
            if recipe and RecipeService._is_complete(recipe):
                # Use fallback image if recipe-scrapers didn't find one
                if not recipe.image and fallback_image:
                    recipe.image = fallback_image
                    print(f"✅ Used fallback image for recipe-scrapers result")
                print("✅ recipe-scrapers successful!")
                return recipe
            else:
                print("⚠️ recipe-scrapers incomplete or failed, continuing...")
            
            # STEP 2: Try extruct for structured data extraction
            print("🔍 Step 2: Trying extruct for structured data...")
            recipe = RecipeService._try_extruct_with_content(response.text, url, fallback_image)
            if recipe and RecipeService._is_complete(recipe):
                print("✅ extruct successful!")
                return recipe
            else:
                print("⚠️ extruct incomplete or failed, trying AI...")
            
            # STEP 3: AI fallback (our existing code)
            print("🔍 Step 3: Using AI fallback...")
            recipe = await RecipeService._try_ai_fallback_with_content(soup, url, fallback_image)
            if recipe and RecipeService._is_complete(recipe):
                print("✅ AI parsing successful!")
                return recipe
            else:
                print("⚠️ AI parsing failed or incomplete")
            
            # STEP 4: Return best attempt or graceful failure
            print("📝 Returning best available result...")
            if recipe and recipe.title != "Could not parse recipe":
                return recipe
            else:
                return Recipe(
                    title="Unable to parse recipe",
                    description="Could not extract recipe data using any method",
                    image=fallback_image,  # At least return the image we found
                    ingredients=["Could not extract ingredients"],
                    instructions=["Could not extract instructions"],
                    found_structured_data=False,
                    used_ai=False
                )
                
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=f"Parsing error: {str(e)}")
    
    @staticmethod
    def _try_recipe_scrapers(url: str) -> Optional[Recipe]:
        """Try recipe-scrapers library first - handles most sites automatically"""
        try:
            scraper = scrape_me(url)
            
            # Extract basic required data
            title = scraper.title() or "Untitled Recipe"
            ingredients = scraper.ingredients() or []
            instructions = scraper.instructions_list() or []
            
            # Extract optional fields - handle missing data gracefully
            try:
                description = scraper.description()
            except (AttributeError, NotImplementedError, Exception):
                description = None
                
            try:
                image = scraper.image()
            except (AttributeError, NotImplementedError, Exception):
                image = None
                
            try:
                prep_time = scraper.prep_time()
            except (AttributeError, NotImplementedError, Exception):
                prep_time = None
                
            try:
                cook_time = scraper.cook_time()
            except (AttributeError, NotImplementedError, Exception):
                cook_time = None
                
            try:
                servings = scraper.yields()
            except (AttributeError, NotImplementedError, Exception):
                servings = None
            
            # These might not be implemented on all scrapers yet
            try:
                cuisine = scraper.cuisine()
            except (AttributeError, NotImplementedError, Exception):
                cuisine = None
                
            try:
                category = scraper.category()
            except (AttributeError, NotImplementedError, Exception):
                category = None
                
            try:
                keywords = scraper.keywords() or []
                if isinstance(keywords, str):
                    keywords = [k.strip() for k in keywords.split(',') if k.strip()]
            except (AttributeError, NotImplementedError, Exception):
                keywords = []
            
            print(f"recipe-scrapers extracted: {title}")
            print(f"  - {len(ingredients)} ingredients, {len(instructions)} instructions")
            print(f"  - image: {image}")
            print(f"  - cuisine: {cuisine}, category: {category}")
            print(f"  - keywords: {keywords}")
            
            return Recipe(
                title=title,
                description=description,
                image=image,
                ingredients=ingredients,
                instructions=instructions,
                prep_time=str(prep_time) if prep_time else None,
                cook_time=str(cook_time) if cook_time else None,
                servings=str(servings) if servings else None,
                cuisine=cuisine,
                category=category,
                keywords=keywords,
                found_structured_data=True,
                used_ai=False
            )
            
        except Exception as e:
            print(f"recipe-scrapers failed: {e}")
            return None
    
    @staticmethod
    def _try_extruct_with_content(html_content: str, url: str, fallback_image: Optional[str]) -> Optional[Recipe]:
        """Try extruct with pre-fetched content"""
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
            recipes = RecipeService._find_recipes_in_extruct_data(data)
            
            if recipes:
                print(f"Found {len(recipes)} recipe(s) in structured data")
                # Return the most complete recipe
                for recipe_data in recipes:
                    recipe = RecipeService._convert_to_recipe(recipe_data)
                    if RecipeService._is_complete(recipe):
                        # Always use fallback image if structured data doesn't have one
                        if not recipe.image and fallback_image:
                            recipe.image = fallback_image
                            print(f"✅ Used fallback image for extruct result")
                        return recipe
                
                # If none are complete, return the best one
                if recipes:
                    recipe = RecipeService._convert_to_recipe(recipes[0])
                    print(f"Returning incomplete but best recipe: {recipe.title}")
                    # Always use fallback image
                    if not recipe.image and fallback_image:
                        recipe.image = fallback_image
                        print(f"✅ Used fallback image for incomplete extruct result")
                    return recipe
            
            return None
            
        except Exception as e:
            print(f"extruct failed: {e}")
            return None
    
    @staticmethod
    async def _try_ai_fallback_with_content(soup: BeautifulSoup, url: str, fallback_image: Optional[str]) -> Optional[Recipe]:
        """Use AI parsing with pre-fetched content"""
        try:
            ai_recipe = await parse_with_ai(soup, url)
            
            # Always use fallback image if AI didn't find one
            if ai_recipe and not ai_recipe.image and fallback_image:
                ai_recipe.image = fallback_image
                print(f"✅ Used fallback image for AI result")
            
            return ai_recipe
            
        except Exception as e:
            print(f"AI fallback failed: {e}")
            return None
        """Try extruct for comprehensive structured data extraction"""
        try:
            headers = {'User-Agent': settings.USER_AGENT}
            response = requests.get(url, headers=headers, timeout=settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Extract all structured data formats
            data = extruct.extract(
                response.text, 
                base_url=url,
                syntaxes=['json-ld', 'microdata', 'rdfa']
            )
            
            print(f"extruct found: {len(data.get('json-ld', []))} JSON-LD items, "
                  f"{len(data.get('microdata', []))} microdata items")
            
            # Find recipes in the extracted data
            recipes = RecipeService._find_recipes_in_extruct_data(data)
            
            if recipes:
                print(f"Found {len(recipes)} recipe(s) in structured data")
                # Return the most complete recipe
                for recipe_data in recipes:
                    recipe = RecipeService._convert_extruct_to_recipe(recipe_data)
                    if RecipeService._is_complete(recipe):
                        # If no image found in structured data, try fallback
                        if not recipe.image:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            fallback_image = RecipeService._extract_fallback_image(soup, url)
                            if fallback_image:
                                print(f"Found fallback image: {fallback_image}")
                                recipe.image = fallback_image
                        return recipe
                
                # If none are complete, return the best one
                if recipes:
                    recipe = RecipeService._convert_extruct_to_recipe(recipes[0])
                    print(f"Returning incomplete but best recipe: {recipe.title}")
                    # Try fallback image for incomplete recipes too
                    if not recipe.image:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        fallback_image = RecipeService._extract_fallback_image(soup, url)
                        if fallback_image:
                            print(f"Found fallback image: {fallback_image}")
                            recipe.image = fallback_image
                    return recipe
            
            return None
            
        except Exception as e:
            print(f"extruct failed: {e}")
            return None
    
    @staticmethod
    def _find_recipes_in_extruct_data(structured_data: dict) -> list:
        """Find all Recipe objects in extruct-extracted data"""
        recipes = []
        
        # Check JSON-LD data
        for item in structured_data.get('json-ld', []):
            recipes.extend(RecipeService._find_recipes_recursive(item))
        
        # Check microdata
        for item in structured_data.get('microdata', []):
            if 'Recipe' in str(item.get('type', '')):
                recipes.append(item)
        
        return recipes
    
    @staticmethod
    def _find_recipes_recursive(obj) -> list:
        """Recursively find Recipe objects in JSON-LD data"""
        recipes = []
        
        def traverse(data):
            if isinstance(data, dict):
                at_type = data.get('@type')
                if at_type:
                    # More robust recipe detection
                    if (at_type == 'Recipe' or 
                        (isinstance(at_type, list) and 'Recipe' in at_type) or
                        'Recipe' in str(at_type)):
                        
                        print(f"Found recipe object: {data.get('name', 'Unnamed')}")
                        print(f"  @type: {at_type}")
                        print(f"  Available fields: {list(data.keys())}")
                        print(f"  Has ingredients: {'recipeIngredient' in data}")
                        print(f"  Has instructions: {'recipeInstructions' in data}")
                        
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
    
    @staticmethod
    def _convert_to_recipe(recipe_data: dict) -> Recipe:
        """Convert any recipe data format to Recipe object"""
        
        # Handle microdata format
        if 'properties' in recipe_data:
            data = recipe_data['properties']
        else:
            data = recipe_data
        
        # Extract fields, handling arrays
        def get_value(field_name):
            value = data.get(field_name)
            if isinstance(value, list) and value:
                return value[0]
            return value
        
        # Handle instructions with concatenation splitting
        instructions = []
        raw_instructions = data.get('recipeInstructions', [])
        
        print(f"🔧 NEW SERVICE: Processing instructions of type: {type(raw_instructions)}")
        
        if isinstance(raw_instructions, str):
            # Single concatenated string - split it intelligently
            print(f"🔧 Found concatenated string instruction, splitting...")
            instructions = RecipeService._split_concatenated_instructions(raw_instructions)
        elif isinstance(raw_instructions, list):
            for instr in raw_instructions:
                if isinstance(instr, dict):
                    text = instr.get('text', str(instr))
                else:
                    text = str(instr)
                
                if text and len(text.strip()) > 5:
                    # Check if this single instruction is actually concatenated
                    if RecipeService._looks_like_concatenated_steps(text):
                        print(f"🔧 Found concatenated instruction in list, splitting...")
                        split_steps = RecipeService._split_concatenated_instructions(text)
                        instructions.extend(split_steps)
                    else:
                        instructions.append(text)
        
        # Handle keywords
        keywords = data.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',')]
        
        title = str(get_value('name') or 'Untitled Recipe')
        print(f"Converted recipe: {title} with {len(data.get('recipeIngredient', []))} ingredients, {len(instructions)} instructions")
        
        return Recipe(
            title=title,
            description=str(get_value('description') or '') if get_value('description') else None,
            image=RecipeService._extract_image_url(data.get('image')),
            ingredients=data.get('recipeIngredient', []),
            instructions=instructions,
            prep_time=str(get_value('prepTime') or '') if get_value('prepTime') else None,
            cook_time=str(get_value('cookTime') or '') if get_value('cookTime') else None,
            servings=str(get_value('recipeYield') or '') if get_value('recipeYield') else None,
            cuisine=str(get_value('recipeCuisine') or '') if get_value('recipeCuisine') else None,
            category=str(get_value('recipeCategory') or '') if get_value('recipeCategory') else None,
            keywords=keywords if isinstance(keywords, list) else [],
            found_structured_data=True,
            used_ai=False
        )
    
    @staticmethod
    def _looks_like_concatenated_steps(text: str) -> bool:
        """Check if text looks like multiple steps concatenated together"""
        # Look for patterns that suggest multiple steps
        step_indicators = [
            'To Prep', 'To Cook', 'To Serve', 'Step 1', 'Step 2',
            'Heat some', 'Next', 'Then', 'When', 'After',
            '1.', '2.', '3.', '4.', '5.'
        ]
        
        found_indicators = sum(1 for indicator in step_indicators if indicator in text)
        
        # If we find multiple step indicators or the text is very long, it's likely concatenated
        return found_indicators >= 2 or len(text) > 500
    
    @staticmethod
    def _split_concatenated_instructions(text: str) -> list:
        """Split concatenated instructions into separate steps"""
        import re
        
        # Split on common patterns
        split_patterns = [
            r'\n\n+',  # Double newlines
            r'(?=To Prep)',
            r'(?=To Cook)',
            r'(?=To Serve)',
            r'(?=Next)',
            r'(?=Then)',
            r'(?=\d+\.)',  # Numbered steps like "1.", "2."
        ]
        
        instructions = [text]  # Start with the full text
        
        for pattern in split_patterns:
            new_instructions = []
            for instruction in instructions:
                parts = re.split(pattern, instruction)
                new_instructions.extend([part.strip() for part in parts if part.strip()])
            instructions = new_instructions
        
        # Clean up and filter
        cleaned_instructions = []
        for instruction in instructions:
            instruction = instruction.strip()
            if len(instruction) > 20:  # Only keep substantial instructions
                cleaned_instructions.append(instruction)
        
        print(f"Split concatenated text into {len(cleaned_instructions)} instructions")
        return cleaned_instructions if cleaned_instructions else [text]
    
    @staticmethod
    def _extract_image_url(image_data) -> Optional[str]:
        """Extract the best image URL from various image data formats"""
        if not image_data:
            return None
        
        # Case 1: Simple URL string
        if isinstance(image_data, str):
            return image_data if image_data.startswith('http') else None
        
        # Case 2: Array of images
        if isinstance(image_data, list):
            for img in image_data:
                url = RecipeService._extract_image_url(img)  # Recursive call
                if url:
                    return url  # Return first valid URL
            return None
        
        # Case 3: ImageObject or similar dict
        if isinstance(image_data, dict):
            # Try different possible URL field names
            url_fields = ['url', 'contentUrl', '@id', 'src']
            for field in url_fields:
                url = image_data.get(field)
                if url and isinstance(url, str) and url.startswith('http'):
                    return url
            
            # If no direct URL found, try nested structures
            if 'properties' in image_data:
                return RecipeService._extract_image_url(image_data['properties'])
        
        return None


    
    @staticmethod
    async def _try_ai_fallback(url: str) -> Optional[Recipe]:
        """Use AI parsing as final fallback"""
        try:
            headers = {'User-Agent': settings.USER_AGENT}
            response = requests.get(url, headers=headers, timeout=settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try AI parsing first
            ai_recipe = await parse_with_ai(soup, url)
            
            # If AI parsing succeeded but no image found, try fallback image extraction
            if ai_recipe and not ai_recipe.image:
                fallback_image = RecipeService._extract_fallback_image(soup, url)
                if fallback_image:
                    print(f"Found fallback image: {fallback_image}")
                    ai_recipe.image = fallback_image
            
            return ai_recipe
            
        except Exception as e:
            print(f"AI fallback failed: {e}")
            return None
    
    @staticmethod
    def _extract_fallback_image(soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract recipe image with og:image as priority"""
        
        # PRIORITY 1: Open Graph image (most reliable for recipe sites)
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            print(f"Found og:image: {og_image['content']}")
            return og_image['content']
        
        # PRIORITY 2: Twitter card image
        twitter_image = soup.find('meta', name='twitter:image')
        if twitter_image and twitter_image.get('content'):
            print(f"Found twitter:image: {twitter_image['content']}")
            return twitter_image['content']
        
        # PRIORITY 3: Schema.org image in meta
        schema_image = soup.find('meta', attrs={'itemprop': 'image'})
        if schema_image and schema_image.get('content'):
            print(f"Found schema image: {schema_image['content']}")
            return schema_image['content']
        
        # PRIORITY 4: Try to find a large image in the main content
        main_content = soup.find('main') or soup.find('article') or soup.find('.content')
        if main_content:
            # Look for images that are likely recipe photos (large, high-quality)
            images = main_content.find_all('img')
            for img in images:
                src = img.get('src') or img.get('data-src')  # Handle lazy loading
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('/'):
                        from urllib.parse import urljoin
                        src = urljoin(base_url, src)
                    
                    # Skip small images, icons, etc.
                    width = img.get('width')
                    height = img.get('height')
                    if width and height:
                        try:
                            if int(width) >= 300 and int(height) >= 200:
                                print(f"Found large content image: {src}")
                                return src
                        except ValueError:
                            pass
                    
                    # If no dimensions, check if it looks like a recipe image
                    alt = img.get('alt', '').lower()
                    if any(keyword in alt for keyword in ['recipe', 'dish', 'food', 'cooking']):
                        print(f"Found recipe-related image: {src}")
                        return src
        
        print("No fallback image found")
        return None
    
    @staticmethod
    def _is_complete(recipe: Recipe) -> bool:
        """Check if recipe is complete enough to use"""
        if not recipe:
            return False
            
        title_ok = recipe.title not in ["Untitled Recipe", "Could not parse recipe", "Unable to parse recipe"]
        ingredients_ok = len(recipe.ingredients) >= 3
        instructions_ok = len(recipe.instructions) >= 2
        
        print(f"Completeness check: title_ok={title_ok}, ingredients_ok={ingredients_ok}, instructions_ok={instructions_ok}")
        
        return title_ok and ingredients_ok and instructions_ok
    
    @staticmethod
    def debug_recipe(url: str) -> DebugInfo:
        """Enhanced debug using extruct to show all structured data"""
        try:
            headers = {'User-Agent': settings.USER_AGENT}
            response = requests.get(url, headers=headers, timeout=settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Use extruct for comprehensive debugging
            data = extruct.extract(
                response.text, 
                base_url=url,
                syntaxes=['json-ld', 'microdata', 'rdfa']
            )
            
            # Find all JSON-LD scripts for traditional debugging
            soup = BeautifulSoup(response.content, 'html.parser')
            json_scripts = soup.find_all('script', type='application/ld+json')
            
            json_scripts_content = []
            for i, script in enumerate(json_scripts):
                script_info = {
                    "script_number": i + 1,
                    "has_content": script.string is not None,
                    "content_preview": script.string[:200] if script.string else None
                }
                json_scripts_content.append(script_info)
            
            # Find recipes using extruct
            recipes = RecipeService._find_recipes_in_extruct_data(data)
            
            # Add extruct info to the first script's content for debugging
            if json_scripts_content:
                json_scripts_content[0]["extruct_info"] = {
                    "json_ld_items": len(data.get('json-ld', [])),
                    "microdata_items": len(data.get('microdata', [])),
                    "recipes_found": len(recipes),
                    "recipe_titles": [r.get('name', 'Unnamed') for r in recipes[:3]]
                }
            
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
