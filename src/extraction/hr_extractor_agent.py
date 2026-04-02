"""
HR Extractor Agent - Clean Architecture Orchestrator

Simplified orchestrator following Clean Architecture principles:
1. extract_ordered_text() - Get plain ordered text from geometric engine
2. call_llm() - Extract structured data via LLM (with fallback strategy)
3. post_process() - Enrich with computed values (dates, experience, seniority)

No legacy rule-based extraction, no fuzzy matching, no keyword lists.
Trust LLM output, add value through computation only.
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass

from src.models.domain.candidate import CandidateProfile
from src.extraction.llm_extractor import EnhancedLLMExtractor, LLMExtractionConfig
from src.processing.post_processor import PostProcessor, ProcessingResult

logger = logging.getLogger(__name__)


@dataclass
class ExtractionConfig:
    """Configuration for CV extraction orchestrator"""
    llm_model: str = "qwen2.5-coder:3b"
    llm_base_url: str = "http://localhost:11434"
    llm_timeout: int = 30
    temperature: float = 0.1


class HRExtractorAgent:
    """
    Orchestrator for CV extraction pipeline.
    
    Clean separation of concerns:
    - PDFExtractor handles geometric layout analysis (Steps 1-4)
    - EnhancedLLMExtractor handles structured extraction with fallback (Step 5)
    - PostProcessor handles enrichment and computation
    """
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        """Initialize orchestrator with configuration"""
        self.config = config or ExtractionConfig()
        self.llm_extractor = EnhancedLLMExtractor(
            LLMExtractionConfig(
                model_name=self.config.llm_model,
                base_url=self.config.llm_base_url,
                timeout=self.config.llm_timeout,
                temperature=self.config.temperature,
            )
        )
        self.post_processor = PostProcessor()
    
    def extract_cv(self, cv_ordered_text: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Main extraction orchestration pipeline.
        
        Flow:
        1. extract_ordered_text() - Get plain ordered text from geometric engine
        2. call_llm() - Extract structured data via LLM with fallback
        3. post_process() - Enrich with computed values
        
        Args:
            cv_ordered_text: Plain ordered text from geometric engine (has # headers, markdown tables)
            language: Language code (vi, en, etc) - optional
            
        Returns:
            Dict with extraction results: status, profile, errors
        """
        if not cv_ordered_text or not cv_ordered_text.strip():
            logger.warning("Empty CV text provided")
            return {
                "status": "error",
                "profile": None,
                "total_years_experience": 0.0,
                "seniority_level": None,
                "errors": ["Empty CV text provided"]
            }
        
        try:
            # Step 1: Extract ordered text (already provided as input)
            logger.info("Step 1: Using provided ordered text from geometric engine")
            ordered_text = cv_ordered_text
            
            # Step 2: Call LLM for structured extraction with fallback
            logger.info("Step 2: Calling LLM extractor...")
            llm_result = self.call_llm(ordered_text, language)
            
            if not llm_result.get("success"):
                logger.warning(f"LLM extraction failed: {llm_result.get('error')}")
                return {
                    "status": "partial",
                    "profile": None,
                    "extraction_method": "fallback",
                    "raw_text": ordered_text,
                    "errors": [llm_result.get("error", "Unknown error")]
                }
            
            # Step 3: Post-process to enrich profile
            logger.info("Step 3: Post-processing...")
            profile = llm_result.get("profile")
            processing_result = self.post_process(profile)
            
            return {
                "status": "success",
                "profile": profile,
                "total_years_experience": processing_result.total_years_experience,
                "seniority_level": processing_result.seniority_level,
                "extraction_method": llm_result.get("method", "llm"),
                "errors": processing_result.errors
            }
        
        except Exception as e:
            logger.error(f"Orchestration error: {e}", exc_info=True)
            return {
                "status": "error",
                "profile": None,
                "errors": [str(e)]
            }
    
    def extract_ordered_text(self, cv_text: str) -> str:
        """
        Extract ordered text from CV.
        
        This method receives already-ordered text from geometric engine.
        In production, this integrates with PDFExtractor.extract().
        
        Args:
            cv_text: Plain text from PDF (already ordered by geometric pipeline)
            
        Returns:
            Ordered text with proper structure (# headers, markdown tables)
        """
        # In current architecture, this is already provided
        # This method exists for clarity and extensibility
        return cv_text
    
    def call_llm(self, ordered_text: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Call LLM extractor for structured data extraction.
        
        Handles:
        - LLM availability check
        - JSON extraction with fallback strategy
        - Validation of extracted profile
        
        Args:
            ordered_text: Plain ordered text (has # headers, markdown tables)
            language: Language code (vi, en, etc)
            
        Returns:
            Dict with:
            - success (bool)
            - profile (CandidateProfile if success)
            - method (llm_full, llm_parsed, fallback, none)
            - error (if not success)
        """
        logger.info(f"Calling LLM extractor with model: {self.config.llm_model}")
        
        try:
            # Call LLM with built-in fallback strategy
            extraction_result = self.llm_extractor.extract(ordered_text, language)
            
            # Check result status
            if extraction_result.get("status") == "success":
                profile = extraction_result.get("data")
                logger.info(f"LLM extraction successful (method: {extraction_result.get('method')})")
                return {
                    "success": True,
                    "profile": profile,
                    "method": extraction_result.get("method", "llm"),
                }
            
            elif extraction_result.get("status") == "partial":
                # LLM failed, fallback to partial extraction
                error = extraction_result.get("error", "LLM extraction failed")
                logger.warning(f"LLM fallback triggered: {error}")
                return {
                    "success": False,
                    "profile": None,
                    "method": "fallback",
                    "error": error,
                    "raw_text": extraction_result.get("raw_text")
                }
            
            else:
                # Unknown status
                return {
                    "success": False,
                    "profile": None,
                    "method": "none",
                    "error": "Unknown extraction status"
                }
        
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
            return {
                "success": False,
                "profile": None,
                "method": "none",
                "error": str(e)
            }
    
    def post_process(self, profile: Optional[CandidateProfile]) -> ProcessingResult:
        """
        Post-process extracted profile for enrichment.
        
        Handles:
        - Date normalization to ISO format
        - Total experience calculation
        - Seniority level assignment
        
        Args:
            profile: CandidateProfile from LLM extraction
            
        Returns:
            ProcessingResult with enriched profile and computed metadata
        """
        if not profile:
            return ProcessingResult(
                success=False,
                profile=None,
                errors=["No profile to post-process"]
            )
        
        logger.info("Post-processing profile...")
        
        try:
            result = self.post_processor.process(profile)
            logger.info(f"Post-processing complete: {result.total_years_experience}y experience, {result.seniority_level} level")
            return result
        
        except Exception as e:
            logger.error(f"Post-processing error: {e}")
            return ProcessingResult(
                success=False,
                profile=profile,
                errors=[str(e)]
            )
