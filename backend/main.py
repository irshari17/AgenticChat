"""
Main entry point for the Agentic AI Chat System backend.
"""

import sys
import os
from contextlib import asynccontextmanager

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("=" * 60)
    print("🤖 Agentic AI Chat System - Backend Started")
    print(f"   Model: {settings.MODEL_NAME}")
    print(f"   API Key set: {'Yes' if settings.OPENROUTER_API_KEY else 'NO - SET YOUR API KEY!'}")
    print(f"   Debug: {settings.DEBUG}")
    print("=" * 60)
    yield
    # Shutdown
    print("=" * 60)
    print("🛑 Agentic AI Chat System - Backend Shutting Down")
    print("=" * 60)


app = FastAPI(
    title="Agentic AI Chat System",
    description="Production-grade agentic chat with LangGraph orchestration",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and mount routes AFTER app creation
from api.routes import router as api_router
from api.websocket import router as ws_router

app.include_router(api_router, prefix="/api")
app.include_router(ws_router, prefix="/ws")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
