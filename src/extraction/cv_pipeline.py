"""
CV Processing Pipeline
Main orchestrator for CV extraction, normalization, translation, and storage
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from src.extraction.pdf import PDFExtractor
from src.extraction.markdown import HybridSectionExtractor
from src.translation import OllamaTranslator
from src.storage import CVStorage
from src.schemas import CVVersion, CandidateProfile


class CVProcessingPipeline:
    """Main pipeline for processing CVs"""

    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.markdown_extractor = HybridSectionExtractor()
        self.translator = OllamaTranslator()
        self.storage = CVStorage()

    def process(self, pdf_path: str, translate: bool = True) -> Dict[str, Any]:
        """Process a CV through the full pipeline"""
        cv_id = str(uuid.uuid4())
        version = f"v1_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        pdf_result = self.pdf_extractor.extract(pdf_path)
        if not pdf_result.is_success:
            return {
                "cv_id": cv_id,
                "success": False,
                "error": pdf_result.error,
            }

        raw_text = pdf_result.full_text

        normalized_text, metadata = self.markdown_extractor.normalize(raw_text)

        final_text = raw_text
        final_normalized = normalized_text
        translation_status = "pending"

        if translate and metadata.language_detected == "vi":
            translated = self.translator.translate(raw_text)
            if translated and translated != raw_text:
                final_text = translated
                translation_status = "completed"

        cv_version = CVVersion(
            version=version,
            source_type="pdf",
            raw_text=final_text,
            normalized_text=final_normalized,
            profile=None,
            language=metadata.language_detected,
            translation_status=translation_status,
            extraction_confidence=metadata.confidence,
        )

        self.storage.save_raw(cv_id, cv_version)

        if translation_status == "completed":
            cv_version.translation_status = translation_status
            self.storage.save_normalized(cv_id, cv_version)

        return {
            "cv_id": cv_id,
            "version": version,
            "success": True,
            "raw_text": final_text[:500],
            "normalized_text": final_normalized[:500],
            "language": metadata.language_detected,
            "confidence": metadata.confidence,
            "translation_status": translation_status,
            "sections_found": metadata.sections_found,
        }

    def process_file(self, file_path: str, translate: bool = True) -> Dict[str, Any]:
        """Process a single file"""
        return self.process(file_path, translate)

    def get_cv(self, cv_id: str) -> Optional[Dict[str, Any]]:
        """Get processed CV"""
        return self.storage.get_cv(cv_id, normalized=True)

    def search_by_skill(self, skill: str, limit: int = 10) -> list:
        """Search CVs by skill"""
        return self.storage.search_by_skill(skill, limit)


__all__ = ["CVProcessingPipeline"]
