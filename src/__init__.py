"""
CV Intelligence Platform
"""

__version__ = "1.0.0"

# Import main modules for easy access
from .processing.post_processor import PostProcessor
from .extraction import (
    CVProcessingPipeline,
    CVParser,
    CVParsingConfig,
    TextCleaner,
    PDFExtractor,
    LLMExtractor,
    LLMExtractionConfig
)

__all__ = [
    "PostProcessor",
    "CVProcessingPipeline",
    "CVParser",
    "CVParsingConfig",
    "TextCleaner",
    "PDFExtractor",
    "LLMExtractor",
    "LLMExtractionConfig",
]
