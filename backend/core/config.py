"""
Application configuration — loads from .env and environment variables.
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # LLM
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
    MAX_MEMORY_ITEMS: int = 200
    MAX_CHAT_HISTORY: int = 50

    # Tools
    ENABLE_SHELL_TOOL: bool = True
    ENABLE_FILE_TOOL: bool = True
    ENABLE_WEB_TOOL: bool = True

    # Safety
    SHELL_TIMEOUT: int = 30
    MAX_FILE_SIZE: int = 10_000_000

    # Agent
    MAX_RETRIES: int = 3
    MAX_PLAN_STEPS: int = 10
    MAX_RECURSIVE_DEPTH: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
