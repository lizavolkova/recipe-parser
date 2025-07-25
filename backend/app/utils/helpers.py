from bs4 import BeautifulSoup
from app.models import Recipe

def extract_main_content(soup: BeautifulSoup) -> str:
    """Extract the main content area for AI parsing, removing navigation, ads, etc."""
    
    # Remove unwanted elements
    for element in soup(['nav', 'header', 'footer', 'aside', 'script', 'style']):
        element.decompose()
    
    # Remove elements with common ad/navigation classes
    unwanted_classes = ['nav', 'navigation', 'sidebar', 'footer', 'header', 'ad', 'advertisement']
    for class_name in unwanted_classes:
        for element in soup.find_all(class_=lambda x: x and any(cls in str(x).lower() for cls in unwanted_classes)):
            element.decompose()
    
    # Try to find main content area
    main_selectors = [
        'main',
        '.main',
        '.content',
        '.post',
        '.entry',
        '.recipe',
        'article'
    ]
    
    for selector in main_selectors:
        main_content = soup.select_one(selector)
        if main_content:
            return main_content.get_text(separator=' ', strip=True)
    
    # Fallback: return body text
    body = soup.find('body')
    if body:
        return body.get_text(separator=' ', strip=True)
    
    return soup.get_text(separator=' ', strip=True)
