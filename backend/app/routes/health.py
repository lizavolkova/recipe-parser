from fastapi import APIRouter
from datetime import datetime
from app.models import HealthResponse
from app.config import openai_client

router = APIRouter()

@router.get("/")
def read_root():
    """Basic hello world endpoint"""
    return {"message": "Hello, Recipe Parser!"}

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint - useful for monitoring"""
    return HealthResponse(
        status="healthy", 
        ai_available=openai_client is not None,
        timestamp=datetime.now().isoformat()
    )
