"""
Agentic AI Chat System v2 — Main Entry Point
Production-grade multi-agent system with LangGraph orchestration.
"""

import sys
import os
import logging

# Ensure backend directory is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")

# Create FastAPI app
app = FastAPI(
    title="Agentic AI Chat System v2",
    description="Multi-agent orchestration with LangGraph, streaming, and tool execution",
    version="2.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers after app creation to avoid circular imports
from api.routes import router as api_router
from api.websocket import router as ws_router

app.include_router(api_router, prefix="/api", tags=["API"])
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "model": settings.MODEL_NAME,
        "api_key_set": bool(settings.OPENROUTER_API_KEY),
    }


@app.on_event("startup")
async def startup_event():
    # Pre-build the graph on startup
    from graph.graph_builder import get_compiled_graph
    get_compiled_graph()

    # Create sandbox
    os.makedirs(os.path.join(os.getcwd(), "sandbox"), exist_ok=True)

    logger.info("=" * 60)
    logger.info("Agentic AI Chat System v2 — Started")
    logger.info(f"   Model:   {settings.MODEL_NAME}")
    logger.info(f"   API Key: {'Set' if settings.OPENROUTER_API_KEY else 'MISSING'}")
    logger.info(f"   Debug:   {settings.DEBUG}")
    logger.info(f"   Tools:   file={settings.ENABLE_FILE_TOOL} web={settings.ENABLE_WEB_TOOL} shell={settings.ENABLE_SHELL_TOOL}")
    logger.info("=" * 60)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
        ws_max_size=16777216,  # 16MB max WS message
    )
