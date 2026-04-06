"""
Configuration management using Pydantic settings.
Loads environment variables and provides typed config access.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # OpenRouter API
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    MODEL_NAME: str = "qwen/qwen3-235b-a22b"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Memory
    MAX_MEMORY_ITEMS: int = 100
    MAX_CHAT_HISTORY: int = 50

    # Tools
    ENABLE_SHELL_TOOL: bool = True
    ENABLE_FILE_TOOL: bool = True
    ENABLE_WEB_TOOL: bool = True

    # Safety
    SHELL_TIMEOUT: int = 30
    MAX_FILE_SIZE: int = 10_000_000  # 10MB


settings = Settings()
