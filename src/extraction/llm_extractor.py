"""
Enhanced LLM Extraction Module

Uses local Ollama models (Qwen2.5-coder) for structured JSON extraction with enhanced schemas.
Falls back to heuristics if LLM is unavailable.
"""

import json
import logging
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass

from src.models.domain.candidate import (
    CandidateProfile,
    ContactInfo,
    Skill,
    CareerProgression,
    Project,
    Education,
    Certification,
    Language,
    SkillEvidence,
    LocationFormat,
    CEFRLEVEL,
)
from src.models.domain.project import LLMProject
from src.models.domain.project_validator import ProjectValidator
from src.models.validation.enums import ExtractionMethod
from src.models.domain.cv_version import ParsingMetadata


logger = logging.getLogger(__name__)


@dataclass
class LLMExtractionConfig:
    """Configuration for LLM extraction."""
    model_name: str = "qwen2.5-coder:3b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.1  # Low temperature for deterministic extraction
    timeout: int = 30
    use_fallback: bool = True  # Fall back to regex if LLM fails
    parser_version: str = "1.0"
    extraction_method: ExtractionMethod = ExtractionMethod.PYMUPDF


class OllamaClient:
    """Wrapper for Ollama API calls with robust error handling and fallback strategy."""

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags", timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False

    def extract_json(
        self,
        prompt: str,
        model: str = "qwen2.5-coder:3b",
        temperature: float = 0.1,
        raw_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call Ollama to extract JSON from text with fallback strategy.

        Args:
            prompt: Prompt with extraction task
            model: Model name to use
            temperature: Sampling temperature
            raw_text: Original text for fallback if JSON is invalid

        Returns:
            Dict with status='success' and JSON data, or status='partial' with raw_text
        """
        if not self.available:
            logger.warning("Ollama not available, returning partial fallback")
            return self._create_fallback_response(raw_text or "")

        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
                "format": "json",
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")

                # Extract JSON from response
                try:
                    # Try direct JSON parsing
                    extracted_json = json.loads(response_text)
                    return {
                        "status": "success",
                        "data": extracted_json,
                        "method": "llm_full",
                    }
                except json.JSONDecodeError:
                    # Try to extract JSON block from text
                    import re

                    match = re.search(r"\{.*\}", response_text, re.DOTALL)
                    if match:
                        try:
                            extracted_json = json.loads(match.group())
                            return {
                                "status": "success",
                                "data": extracted_json,
                                "method": "llm_parsed",
                            }
                        except json.JSONDecodeError:
                            logger.warning(
                                f"Failed to parse JSON from LLM response: {response_text[:100]}"
                            )
                            # Fallback to partial with raw text
                            return self._create_fallback_response(raw_text or response_text)
                    
                    # Fallback to partial with raw text
                    return self._create_fallback_response(raw_text or response_text)
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return self._create_fallback_response(raw_text or "")

        except requests.Timeout:
            logger.error(f"LLM extraction timeout after {self.timeout}s, using fallback")
            return self._create_fallback_response(raw_text or "")
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}, using fallback")
            return self._create_fallback_response(raw_text or "")

    def _create_fallback_response(self, raw_text: str) -> Dict[str, Any]:
        """Create fallback response when LLM fails or times out."""
        return {
            "status": "partial",
            "method": "fallback",
            "raw_text": raw_text,
            "data": None,
            "error": "LLM extraction failed or unavailable"
        }


class EnhancedLLMExtractor:
    """Extracts structured data from CV using LLM with enhanced schemas."""

    EXTRACTION_PROMPT = """Extract structured information from the following CV text.
Return valid JSON with the following structure (use null for missing fields):

{{
    "contact": {{
        "name": "Full Name",
        "email": "email@example.com",
        "phone": "E.164 format or null",
        "location": {{
            "city": "City Name",
            "country": "Country Name",
            "country_code": "VN|US|etc",
            "remote_eligible": true|false
        }},
        "linkedin": "URL or null",
        "github": "URL or null",
        "portfolio": "URL or null"
    }},
    "summary": "Professional summary or null",
    "skills": [
        {{
            "name": "Original skill name",
            "normalized_name": "normalized_name (auto-generated)",
            "years_experience": 3.5,
            "level": "junior|mid|senior|lead|principal",
            "confidence": 0.85,
            "last_used": "YYYY-MM or null",
            "frequency": 2,
            "evidence": [
                {{
                    "skill_name": "Skill mentioned",
                    "context": "Project or role name",
                    "evidence_text": "Direct quote from CV",
                    "metrics": ["Quantifiable outcome"],
                    "confidence": 0.9
                }}
            ]
        }}
    ],
    "experience": [
        {{
            "company": "Company Name",
            "title": "Job Title",
            "start_date": "YYYY-MM",
            "end_date": "YYYY-MM or null if current",
            "is_current": false,
            "description": "Role description",
            "skills_used": ["skill1", "skill2"],
            "achievements": ["Achievement 1"],
            "impact_score": 4,
            "evidence_strength": 0.65
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "company": "Company or organization name",
            "role": "Role in project",
            "start_date": "YYYY-MM",
            "end_date": "YYYY-MM",
            "description": "What the project was about",
            "tech_stack": ["tech1", "tech2"],
            "skills_used": ["skill1"],
            "contributions": ["Contribution 1"],
            "metrics": ["Metric 1: 50% improvement"],
            "ownership": "led|owned|contributed|supported",
            "complexity_score": 4,
            "impact_score": 4,
            "evidence_strength": 0.7
        }}
    ],
    "education": [
        {{
            "institution": "University Name",
            "degree": "Bachelor|Master|PhD",
            "field_of_study": "Computer Science",
            "start_date": "YYYY-MM or null",
            "end_date": "YYYY-MM or null",
            "gpa": 3.8 or null,
            "honors": "Cum Laude or null",
            "description": "Additional details or null"
        }}
    ],
    "certifications": [
        {{
            "name": "Certification Name",
            "issuer": "AWS|Google|etc",
            "issue_date": "YYYY-MM",
            "expiry_date": "YYYY-MM or null",
            "credential_id": "Credential ID or URL or null",
            "is_current": true,
            "confidence": 0.8
        }}
    ],
    "languages": [
        {{
            "name": "Language Name",
            "cefr_level": "A1|A2|B1|B2|C1|C2|NATIVE|FLUENT",
            "native": false,
            "confidence": 0.75
        }}
    ]
}}

CRITICAL REQUIREMENTS:
1. Extract ALL information accurately from the CV text
2. Return ONLY valid JSON - no explanations or markdown
3. Follow the schema structure exactly
4. Handle multi-language content (Vietnamese, English, etc.)
5. Normalize data:
   - Phone to E.164 format (e.g., +84912345678, +12025551234)
   - Dates to YYYY-MM format (e.g., 2024-01 for January 2024)
   - Skill names to lowercase (e.g., "Python 3" → "python", "React.js" → "react")
6. Preserve evidence with confidence scores
7. Calculate metrics and impact scores where possible
8. Provide confidence_score for each extraction (0-1)

GUIDELINES:
- Dates: Transform any format to YYYY-MM (e.g., "Jan 2024" → "2024-01", "2024年1月" → "2024-01")
- Phone: Include country code (+84 for Vietnam, +1 for US, etc.). Handle variations like "091" → "+84"
- Skills: Extract all technical and soft skills. Provide normalized versions (lowercase, no special chars)
- Experience: list in reverse chronological order (most recent first)
- Confidence: Score based on how clear/explicit the information was in the CV (0-1)
- Missing fields: Use null, not empty strings or 0
- If duration or is_current not specified: Try to infer from dates

LANGUAGE HANDLING:
- Detect CV language automatically
- Process bilingual CVs intelligently
- Map foreign language skill names to English equivalents where possible

CV TEXT:
{cv_text}

Return ONLY valid JSON following the schema provided. No explanations."""

    def __init__(self, config: Optional[LLMExtractionConfig] = None):
        self.config = config or LLMExtractionConfig()
        self.client = OllamaClient(self.config.base_url, self.config.timeout)

    def extract(self, cv_markdown: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract structured data from markdown CV using enhanced schemas.
        Supports fallback when LLM unavailable or extraction fails.

        Args:
            cv_markdown: Plain ordered text from CV (with # headers and markdown tables)
            language: Detected language code (vi, en, etc)

        Returns:
            Dict with status='success' (data extracted), 'partial' (raw_text + fallback),
            or 'error' (no data extracted)
        """
        prompt = self.EXTRACTION_PROMPT.replace("{cv_text}", cv_markdown)

        logger.info(f"Extracting with model: {self.config.model_name}")

        # Call LLM with fallback strategy built-in
        llm_result = self.client.extract_json(
            prompt=prompt,
            model=self.config.model_name,
            temperature=self.config.temperature,
            raw_text=cv_markdown,  # Pass raw text for fallback
        )

        # Handle result (either success with JSON or partial with raw_text)
        if llm_result.get("status") == "success":
            extracted_data = llm_result.get("data", {})
            try:
                profile = self._build_and_validate_profile(extracted_data, language)
                return {
                    "status": "success",
                    "data": profile,
                    "method": llm_result.get("method", "llm"),
                    "fallback": False
                }
            except Exception as e:
                logger.error(f"Profile validation failed: {e}")
                # Return partial response with raw_text for fallback processing
                return {
                    "status": "partial",
                    "data": None,
                    "raw_text": cv_markdown,
                    "method": "fallback",
                    "fallback": True,
                    "error": f"Validation failed: {str(e)}"
                }

        elif llm_result.get("status") == "partial":
            # LLM failed or returned invalid JSON, return raw_text for post-processing
            logger.warning(f"LLM extraction partial: {llm_result.get('error')}")
            return {
                "status": "partial",
                "data": None,
                "raw_text": llm_result.get("raw_text", cv_markdown),
                "method": "fallback",
                "fallback": True,
                "error": llm_result.get("error", "Unknown error")
            }

        else:
            # Unknown status, return error
            return {
                "status": "error",
                "data": None,
                "method": "none",
                "fallback": False,
                "error": "Unknown extraction status"
            }

    def _build_and_validate_profile(self, data: Dict[str, Any], language: Optional[str]) -> CandidateProfile:
        """Build and validate CandidateProfile from extracted data"""
        # Normalize contact info
        contact_data = data.get("contact", {})
        contact = self._normalize_contact(contact_data)
        
        # Normalize skills
        skills = [self._normalize_skill(s) for s in data.get("skills", [])]
        
        # Normalize experience
        experience = [
            self._normalize_experience(e) 
            for e in data.get("experience", [])
        ]
        
        # Normalize projects
        projects = [
            self._normalize_project(p) 
            for p in data.get("projects", [])
        ]
        
        # Normalize education
        education = [
            self._normalize_education(e) 
            for e in data.get("education", [])
        ]
        
        # Normalize certifications
        certifications = [
            self._normalize_certification(c) 
            for c in data.get("certifications", [])
        ]
        
        # Normalize languages
        languages = [
            self._normalize_language(l) 
            for l in data.get("languages", [])
        ]
        
        # Create and validate profile
        profile = CandidateProfile(
            contact=contact,
            summary=data.get("summary"),
            skills=skills,
            experience=experience,
            projects=projects,
            education=education,
            certifications=certifications,
            languages=languages
        )
        
        # Compute derived fields
        profile.derived_fields = profile.compute_derived_fields()
        
        # Create metadata
        profile.parsing_metadata = ParsingMetadata(
            parser_version=self.config.parser_version,
            extraction_method=self.config.extraction_method,
            confidence_score=self._compute_overall_confidence(data),
            source_language=language or "en",
            translation_required=False  # Assume already translated if needed
        )
        
        return profile

    def _normalize_contact(self, data: Dict) -> ContactInfo:
        """Normalize contact information"""
        location_data = data.get("location")
        location = None
        if location_data:
            location = LocationFormat(
                city=location_data.get("city"),
                country=location_data.get("country"),
                country_code=location_data.get("country_code"),
                remote_eligible=location_data.get("remote_eligible", False)
            )
        
        return ContactInfo(
            name=data.get("name"),
            email=data.get("email"),
            phone=data.get("phone"),  # E.164 normalization happens in validator
            location=location,
            linkedin=data.get("linkedin"),
            github=data.get("github"),
            portfolio=data.get("portfolio")
        )

    def _normalize_skill(self, data: Dict) -> Skill:
        """Normalize skill data"""
        evidence_list = []
        for ev in data.get("evidence", []):
            evidence_list.append(
                SkillEvidence(
                    skill_name=ev.get("skill_name", ""),
                    context=ev.get("context", ""),
                    evidence_text=ev.get("evidence_text", ""),
                    metrics=ev.get("metrics", []),
                    confidence=ev.get("confidence", 0.7)
                )
            )
        
        return Skill(
            name=data.get("name", "Unknown"),
            normalized_name=data.get("normalized_name"),
            years_experience=data.get("years_experience", 0),
            level=data.get("level", "mid"),
            confidence=data.get("confidence", 0.7),
            last_used=data.get("last_used"),
            frequency=data.get("frequency", 1),
            evidence=evidence_list
        )

    def _normalize_experience(self, data: Dict) -> CareerProgression:
        """Normalize experience data"""
        start_date = data.get("start_date")
        if not start_date:
            logger.warning(f"Missing start_date for experience at {data.get('company', 'Unknown')}")
        
        return CareerProgression(
            company=data.get("company", "Unknown"),
            title=data.get("title", "Unknown"),
            start_date=start_date,  # Let domain model handle None appropriately
            end_date=data.get("end_date"),
            description=data.get("description"),
            skills_used=data.get("skills_used", []),
            achievements=data.get("achievements", []),
            impact_score=data.get("impact_score", 3),
            evidence_strength=data.get("evidence_strength", 0.5)
        )
    def _normalize_project(self, data: Dict) -> Project:
        """Normalize project data"""
        # Try to create LLMProject first for enhanced validation
        try:
            llm_project = LLMProject(
                name=data.get("name", "Unknown"),
                company=data.get("company", "Unknown"),
                description=data.get("description", ""),
                technologies=data.get("tech_stack", []),
                metrics=data.get("metrics", []),
                role=data.get("role", "Team member"),
                complexity_level=data.get("complexity_level", "medium"),
                ownership=data.get("ownership", "contributed"),
                confidence=data.get("confidence", 0.75),
                extraction_method="llm"
            )
            
            # Validate the project
            validator = ProjectValidator()
            validation_result = validator.validate_project(llm_project)
            
            if validation_result.is_valid:
                # Convert LLMProject to Project
                return Project(
                    name=llm_project.name,
                    role=llm_project.role,
                    start_date=data.get("start_date"),
                    end_date=data.get("end_date"),
                    description=llm_project.description,
                    tech_stack=llm_project.technologies,
                    skills_used=data.get("skills_used", []),
                    contributions=data.get("contributions", []),
                    metrics=llm_project.metrics,
                    ownership=llm_project.ownership,
                    complexity_score=llm_project.get_complexity_score(),
                    impact_score=data.get("impact_score", 3),
                    evidence_strength=validation_result.confidence
                )
            else:
                logger.warning(f"Project validation failed: {validation_result.errors}")
        except Exception as e:
            logger.warning(f"Failed to create LLMProject: {e}")
        
        # Fallback to basic Project creation
        return Project(
            name=data.get("name", "Unknown"),
            role=data.get("role", "Team member"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            description=data.get("description", ""),
            tech_stack=data.get("tech_stack", []),
            skills_used=data.get("skills_used", []),
            contributions=data.get("contributions", []),
            metrics=data.get("metrics", []),
            ownership=data.get("ownership", "contributed"),
            complexity_score=data.get("complexity_score", 3),
            impact_score=data.get("impact_score", 3),
            evidence_strength=data.get("evidence_strength", 0.5)
        )

    def _normalize_education(self, data: Dict) -> Education:
        """Normalize education data"""
        return Education(
            institution=data.get("institution", "Unknown"),
            degree=data.get("degree", "Unknown"),
            field_of_study=data.get("field_of_study"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            gpa=data.get("gpa"),
            honors=data.get("honors"),
            description=data.get("description")
        )

    def _normalize_certification(self, data: Dict) -> Certification:
        """Normalize certification data"""
        return Certification(
            name=data.get("name", "Unknown"),
            issuer=data.get("issuer", "Unknown"),
            issue_date=data.get("issue_date"),
            expiry_date=data.get("expiry_date"),
            credential_id=data.get("credential_id"),
            is_current=data.get("is_current", True),
            confidence=data.get("confidence", 0.7)
        )

    def _normalize_language(self, data: Dict) -> Language:
        """Normalize language data.
        
        Converts CEFR level from string to enum with proper error handling.
        """
        cefr_str = data.get("cefr_level", "B1")
        try:
            # Convert string to enum if necessary
            cefr_level = CEFRLEVEL(cefr_str) if isinstance(cefr_str, str) else cefr_str
        except ValueError:
            logger.warning(f"Invalid CEFR level '{cefr_str}', defaulting to B1")
            cefr_level = CEFRLEVEL.B1
        
        return Language(
            name=data.get("name", "Unknown"),
            cefr_level=cefr_level,
            native=data.get("native", False),
            confidence=data.get("confidence", 0.6)
        )

    @staticmethod
    def _compute_overall_confidence(data: Dict[str, Any]) -> float:
        """Compute overall extraction confidence (0-1)"""
        if not data:
            return 0.0
        
        scores = []
        
        # Contact info confidence
        contact = data.get("contact", {})
        if contact:
            contact_fields = sum([
                1 for v in contact.values() 
                if v and v not in ["", {}]
            ])
            scores.append(contact_fields / 7)  # 7 possible fields
        
        # Skills confidence
        skills = data.get("skills", [])
        if skills:
            skill_confidences = [s.get("confidence", 0.5) for s in skills]
            scores.append(sum(skill_confidences) / len(skill_confidences))
        
        # Experience confidence
        experience = data.get("experience", [])
        if experience:
            exp_confidences = [e.get("evidence_strength", 0.5) for e in experience]
            scores.append(sum(exp_confidences) / len(exp_confidences))
        
        # Average all scores
        return sum(scores) / len(scores) if scores else 0.5


# Backward compatibility alias
LLMExtractor = EnhancedLLMExtractor
