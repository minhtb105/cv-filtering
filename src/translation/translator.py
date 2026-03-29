"""
Ollama Translation Service
Translates Vietnamese CV text to English
"""

import json
import requests
from typing import Optional
from src.config import settings


class OllamaTranslator:
    """Translation service using Ollama"""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.source_lang = settings.TRANSLATION_SOURCE_LANG
        self.target_lang = settings.TRANSLATION_TARGET_LANG

    def translate(self, text: str, source_lang: Optional[str] = None) -> str:
        """Translate text from source to target language"""
        if not text or not text.strip():
            return text

        src = source_lang or self.source_lang
        tgt = self.target_lang

        if src == tgt:
            return text

        prompt = self._build_prompt(text, src, tgt)

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", text).strip()
            else:
                return text

        except Exception:
            return text

    def _build_prompt(self, text: str, source_lang: str, target_lang: str) -> str:
        """Build translation prompt"""
        return f"""Translate the following {source_lang} CV/resume text to {target_lang}.
Only output the translated text, no explanations.

{text}

{target_lang}:"""

    def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False


__all__ = ["OllamaTranslator"]
