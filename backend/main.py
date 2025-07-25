from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import health, recipes

# Create the FastAPI application instance
app = FastAPI(
    title="Recipe Parser API", 
    version="1.0.0",
    description="An AI-powered recipe parser that extracts structured data from recipe URLs"
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include route modules
app.include_router(health.router, tags=['health'])
app.include_router(recipes.router, tags=['recipes'])

if __name__ == "__main__":
    import uvicorn
    
    if settings.DEBUG:
        # In debug mode, use the import string for proper reloading
        uvicorn.run(
            "main:app",  # Import string instead of app object
            host=settings.API_HOST, 
            port=settings.API_PORT,
            reload=True  # This will work properly now
        )
    else:
        # In production, run directly
        uvicorn.run(
            app, 
            host=settings.API_HOST, 
            port=settings.API_PORT,
            reload=False
        )
