"""
PDF Extraction Module

Handles PDF text extraction with fallback strategy:
1. Primary: PyMuPDF (fitz) - handles multi-column layouts
2. Fallback: pdfplumber - for complex PDFs
"""

import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extracts text from PDF files with fallback strategy."""

    @staticmethod
    def extract_with_pymupdf(pdf_path: str) -> Tuple[bool, str]:
        """
        Extract text using PyMuPDF (fitz).

        Returns:
            (success: bool, text: str)
        """
        try:
            import fitz  # PyMuPDF

            document = fitz.open(pdf_path)
            text = ""

            for page_num in range(len(document)):
                page = document[page_num]
                # Use sort=True to handle multi-column layouts
                page_text = page.get_text("text", sort=True)
                text += page_text + f"\n--- Page {page_num + 1} ---\n"

            document.close()

            if text.strip():
                return True, text
            else:
                return False, ""

        except ImportError:
            logger.warning("PyMuPDF not installed, cannot use primary extraction")
            return False, ""
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}")
            return False, ""

    @staticmethod
    def extract_with_pdfplumber(pdf_path: str) -> Tuple[bool, str]:
        """
        Extract text using pdfplumber (fallback).

        Returns:
            (success: bool, text: str)
        """
        try:
            import pdfplumber

            text = ""

            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + f"\n--- Page {page_num + 1} ---\n"

            if text.strip():
                return True, text
            else:
                return False, ""

        except ImportError:
            logger.warning("pdfplumber not installed")
            return False, ""
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return False, ""

    @staticmethod
    def extract_text_with_fallback(pdf_path: str) -> Tuple[bool, str, str]:
        """
        Extract text from PDF with fallback strategy.

        Args:
            pdf_path: Path to PDF file

        Returns:
            (success: bool, text: str, method: str)
            - success: True if extraction worked
            - text: Extracted text
            - method: Which method succeeded ("pymupdf", "pdfplumber", or "failed")
        """
        # Try PyMuPDF first
        success, text = PDFExtractor.extract_with_pymupdf(pdf_path)
        if success:
            logger.info(f"Successfully extracted {pdf_path} using PyMuPDF")
            return True, text, "pymupdf"

        # Fallback to pdfplumber
        success, text = PDFExtractor.extract_with_pdfplumber(pdf_path)
        if success:
            logger.info(f"Successfully extracted {pdf_path} using pdfplumber")
            return True, text, "pdfplumber"

        # Both failed
        logger.error(f"Failed to extract text from {pdf_path} with both methods")
        return False, "", "failed"

    @staticmethod
    def extract_images_with_ocr(pdf_path: str) -> Tuple[bool, str]:
        """
        Extract text from images using OCR (Tesseract fallback for image-based PDFs).

        Returns:
            (success: bool, text: str)
        """
        try:
            import pytesseract
            from pdf2image import convert_from_path

            logger.info(f"Attempting OCR extraction from {pdf_path}")

            images = convert_from_path(pdf_path)
            text = ""

            for page_num, image in enumerate(images):
                page_text = pytesseract.image_to_string(image)
                if page_text:
                    text += page_text + f"\n--- Page {page_num + 1} ---\n"

            if text.strip():
                logger.info(f"OCR extraction successful: {len(text)} chars")
                return True, text
            else:
                return False, ""

        except ImportError:
            logger.warning("Tesseract/pdf2image not available for OCR")
            return False, ""
        except Exception as e:
            logger.warning(f"OCR extraction failed: {e}")
            return False, ""
