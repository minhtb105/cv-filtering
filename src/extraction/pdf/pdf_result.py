"""
PDF Extraction Result - Standardized output from PDF extraction
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class ExtractedPage:
    """Single page extraction result"""
    page_number: int
    text: str
    width: Optional[float] = None
    height: Optional[float] = None


@dataclass
class PDFExtractResult:
    """Complete PDF extraction result"""
    pages: List[ExtractedPage]
    total_pages: int
    source_path: str
    extraction_method: str
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None

    @property
    def full_text(self) -> str:
        """Get all page text combined"""
        return "\n\n".join(p.text for p in self.pages)

    @property
    def is_success(self) -> bool:
        """Check if extraction was successful"""
        return self.error is None and bool(self.full_text.strip())


__all__ = ["ExtractedPage", "PDFExtractResult"]
