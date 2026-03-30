"""
CV Version Models

Models for CV version tracking and management in the CV Intelligence Platform.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from src.models.domain.candidate import CandidateProfile
from src.models.validation.enums import SourceLanguage, TranslationStatus, SourceType


class ParsingMetadata(BaseModel):
    """Metadata about CV parsing process"""
    parser_version: str = Field(..., description="Version of parser used")
    extraction_method: str = Field(..., description="PDF extraction method")
    confidence_score: float = Field(default=0.0, ge=0, le=1, description="Overall extraction confidence")
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Parsing timestamp")
    raw_text_length: int = Field(default=0, description="Length of raw extracted text")
    source_language: str = Field(default="en", description="Detected source language")
    translation_required: bool = Field(default=False, description="Was translation needed")
    extraction_errors: List[str] = Field(default_factory=list, description="Any extraction errors")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    
    class Config:
        frozen = False


class CVVersion(BaseModel):
    """CV version for tracking"""
    version: str = Field(..., description="Version identifier")
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Extraction timestamp")
    source_type: SourceType = Field(..., description="Source document type")
    raw_text: Optional[str] = Field(None, description="Raw extracted text")
    normalized_text: Optional[str] = Field(None, description="Normalized markdown text")
    profile: Optional['CandidateProfile'] = Field(None, description="Parsed candidate profile")
    language: Optional[SourceLanguage] = Field(None, description="Detected language (vi/en)")
    translation_status: TranslationStatus = Field(
        default="pending", description="Translation status"
    )
    extraction_confidence: float = Field(default=0.0, ge=0, le=1, description="Extraction confidence score")

    class Config:
        frozen = False