"""
Main PDF Extractor with fallback chain
Tries pdfplumber first, falls back to pypdfium2
"""

import os
from typing import Optional
from .pdf_result import PDFExtractResult
from .pdfplumber_extractor import PDFPlumberExtractor
from .pypdfium2_extractor import PyPDFium2Extractor


class PDFExtractor:
    """Main PDF extractor with fallback support"""

    def __init__(self):
        self.extractors = [
            PDFPlumberExtractor(),
            PyPDFium2Extractor(),
        ]

    def extract(self, pdf_path: str) -> PDFExtractResult:
        """Extract text from PDF with fallback"""
        if not os.path.exists(pdf_path):
            return PDFExtractResult(
                pages=[],
                total_pages=0,
                source_path=pdf_path,
                extraction_method="none",
                error=f"File not found: {pdf_path}"
            )

        last_error = None
        for extractor in self.extractors:
            result = extractor.extract(pdf_path)
            if result.is_success:
                return result
            last_error = result.error

        return PDFExtractResult(
            pages=[],
            total_pages=0,
            source_path=pdf_path,
            extraction_method="failed",
            error=last_error or "All extraction methods failed"
        )

    def extract_single_page(self, pdf_path: str, page_number: int) -> Optional[str]:
        """Extract single page text"""
        result = self.extract(pdf_path)
        if result.is_success and 1 <= page_number <= len(result.pages):
            return result.pages[page_number - 1].text
        return None


__all__ = ["PDFExtractor"]
