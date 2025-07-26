"""
Clean ingredient parser using Python's built-in fractions module
Converts unicode fractions for parsing, then back to unicode for display
Updated with confidence threshold logic for fallback to original text
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from fractions import Fraction
import re
from ingredient_parser import parse_ingredient


@dataclass
class StructuredIngredient:
    """Represents a fully parsed ingredient with all components"""
    raw_ingredient: str          # For recipe search/filtering: "flour", "butter"
    quantity: Optional[str]      # For shopping lists: "3", "1/2"  
    unit: Optional[str]          # For shopping lists: "cups", "tsp"
    descriptors: List[str] = field(default_factory=list)  # For context: ["fresh", "chopped", "room temperature"]
    original_text: str = ""      # Original: "3 cups all-purpose flour, sifted"
    confidence: float = 0.0      # How confident the parser is
    used_fallback: bool = False  # Whether we fell back to original text


# Unicode fraction mappings (bidirectional)
UNICODE_TO_FRACTION = {
    '½': '1/2', '⅓': '1/3', '⅔': '2/3', '¼': '1/4', '¾': '3/4',
    '⅕': '1/5', '⅖': '2/5', '⅗': '3/5', '⅘': '4/5', '⅙': '1/6', '⅚': '5/6',
    '⅛': '1/8', '⅜': '3/8', '⅝': '5/8', '⅞': '7/8'
}

FRACTION_TO_UNICODE = {v: k for k, v in UNICODE_TO_FRACTION.items()}

# Configuration
CONFIDENCE_THRESHOLD = 0.6  # Adjustable threshold


def normalize_fractions_for_parsing(text: str) -> str:
    """
    Convert unicode fractions to text fractions for ML parsing
    """
    for unicode_frac, text_frac in UNICODE_TO_FRACTION.items():
        text = text.replace(unicode_frac, text_frac)
    
    # Fix spacing issues like "1/2-inch" -> "1/2 inch"
    text = re.sub(r'(\d+/\d+)-', r'\1 ', text)
    
    return text


def convert_to_unicode_fraction(fraction_str: str) -> str:
    """
    Convert text fractions to unicode and improper fractions to mixed numbers
    Examples: "7/2" → "3 ½", "5/4" → "1 ¼", "1/2" → "½"
    """
    if not fraction_str:
        return fraction_str
    
    try:
        # Handle decimal numbers
        if '.' in fraction_str:
            frac = Fraction(float(fraction_str)).limit_denominator()
        else:
            frac = Fraction(fraction_str)
        
        # Convert improper fractions to mixed numbers
        if frac.numerator >= frac.denominator and frac.denominator != 1:
            # Calculate whole part and remaining fraction
            whole_part = frac.numerator // frac.denominator
            remainder = frac.numerator % frac.denominator
            
            if remainder == 0:
                # It's a whole number
                return str(whole_part)
            else:
                # Mixed number: whole + fraction
                fractional_part = Fraction(remainder, frac.denominator)
                fractional_str = str(fractional_part)
                
                # Try to convert fractional part to unicode
                unicode_frac = FRACTION_TO_UNICODE.get(fractional_str, fractional_str)
                return f"{whole_part} {unicode_frac}"
        else:
            # Proper fraction or whole number, just convert to unicode if possible
            frac_str = str(frac)
            return FRACTION_TO_UNICODE.get(frac_str, frac_str)
        
    except (ValueError, ZeroDivisionError):
        return fraction_str


# Minimal consolidation rules for raw ingredients only
RAW_INGREDIENT_CONSOLIDATION = {
    "eggs": ["egg", "eggs", "whole egg", "whole eggs", "large egg", "large eggs"],
    "butter": ["butter", "unsalted butter", "salted butter"],
    "sugar": ["sugar", "granulated sugar", "white sugar", "cane sugar"],
    "brown sugar": ["brown sugar", "dark brown sugar", "light brown sugar"],
    "salt": ["salt", "kosher salt", "sea salt", "table salt", "fine salt"],
    "olive oil": ["olive oil", "extra virgin olive oil", "evoo"],
}

# Ingredients to ignore completely
IGNORED_INGREDIENTS = ["water"]


def normalize_raw_ingredient(ingredient_name: str) -> Optional[str]:
    """
    Lightly normalize raw ingredient names for consolidation
    """
    name = ingredient_name.lower().strip()
    
    # Remove asterisks (footnote markers)
    name = re.sub(r'\*+', '', name).strip()
    
    # Filter out water
    if any(ignored in name for ignored in IGNORED_INGREDIENTS):
        return None
    
    # Check consolidation rules
    for consolidated_name, variations in RAW_INGREDIENT_CONSOLIDATION.items():
        if any(variation.lower() in name for variation in variations):
            return consolidated_name
    
    return name


def should_use_fallback(parsed_name: str, original_text: str, confidence: float) -> bool:
    """
    Determine if we should use original text instead of parsed result
    Simple confidence-only check
    """
    # Low confidence threshold - use original text
    if confidence < CONFIDENCE_THRESHOLD:
        print(f"🔄 Low confidence ({confidence:.3f}) for '{original_text}', using fallback")
        return True
    
    return False


def parse_ingredient_structured(ingredient_text: str, confidence_threshold: float = CONFIDENCE_THRESHOLD) -> Optional[StructuredIngredient]:
    """
    Parse a single ingredient into structured components using ingredient-parser-nlp
    Enhanced with confidence threshold fallback logic
    """
    if not ingredient_text or not ingredient_text.strip():
        return None
    
    # Normalize fractions for ML parsing
    normalized_text = normalize_fractions_for_parsing(ingredient_text)
        
    try:
        parsed = parse_ingredient(normalized_text)
        
        # Extract quantity and unit
        quantity = None
        unit = None
        if hasattr(parsed, 'amount') and parsed.amount:
            if isinstance(parsed.amount, list) and len(parsed.amount) > 0:
                amount_obj = parsed.amount[0]
                raw_quantity = getattr(amount_obj, 'quantity', None)
                unit_obj = getattr(amount_obj, 'unit', None)
                unit = str(unit_obj) if unit_obj else None
                
                # Convert quantity back to unicode fraction for display
                if raw_quantity:
                    quantity = convert_to_unicode_fraction(str(raw_quantity))
        
        # Extract ingredient name and confidence
        ingredient_name = None
        name_confidence = 1.0
        if hasattr(parsed, 'name') and parsed.name:
            if isinstance(parsed.name, list) and len(parsed.name) > 0:
                ingredient_name = parsed.name[0].text
                name_confidence = getattr(parsed.name[0], 'confidence', 1.0)
            else:
                ingredient_name = str(parsed.name)
        
        if not ingredient_name:
            return None
        
        # Check if we should use fallback based on confidence
        used_fallback = False
        if should_use_fallback(ingredient_name, ingredient_text, name_confidence):
            # Use original text as-is
            raw_ingredient = ingredient_text.strip()
            used_fallback = True
            
            # Clear quantity/unit since we're not trusting the parsing
            quantity = None
            unit = None
            descriptors = []
            
            return StructuredIngredient(
                raw_ingredient=raw_ingredient,  # This will be the original text
                quantity=quantity,
                unit=unit,
                descriptors=descriptors,
                original_text=ingredient_text,
                confidence=name_confidence,
                used_fallback=used_fallback
            )
        
        # Use parsed result (normal case)
        raw_ingredient = normalize_raw_ingredient(ingredient_name)
        if not raw_ingredient:
            return None  # Filtered out (like water)
        
        # Extract and clean descriptors
        descriptors = []
        if hasattr(parsed, 'preparation') and parsed.preparation:
            prep_text = getattr(parsed.preparation, 'text', str(parsed.preparation))
            if prep_text:
                # Clean up and split descriptors
                prep_text = prep_text.replace('(', '').replace(')', '').replace(',', '')
                descriptors = [part.strip() for part in prep_text.split() if len(part.strip()) > 1]
        
        # Add comment as descriptor if present
        if hasattr(parsed, 'comment') and parsed.comment:
            comment_text = getattr(parsed.comment, 'text', str(parsed.comment))
            if comment_text:
                comment_text = comment_text.replace('(', '').replace(')', '').replace(',', '')
                descriptors.extend([part.strip() for part in comment_text.split() if len(part.strip()) > 1])
        
        return StructuredIngredient(
            raw_ingredient=raw_ingredient,
            quantity=quantity,  # Now in unicode format: "½" not "1/2"
            unit=unit,
            descriptors=descriptors,
            original_text=ingredient_text,
            confidence=name_confidence,
            used_fallback=used_fallback
        )
        
    except Exception as e:
        print(f"Failed to parse ingredient '{ingredient_text}': {e}")
        return None


def combine_quantities(qty1: Optional[str], qty2: Optional[str]) -> Optional[str]:
    """
    Combine two quantity strings, handling fractions and decimals
    """
    if not qty1 and not qty2:
        return None
    if not qty1:
        return qty2
    if not qty2:
        return qty1
    
    try:
        # Parse both quantities as fractions to handle unicode fractions
        # First normalize any unicode fractions
        qty1_normalized = normalize_fractions_for_parsing(qty1)
        qty2_normalized = normalize_fractions_for_parsing(qty2)
        
        # Convert to fractions for accurate arithmetic
        frac1 = Fraction(qty1_normalized)
        frac2 = Fraction(qty2_normalized)
        
        # Add them together
        total = frac1 + frac2
        
        # Convert back to string and then to unicode fraction if possible
        total_str = str(total)
        return convert_to_unicode_fraction(total_str)
        
    except (ValueError, ZeroDivisionError):
        # If we can't parse as numbers, just concatenate with "+"
        return f"{qty1} + {qty2}"


def can_combine_ingredients(ing1: StructuredIngredient, ing2: StructuredIngredient) -> bool:
    """
    Check if two ingredients can be safely combined (same unit or both unitless)
    """
    # Must be same raw ingredient
    if ing1.raw_ingredient != ing2.raw_ingredient:
        return False
    
    # Can combine if units are the same (including both None)
    if ing1.unit == ing2.unit:
        return True
    
    # Can combine if both are unitless (count items like "eggs")
    if ing1.unit is None and ing2.unit is None:
        return True
    
    return False


def parse_ingredients_list(ingredients: List[str], confidence_threshold: float = CONFIDENCE_THRESHOLD) -> List[StructuredIngredient]:
    """
    Parse a list of ingredient strings into structured format with quantity consolidation
    """
    structured_ingredients = []
    ingredient_map = {}  # raw_ingredient -> list of StructuredIngredient
    
    # First pass: parse all ingredients
    for ingredient_text in ingredients:
        structured = parse_ingredient_structured(ingredient_text, confidence_threshold)
        
        if structured:
            raw_name = structured.raw_ingredient
            if raw_name not in ingredient_map:
                ingredient_map[raw_name] = []
            ingredient_map[raw_name].append(structured)
    
    # Second pass: consolidate ingredients with same name
    for raw_name, ingredient_list in ingredient_map.items():
        if len(ingredient_list) == 1:
            # Single occurrence, just add it
            structured_ingredients.append(ingredient_list[0])
        else:
            # Multiple occurrences, try to consolidate
            consolidated = consolidate_ingredient_group(ingredient_list)
            structured_ingredients.extend(consolidated)
    
    return structured_ingredients


def consolidate_ingredient_group(ingredient_list: List[StructuredIngredient]) -> List[StructuredIngredient]:
    """
    Consolidate a group of ingredients with the same raw name
    """
    if len(ingredient_list) <= 1:
        return ingredient_list
    
    # Group by unit (ingredients with same unit can be combined)
    unit_groups = {}
    for ing in ingredient_list:
        unit_key = ing.unit or "unitless"
        if unit_key not in unit_groups:
            unit_groups[unit_key] = []
        unit_groups[unit_key].append(ing)
    
    consolidated = []
    
    for unit_key, group in unit_groups.items():
        if len(group) == 1:
            # Only one ingredient with this unit, keep as-is
            consolidated.append(group[0])
        else:
            # Multiple ingredients with same unit, combine quantities
            base_ingredient = group[0]  # Use first as template
            combined_quantity = base_ingredient.quantity
            
            # Combine quantities from all ingredients in this unit group
            for ing in group[1:]:
                combined_quantity = combine_quantities(combined_quantity, ing.quantity)
            
            # Combine descriptors (remove duplicates)
            all_descriptors = []
            for ing in group:
                all_descriptors.extend(ing.descriptors)
            unique_descriptors = list(dict.fromkeys(all_descriptors))  # Preserve order, remove duplicates
            
            # Create consolidated ingredient
            consolidated_ingredient = StructuredIngredient(
                raw_ingredient=base_ingredient.raw_ingredient,
                quantity=combined_quantity,
                unit=base_ingredient.unit,
                descriptors=unique_descriptors,
                original_text=f"Combined: {', '.join([ing.original_text for ing in group])}",
                confidence=min([ing.confidence for ing in group]),  # Use lowest confidence
                used_fallback=any([ing.used_fallback for ing in group])  # True if any used fallback
            )
            
            consolidated.append(consolidated_ingredient)
    
    return consolidated


def get_raw_ingredients_for_search(structured_ingredients: List[StructuredIngredient]) -> List[str]:
    """
    Extract just the raw ingredient names for recipe search/filtering
    """
    return [ing.raw_ingredient for ing in structured_ingredients]


def get_shopping_list_items(structured_ingredients: List[StructuredIngredient]) -> List[Dict[str, Any]]:
    """
    Format ingredients for shopping list with quantities (using unicode fractions)
    Returns consolidated quantities when ingredients were combined
    """
    shopping_items = []
    
    for ing in structured_ingredients:
        # Check if this was a consolidated ingredient
        was_combined = "Combined:" in ing.original_text
        
        item = {
            "name": ing.raw_ingredient,      # Raw ingredient name
            "quantity": ing.quantity,        # Unicode: "4" for combined eggs 
            "unit": ing.unit,
            "descriptors": ing.descriptors,
            "original": ing.original_text,
            "confidence": ing.confidence,
            "shopping_display": format_shopping_item(ing),  # "4 eggs"
            "used_fallback": ing.used_fallback,
            "was_combined": was_combined     # True if quantities were added together
        }
        shopping_items.append(item)
    
    return shopping_items


def format_shopping_item(ing: StructuredIngredient) -> str:
    """
    Format an ingredient for display on shopping list (with unicode fractions)
    """
    if ing.used_fallback:
        # For fallback ingredients, use the raw ingredient which preserves original meaning
        return ing.raw_ingredient  # This will be "hummus or goat cheese"
    
    parts = []
    
    if ing.quantity:
        parts.append(ing.quantity)  # Will be "½" not "1/2"
    
    if ing.unit:
        parts.append(ing.unit)
    
    parts.append(ing.raw_ingredient)
    
    return " ".join(parts)


# Example usage and testing
if __name__ == "__main__":
    # Test basic confidence threshold
    basic_test_ingredients = [
        "hummus or goat cheese",  # Should trigger fallback due to low confidence
        "¼ cup olive oil",  # Should parse normally
        "¾ teaspoon salt",  # Should parse normally
    ]
    
    print("🧪 Testing simplified confidence threshold logic:")
    print(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
    print("=" * 60)
    
    for ingredient in basic_test_ingredients:
        result = parse_ingredient_structured(ingredient)
        if result:
            print(f"Original: {ingredient}")
            print(f"  Name: {result.raw_ingredient}")
            print(f"  Confidence: {result.confidence:.3f}")
            print(f"  Used fallback: {result.used_fallback}")
            print(f"  Shopping display: {format_shopping_item(result)}")
            if result.used_fallback:
                print(f"  ✅ Used original text due to low confidence")
            print("-" * 40)
    
    # Test mixed fraction conversion
    print("\n🔢 Testing mixed fraction conversion:")
    print("=" * 60)
    
    fraction_tests = ["7/2", "5/4", "3/2", "1/2", "11/4", "9/8"]
    for frac in fraction_tests:
        converted = convert_to_unicode_fraction(frac)
        print(f"{frac} → {converted}")
    
    # Test quantity consolidation
    print("\n🥚 Testing quantity consolidation (eggs example):")
    print("=" * 60)
    
    consolidation_test = [
        "1 whole egg (whisked)",
        "3 eggs",
        "2 cups flour",
        "1 cup flour",  # Should combine to 3 cups
        "1 tablespoon butter",
        "1 cup butter (cold)",  # Different unit, should stay separate
        "3 1/2 pounds pumpkin",  # Test mixed fraction input
        "1/2 pound pumpkin"      # Should combine to 4 pounds
    ]
    
    consolidated_results = parse_ingredients_list(consolidation_test)
    
    for result in consolidated_results:
        print(f"Consolidated: {result.raw_ingredient}")
        print(f"  Quantity: {result.quantity} {result.unit or ''}")
        print(f"  Shopping display: {format_shopping_item(result)}")
        if "Combined:" in result.original_text:
            print(f"  ✅ Combined from multiple ingredients")
        print("-" * 40)
