from typing import Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class ImageExtractor:
    """Handles image extraction from recipe pages"""
    
    @staticmethod
    def extract_og_image(soup: BeautifulSoup) -> Optional[str]:
        """Extract og:image - most reliable for recipe sites"""
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image.get('content')
        
        # Fallback to twitter:image
        twitter_image = soup.find('meta', name='twitter:image')
        if twitter_image and twitter_image.get('content'):
            return twitter_image.get('content')
        
        return None
    
    @staticmethod
    def extract_from_structured_data(image_data) -> Optional[str]:
        """Extract image URL from various structured data formats"""
        if not image_data:
            return None
        
        # Case 1: Simple URL string
        if isinstance(image_data, str):
            return image_data if image_data.startswith('http') else None
        
        # Case 2: Array of images
        if isinstance(image_data, list):
            for img in image_data:
                url = ImageExtractor.extract_from_structured_data(img)  # Recursive
                if url:
                    return url  # Return first valid URL
        
        # Case 3: ImageObject or similar dict
        if isinstance(image_data, dict):
            for field in ['url', 'contentUrl', '@id', 'src']:
                url = image_data.get(field)
                if url and isinstance(url, str) and url.startswith('http'):
                    return url
        
        return None
    
    @staticmethod
    def extract_fallback_image(soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract recipe image from meta tags and content as fallback"""
        
        # Priority 1: Open Graph image (most reliable)
        og_image = ImageExtractor.extract_og_image(soup)
        if og_image:
            print(f"Found og:image: {og_image}")
            return og_image
        
        # Priority 2: Schema.org image in meta
        schema_image = soup.find('meta', attrs={'itemprop': 'image'})
        if schema_image and schema_image.get('content'):
            print(f"Found schema image: {schema_image['content']}")
            return schema_image['content']
        
        # Priority 3: Large images in main content
        main_content = soup.find('main') or soup.find('article') or soup.find('.content')
        if main_content:
            images = main_content.find_all('img')
            for img in images:
                src = img.get('src') or img.get('data-src')  # Handle lazy loading
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('/'):
                        src = urljoin(base_url, src)
                    
                    # Check if it looks like a recipe image
                    if ImageExtractor._is_recipe_image(img, src):
                        print(f"Found content image: {src}")
                        return src
        
        print("No fallback image found")
        return None
    
    @staticmethod
    def _is_recipe_image(img_tag, src: str) -> bool:
        """Check if an image looks like a recipe photo"""
        # Skip small images, icons, etc.
        width = img_tag.get('width')
        height = img_tag.get('height')
        if width and height:
            try:
                if int(width) >= 300 and int(height) >= 200:
                    return True
            except ValueError:
                pass
        
        # Check alt text for recipe-related keywords
        alt = img_tag.get('alt', '').lower()
        if any(keyword in alt for keyword in ['recipe', 'dish', 'food', 'cooking']):
            return True
        
        # Check src for recipe-related keywords
        if any(keyword in src.lower() for keyword in ['recipe', 'dish', 'food', 'cooking']):
            return True
        
        return False
