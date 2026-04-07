"""
Configuration management using Pydantic settings.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # OpenRouter API
    OPENROUTER_API_KEY: str = "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"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    MODEL_NAME: str = "openai/gpt-oss-120b:free"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

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

    class Config:
        env_file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", ".env")
        )
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env vars


# Create settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"Warning: Error loading settings: {e}")
    print("Using defaults...")
    settings = Settings(
        _env_file=None,  # type: ignore
    )
