"""
CV Processing Pipeline Integration

Clean architecture pipeline orchestrator:
  STEP 1-4: Geometric extraction via PDFExtractor
  STEP 5: LLM-based structured extraction via HRExtractorAgent
  STEP 6: Enrichment via PostProcessor (experience calculation, seniority level)

This module provides a unified interface for end-to-end CV processing with
a direct chain: PDFExtractor → HRExtractorAgent → PostProcessor.

No legacy regex/keyword extraction, no rule-based section detection.
Trust the LLM output, enrich through computation only.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Any

from src.extraction.pdf_extractor import PDFExtractor, ExtractionResult
from src.extraction.hr_extractor_agent import HRExtractorAgent, ExtractionConfig
from src.processing.post_processor import PostProcessor

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for CV processing pipeline."""
    use_llm: bool = True
    llm_model: str = "qwen2.5-coder:3b"
    llm_base_url: str = "http://localhost:11434"
    llm_timeout: int = 30
    llm_temperature: float = 0.1
    output_markdown_dir: Optional[str] = None
    output_json_dir: Optional[str] = None
    debug: bool = False


@dataclass
class ProcessingResult:
    """Result of full pipeline processing."""
    success: bool
    filename: str
    
    # STEP 1-4 outputs: Geometric extraction
    intermediate_markdown: str  # Unformatted dump from geometric pipeline
    ordered_text: str           # Plain ordered text (geometric + simple formatting)
    total_pages: int
    
    # STEP 5 outputs: LLM extraction
    extracted_profile: Optional[Dict[str, Any]] = None
    extraction_method: str = "pymupdf"
    
    # STEP 6 outputs: Post-processing enrichment
    total_years_experience: float = 0.0
    seniority_level: Optional[str] = None
    
    # Metadata
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class CVProcessingPipeline:
    """
    Unified CV processing pipeline with Clean Architecture.
    
    Process flow:
    1. STEP 1-4: Geometric extraction (PDFExtractor)
       - Word extraction via PyMuPDF
       - Line assembly
       - Block detection (including tables)
       - Reading order assembly → intermediate markdown dump
    
    2. STEP 5: LLM-based structured extraction (HRExtractorAgent)
       - Pass full_text from geometric extraction to LLM
       - Extract structured candidate profile via JSON schema
       - Fallback strategy if LLM unavailable
    
    3. STEP 6: Post-processing enrichment (PostProcessor)
       - Date normalization
       - Years of experience calculation from career entries
       - Seniority level assignment based on experience + title signals
    
    Design principle: Trust LLM output, add value through computation only.
    No keyword lists, no fuzzy matching, no regex-based fallbacks for section detection.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the pipeline with configuration.
        
        Args:
            config: PipelineConfig instance
        """
        self.config = config or PipelineConfig()
        
        # Initialize extractors
        self.pdf_extractor = PDFExtractor()
        
        extraction_cfg = ExtractionConfig(
            use_llm=self.config.use_llm,
            llm_model=self.config.llm_model,
            llm_base_url=self.config.llm_base_url,
            llm_timeout=self.config.llm_timeout,
            temperature=self.config.llm_temperature,
        )
        self.hr_agent = HRExtractorAgent(extraction_cfg)
        self.post_processor = PostProcessor()
        
        # Create output directories if specified
        if self.config.output_markdown_dir:
            Path(self.config.output_markdown_dir).mkdir(parents=True, exist_ok=True)
        if self.config.output_json_dir:
            Path(self.config.output_json_dir).mkdir(parents=True, exist_ok=True)
        
        if self.config.debug:
            logger.setLevel(logging.DEBUG)

    def process_pdf(self, pdf_path: str) -> ProcessingResult:
        """
        Process a PDF through the complete pipeline.

        Flow:
        1. Extract geometry & text (PDFExtractor)
        2. Extract structured data (HRExtractorAgent)
        3. Enrich with computed values (PostProcessor)

        Args:
            pdf_path (str): Path to PDF file

        Returns:
            ProcessingResult with all outputs and metadata
        """
        filename = os.path.basename(pdf_path)
        logger.info(f"[Pipeline] Starting: {filename}")

        # Validate file exists
        if not os.path.exists(pdf_path):
            error_msg = f"File not found: {pdf_path}"
            logger.error(f"[Pipeline] {error_msg}")
            return ProcessingResult(
                success=False,
                filename=filename,
                intermediate_markdown="",
                ordered_text="",
                total_pages=0,
                error=error_msg
            )

        try:
            # STEP 1-4: Geometric extraction
            logger.debug(f"[Pipeline] STEP 1-4: Geometric extraction...")
            extraction_result: ExtractionResult = self.pdf_extractor.extract(pdf_path)

            if not extraction_result.is_success:
                logger.error(f"[Pipeline] Geometric extraction failed: {extraction_result.error}")
                return ProcessingResult(
                    success=False,
                    filename=filename,
                    intermediate_markdown="",
                    ordered_text="",
                    total_pages=extraction_result.total_pages,
                    error=extraction_result.error
                )

            logger.debug(f"[Pipeline] STEP 1-4 complete: {extraction_result.total_pages} pages extracted")

            # Save intermediate markdown dump (if output_markdown_dir is configured)
            if self.config.output_markdown_dir:
                pdf_name = Path(pdf_path).stem
                markdown_path = os.path.join(
                    self.config.output_markdown_dir,
                    f"{pdf_name}.md"
                )
                with open(markdown_path, "w", encoding="utf-8") as f:
                    f.write(extraction_result.intermediate_markdown)
                logger.info(f"[Pipeline] Intermediate markdown saved: {markdown_path}")

            # STEP 5: LLM-based structured extraction
            logger.debug(f"[Pipeline] STEP 5: LLM-based extraction...")
            llm_result = self.hr_agent.extract_cv(extraction_result.full_text)

            if llm_result.get("status") not in ("success", "partial"):
                error_msg = "; ".join(llm_result.get("errors", ["Unknown LLM error"]))
                logger.warning(f"[Pipeline] LLM extraction failed: {error_msg}")
                extracted_profile = None
            else:
                extracted_profile = llm_result.get("profile")
                logger.debug(f"[Pipeline] STEP 5 complete: Profile extracted")

            # STEP 6: Post-processing enrichment
            logger.debug(f"[Pipeline] STEP 6: Post-processing...")
            total_years = 0.0
            seniority_level = None

            if extracted_profile:
                try:
                    # The extracted_profile from HRExtractorAgent is a dict,
                    # we need to pass the actual CandidateProfile object if available
                    # For now, we extract the computed values from llm_result
                    processing_result = self.post_processor.process(extracted_profile)
                    total_years = processing_result.total_years_experience
                    seniority_level = processing_result.seniority_level.value if processing_result.seniority_level else None
                    logger.debug(f"[Pipeline] Post-processing complete: {total_years} years, {seniority_level}")
                except Exception as e:
                    logger.warning(f"[Pipeline] Post-processing partial failure: {e}")

            # Prepare final result
            result = ProcessingResult(
                success=True,
                filename=filename,
                intermediate_markdown=extraction_result.intermediate_markdown,
                ordered_text=extraction_result.full_text,
                total_pages=extraction_result.total_pages,
                extracted_profile=extracted_profile,
                extraction_method="pymupdf",
                total_years_experience=total_years,
                seniority_level=seniority_level,
                metadata={
                    "extraction_status": llm_result.get("status", "unknown"),
                    "extraction_method": llm_result.get("extraction_method", "unknown"),
                }
            )

            logger.info(
                f"[Pipeline] Complete: {extraction_result.total_pages} pages, "
                f"{total_years} years exp, {seniority_level} seniority"
            )
            return result

        except Exception as e:
            logger.error(f"[Pipeline] Unexpected error: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                filename=filename,
                intermediate_markdown="",
                ordered_text="",
                total_pages=0,
                error=f"Pipeline error: {str(e)}"
            )

    def process_batch(
        self,
        pdf_dir: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, ProcessingResult]:
        """
        Process multiple PDFs in a directory.

        Args:
            pdf_dir (str): Directory containing PDF files
            output_dir (str): Output directory for results (optional)

        Returns:
            Dict[filename] → ProcessingResult
        """
        results = {}
        pdf_files = list(Path(pdf_dir).glob("*.pdf"))

        logger.info(f"[Batch] Starting batch processing: {len(pdf_files)} files")

        for pdf_file in pdf_files:
            logger.info(f"[Batch] Processing: {pdf_file.name}")
            result = self.process_pdf(str(pdf_file))
            results[pdf_file.name] = result

        logger.info(f"[Batch] Complete: {len(results)} files processed")
        return results