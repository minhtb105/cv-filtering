"""
Configuration management for CV Intelligence Platform
Loads settings from .env file with sensible defaults
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings"""

    def __init__(self):
        # MongoDB
        self.MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.MONGODB_DB: str = os.getenv("MONGODB_DB", "cv_intelligence")

        # Ollama
        self.OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b-instruct-q4_K_M")

        # Gemini (for some features)
        self.GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

        # Extraction
        self.EXTRACTION_CACHE_ENABLED: bool = os.getenv("EXTRACTION_CACHE_ENABLED", "true").lower() == "true"
        self.EXTRACTION_TIMEOUT: int = int(os.getenv("EXTRACTION_TIMEOUT", "30"))

        # Translation
        self.TRANSLATION_ENABLED: bool = os.getenv("TRANSLATION_ENABLED", "true").lower() == "true"
        self.TRANSLATION_SOURCE_LANG: str = os.getenv("TRANSLATION_SOURCE_LANG", "vi")
        self.TRANSLATION_TARGET_LANG: str = os.getenv("TRANSLATION_TARGET_LANG", "en")

        # Scoring
        self.MIN_MATCH_SCORE: float = float(os.getenv("MIN_MATCH_SCORE", "0.7"))
        self.REUSE_ENABLED: bool = os.getenv("REUSE_ENABLED", "true").lower() == "true"

        # API
        self.API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT: int = int(os.getenv("API_PORT", "8000"))
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

        # Paths
        self.SAMPLE_DIR: str = os.getenv("SAMPLE_DIR", "sample")
        self.OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")

    def validate(self) -> bool:
        """Validate required settings"""
        if self.MONGODB_URL is None:
            return False
        return True


settings = Settings()

if not settings.validate():
    print("[ERROR] Invalid settings. Check config.py")

__all__ = ["settings", "Settings"]
