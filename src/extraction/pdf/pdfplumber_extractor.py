"""
PDFPlumber-based PDF extraction
Primary extractor with glyph error handling
"""

import pdfplumber
from typing import Optional
from datetime import datetime
from .pdf_result import PDFExtractResult, ExtractedPage


class PDFPlumberExtractor:
    """Extract text from PDFs using pdfplumber"""

    GLYPH_MAPPING = {
        "\x00": "",
        "\ufffd": "",
        "\u0000": "",
        "\u0001": "",
        "\u0002": "",
        "\u0003": "",
        "\x01": "",
        "\x02": "",
        "\x03": "",
    }

    def __init__(self):
        self.name = "pdfplumber"

    def extract(self, pdf_path: str) -> PDFExtractResult:
        """Extract text from PDF file"""
        try:
            pages = []
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    text = self._clean_glyph_errors(text)

                    width = page.width if hasattr(page, "width") else None
                    height = page.height if hasattr(page, "height") else None

                    pages.append(ExtractedPage(
                        page_number=i,
                        text=text,
                        width=width,
                        height=height
                    ))

            return PDFExtractResult(
                pages=pages,
                total_pages=len(pages),
                source_path=pdf_path,
                extraction_method=self.name,
                extracted_at=datetime.utcnow()
            )

        except Exception as e:
            return PDFExtractResult(
                pages=[],
                total_pages=0,
                source_path=pdf_path,
                extraction_method=self.name,
                extracted_at=datetime.utcnow(),
                error=str(e)
            )

    def _clean_glyph_errors(self, text: str) -> str:
        """Clean common glyph mapping errors"""
        for old, new in self.GLYPH_MAPPING.items():
            text = text.replace(old, new)

        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)


__all__ = ["PDFPlumberExtractor"]
