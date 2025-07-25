# backend/app/routes/health.py (Updated)
from fastapi import APIRouter
from datetime import datetime
from app.models import HealthResponse
from app.config import openai_client, settings

router = APIRouter()

@router.get("/")
def read_root():
    """Basic hello world endpoint"""
    return {"message": "Hello, AI-Enhanced Recipe Parser!"}

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint - now includes AI categorization status"""
    return HealthResponse(
        status="healthy", 
        ai_available=openai_client is not None,
        ai_model=settings.AI_MODEL if openai_client else None,
        ai_categorization_enabled=True,  # Now standard behavior
        timestamp=datetime.now().isoformat()
    )
