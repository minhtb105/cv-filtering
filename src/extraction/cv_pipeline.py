"""
CV Processing Pipeline Integration

Full 5-step pipeline orchestrator:
  STEP 1-4: Geometric extraction via PDFExtractor
  STEP 5A/5B: Section extraction via CVReadingOrder

This module provides a clean unified interface for end-to-end CV processing.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Any

from src.extraction.pdf_extractor import PDFExtractor
from src.extraction.cv_reading_order import CVReadingOrder, ExtractionMode, ExtractedSection

logger = logging.getLogger(__name__)


# Import ExtractionResult from the module - handle both locations
try:
    from .pdf_extractor import ExtractionResult
except ImportError:
    try:
        from pdf_extractor import ExtractionResult
    except ImportError:
        # Define it locally if not available
        @dataclass
        class ExtractionResult:
            """Result of PDF extraction."""
            intermediate_markdown: str
            full_text: str
            total_pages: int
            is_success: bool
            error: str = ""


@dataclass
class PipelineConfig:
    """Configuration for CV processing pipeline."""
    use_llm: bool = False
    output_markdown_dir: Optional[str] = None
    output_json_dir: Optional[str] = None
    debug: bool = False


@dataclass
class ProcessingResult:
    """Result of full pipeline processing."""
    success: bool
    filename: str
    
    # Step 1-4 outputs
    intermediate_markdown: str  # Unformatted dump from Step 4
    ordered_text: str           # Plain ordered text (for review)
    total_pages: int
    
    # Step 5 outputs
    extracted_sections: Dict[str, ExtractedSection]  # Structured content by type
    
    # Metadata
    extraction_method: str  # "pymupdf" or "pdfplumber"
    error: str = ""
    metadata: Dict[str, Any] = None
    
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CVProcessingPipeline:
    """
    Unified 5-step CV processing pipeline.
    
    STEP 1-4: Geometric extraction
      - Word extraction (PyMuPDF primary)
      - Line assembly
      - Block detection (including tables)
      - Reading order assembly → intermediate markdown dump
    
    STEP 5: Section extraction
      - Mode A: NO-LLM regex-based (~75-80% accuracy, fast)
      - Mode B: LLM-based (~95%+ accuracy, requires LLM service)
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.pdf_extractor = PDFExtractor()
        self.reading_order = CVReadingOrder(
            mode=ExtractionMode.LLM if self.config.use_llm else ExtractionMode.NO_LLM
        )
        
        # Create output directories if specified
        if self.config.output_markdown_dir:
            Path(self.config.output_markdown_dir).mkdir(parents=True, exist_ok=True)
        if self.config.output_json_dir:
            Path(self.config.output_json_dir).mkdir(parents=True, exist_ok=True)
        
        if self.config.debug:
            logger.setLevel(logging.DEBUG)

    def process_pdf(self, pdf_path: str) -> ProcessingResult:
        """
        Process a PDF through the complete 5-step pipeline.

        Args:
            pdf_path: Path to PDF file

        Returns:
            ProcessingResult with all intermediate and final outputs
        """
        filename = os.path.basename(pdf_path)
        logger.info(f"Starting pipeline processing: {filename}")

        # Validate file
        if not os.path.exists(pdf_path):
            return ProcessingResult(
                success=False,
                filename=filename,
                intermediate_markdown="",
                ordered_text="",
                total_pages=0,
                extracted_sections={},
                extraction_method="",
                error=f"File not found: {pdf_path}"
            )

        try:
            # STEP 1-4: Geometric extraction
            logger.debug(f"Running STEP 1-4: Geometric extraction...")
            extraction_result: ExtractionResult = self.pdf_extractor.extract(pdf_path)

            if not extraction_result.is_success:
                return ProcessingResult(
                    success=False,
                    filename=filename,
                    intermediate_markdown="",
                    ordered_text="",
                    total_pages=extraction_result.total_pages,
                    extracted_sections={},
                    extraction_method="",
                    error=extraction_result.error
                )

            # Save intermediate markdown dump
            markdown_path = None
            if self.config.output_markdown_dir:
                markdown_path = os.path.join(
                    self.config.output_markdown_dir,
                    f"{Path(pdf_path).stem}.md"
                )
                with open(markdown_path, "w", encoding="utf-8") as f:
                    f.write(extraction_result.intermediate_markdown)
                logger.info(f"Intermediate markdown saved: {markdown_path}")

            # STEP 5: Section extraction
            logger.debug(f"Running STEP 5: Section extraction...")
            extracted_sections = self.reading_order.extract(
                extraction_result.intermediate_markdown
            )

            # Save extracted sections as JSON
            json_path = None
            if self.config.output_json_dir and extracted_sections:
                json_path = os.path.join(
                    self.config.output_json_dir,
                    f"{Path(pdf_path).stem}_extracted.json"
                )
                import json
                json_data = {
                    section_type: {
                        "content": section.content,
                        "confidence": section.confidence
                    }
                    for section_type, section in extracted_sections.items()
                }
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Extracted JSON saved: {json_path}")

            # Prepare result
            result = ProcessingResult(
                success=True,
                filename=filename,
                intermediate_markdown=extraction_result.intermediate_markdown,
                ordered_text=extraction_result.full_text,
                total_pages=extraction_result.total_pages,
                extracted_sections=extracted_sections,
                extraction_method="pymupdf",  # Primary extraction method
                metadata={
                    "markdown_file": markdown_path,
                    "json_file": json_path,
                    "sections_found": len(extracted_sections),
                    "extraction_mode": self.reading_order.mode.value,
                }
            )

            logger.info(
                f"Pipeline completed successfully: "
                f"{len(extracted_sections)} sections extracted from {result.total_pages} pages"
            )
            return result

        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                filename=filename,
                intermediate_markdown="",
                ordered_text="",
                total_pages=0,
                extracted_sections={},
                extraction_method="",
                error=str(e)
            )

    def process_batch(self, pdf_dir: str, output_dir: Optional[str] = None) -> Dict[str, ProcessingResult]:
        """
        Process multiple PDFs in a directory.

        Args:
            pdf_dir: Directory containing PDF files
            output_dir: Output directory for results

        Returns:
            Dict[filename] → ProcessingResult
        """
        results = {}
        pdf_files = list(Path(pdf_dir).glob("*.pdf"))

        logger.info(f"Processing {len(pdf_files)} PDF files from {pdf_dir}")

        for pdf_file in pdf_files:
            logger.info(f"Processing: {pdf_file.name}")
            result = self.process_pdf(str(pdf_file))
            results[pdf_file.name] = result

        logger.info(f"Batch processing completed: {len(results)} files processed")
        return results