from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List

class RecipeURL(BaseModel):
    """Request model for recipe URL parsing"""
    url: HttpUrl = Field(..., description="The recipe URL to parse")

class Recipe(BaseModel):
    """Recipe data model"""
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    source: Optional[str] = None
    ingredients: List[str]
    instructions: List[str]
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    servings: Optional[str] = None
    cuisine: Optional[str] = None
    category: Optional[str] = None
    keywords: List[str] = []
    found_structured_data: bool = False
    used_ai: bool = False

class DebugInfo(BaseModel):
    """Debug information about a webpage"""
    status: str
    html_length: Optional[int] = None
    json_scripts_found: Optional[int] = None
    json_scripts_content: Optional[List[dict]] = None
    ai_available: Optional[bool] = None
    error: Optional[str] = None
    error_type: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    ai_available: bool
    timestamp: Optional[str] = None
