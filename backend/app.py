"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.health import router as health_router
from routes.chat import router as chat_router
from routes.parts import router as parts_router


def create_app():
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="PartSelect Chat Agent API",
        version="1.0.0",
        description="""
## PartSelect Chatbot Backend API

API for searching and retrieving appliance parts information.

**Supported Appliance Types:**
- Refrigerators
- Dishwashers

**Features:**
- Product search via natural language
- Part details lookup
- Compatible models information
- Health monitoring
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Enable CORS for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(parts_router)
    
    return app


app = create_app()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
