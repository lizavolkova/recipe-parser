"""
Development server script
Run with: python dev.py
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("🚀 Starting Recipe Parser API in development mode...")
    print(f"   Host: {settings.API_HOST}")
    print(f"   Port: {settings.API_PORT}")
    print(f"   Debug: {settings.DEBUG}")
    print(f"   AI Available: {settings.OPENAI_API_KEY != ''}")
    print("   Auto-reload: ✅ Enabled")
    print("   Docs: http://localhost:8000/docs")
    print()
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level="info"
    )
