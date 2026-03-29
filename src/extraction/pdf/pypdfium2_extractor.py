"""
PyPDFium2-based PDF extraction
Fallback extractor when pdfplumber fails
"""

import pypdfium2 as pdfium
from typing import Optional
from datetime import datetime
from .pdf_result import PDFExtractResult, ExtractedPage


class PyPDFium2Extractor:
    """Extract text from PDFs using pypdfium2"""

    def __init__(self):
        self.name = "pypdfium2"

    def extract(self, pdf_path: str) -> PDFExtractResult:
        """Extract text from PDF file"""
        try:
            pdf = pdfium.PdfDocument(pdf_path)
            pages = []

            for i in range(len(pdf)):
                page = pdf[i]
                textpage = page.get_textpage()
                text = textpage.get_text_bounded()

                width = page.get_width() if hasattr(page, "get_width") else None
                height = page.get_height() if hasattr(page, "get_height") else None

                pages.append(ExtractedPage(
                    page_number=i + 1,
                    text=self._clean_text(text),
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

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        text = text.replace("\x00", "")
        text = text.replace("\ufffd", "")

        lines = text.split("\n")
        cleaned_lines = [line.strip() for line in lines if line.strip()]

        return "\n".join(cleaned_lines)


__all__ = ["PyPDFium2Extractor"]
