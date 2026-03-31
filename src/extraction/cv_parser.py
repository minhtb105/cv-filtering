"""
CV Parser - Main Public API

Simplified CV parsing interface using Clean Architecture pipeline:
- STEP 1-4: Geometric extraction (PDFExtractor)
- STEP 5: LLM-based structured extraction (HRExtractorAgent)
- STEP 6: Enrichment (PostProcessor)

This parser provides a high-level interface that wraps CVProcessingPipeline,
handling file I/O, result serialization, and format conversion.

Design principle: Trust LLM output, enrich through computation only.
No keyword lists, no fuzzy matching, no regex-based section detection.
"""

import logging
import os
import json
from typing import Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass

from src.extraction.cv_pipeline import CVProcessingPipeline, PipelineConfig, ProcessingResult

logger = logging.getLogger(__name__)


@dataclass
class CVParsingConfig:
    """Configuration for CV parsing."""
    use_llm_extraction: bool = True
    llm_model: str = "qwen2.5-coder:3b"
    llm_base_url: str = "http://localhost:11434"
    llm_timeout: int = 30
    output_markdown_dir: Optional[str] = None
    output_json_dir: Optional[str] = None
    debug: bool = False


class CVParser:
    """Public CV parsing interface."""

    def __init__(self, config: Optional[CVParsingConfig] = None):
        """
        Initialize the CV parser.
        
        Args:
            config: CVParsingConfig instance
        """
        self.config = config or CVParsingConfig()
        
        # Initialize the processing pipeline
        pipeline_cfg = PipelineConfig(
            use_llm=self.config.use_llm_extraction,
            llm_model=self.config.llm_model,
            llm_base_url=self.config.llm_base_url,
            llm_timeout=self.config.llm_timeout,
            output_markdown_dir=self.config.output_markdown_dir,
            output_json_dir=self.config.output_json_dir,
            debug=self.config.debug,
        )
        self.pipeline = CVProcessingPipeline(config=pipeline_cfg)

    def parse_cv(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse a CV PDF file end-to-end.

        Flow:
        1. STEP 1-4: Extract geometric structure via PDFExtractor
        2. STEP 5: Extract structured data via HRExtractorAgent (LLM-based)
        3. STEP 6: Enrich with computed values via PostProcessor

        Args:
            pdf_path (str): Path to PDF file

        Returns:
            Dict with parsing results:
            {
                'success': bool,
                'filename': str,
                'extraction_method': str,
                'cleaned_text': str,
                'extracted_profile': Dict or None,
                'total_years_experience': float,
                'seniority_level': str or None,
                'markdown': str (intermediate markdown dump),
                'errors': List[str],
                'metadata': Dict
            }
        """
        result_dict = {
            "success": False,
            "filename": os.path.basename(pdf_path),
            "extraction_method": "geometric_pipeline",
            "cleaned_text": "",
            "extracted_profile": None,
            "total_years_experience": 0.0,
            "seniority_level": None,
            "markdown": "",
            "errors": [],
            "metadata": {
                "pdf_path": pdf_path,
                "file_size": 0,  # Will be set after validation
                "pipeline": "Clean Architecture (PDFExtractor → HRExtractorAgent → PostProcessor)",
            },
        }

        try:
            logger.info(f"[CVParser] Starting: {pdf_path}")

            # File validation
            if not os.path.exists(pdf_path):
                error_msg = f"File not found: {pdf_path}"
                result_dict["errors"].append(error_msg)
                logger.error(f"[CVParser] {error_msg}")
                return result_dict

            # Run the pipeline
            logger.info(f"[CVParser] Running pipeline...")
            pipeline_result: ProcessingResult = self.pipeline.process_pdf(pdf_path)

            # Copy results from pipeline
            result_dict["success"] = pipeline_result.success
            result_dict["cleaned_text"] = pipeline_result.ordered_text
            result_dict["extracted_profile"] = pipeline_result.extracted_profile
            result_dict["total_years_experience"] = pipeline_result.total_years_experience
            result_dict["seniority_level"] = pipeline_result.seniority_level
            result_dict["markdown"] = pipeline_result.intermediate_markdown
            result_dict["metadata"]["total_pages"] = pipeline_result.total_pages
            result_dict["metadata"]["extraction_status"] = pipeline_result.metadata.get("extraction_status", "unknown")
            result_dict["metadata"]["file_size"] = os.path.getsize(pdf_path)
            
            if pipeline_result.error:
                result_dict["errors"].append(pipeline_result.error)
                logger.error(f"[CVParser] Pipeline error: {pipeline_result.error}")
                return result_dict

            logger.info(
                f"[CVParser] Success: "
                f"{pipeline_result.total_pages} pages, "
                f"{pipeline_result.total_years_experience} years exp, "
                f"{pipeline_result.seniority_level} seniority"
            )

        except Exception as e:
            logger.error(f"[CVParser] Unexpected error: {e}", exc_info=True)
            result_dict["errors"].append(f"Parsing error: {str(e)}")

        return result_dict

    def parse_batch(
        self,
        pdf_dir: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Parse multiple CV PDFs in a directory.

        Args:
            pdf_dir (str): Directory containing PDF files
            output_dir (str): Optional output directory for results

        Returns:
            Dict[filename] → parse_cv result
        """
        results = {}
        pdf_files = list(Path(pdf_dir).glob("*.pdf"))

        logger.info(f"[CVParser] Batch: Starting {len(pdf_files)} files")

        for pdf_file in pdf_files:
            logger.info(f"[CVParser] Batch: {pdf_file.name}")
            result = self.parse_cv(str(pdf_file))
            results[pdf_file.name] = result

            # Save individual results if output_dir specified
            if output_dir and result["success"]:
                output_path = os.path.join(output_dir, f"{pdf_file.stem}_result.json")
                os.makedirs(output_dir, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

        logger.info(f"[CVParser] Batch: Complete {len(results)} files")
        
        return results

    