"""
Candidate Profile Models

Enhanced Pydantic schemas for candidate data with normalization, validation, and matching.
Comprehensive ATS-standard data models for candidate profiles.
"""

from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
import re

# Import enums and validators from our validation module
from src.models.validation.enums import CEFRLEVEL, SeniorityLevel, RiskFlagType, RiskLevel
from src.models.validation.validators import PhoneValidator, DateValidator


# ============================================================================
# LOCATION & CONTACT
# ============================================================================

class LocationFormat(BaseModel):
    """Structured location"""
    city: Optional[str] = Field(None, description="City name")
    country: Optional[str] = Field(None, description="Country name")
    country_code: Optional[str] = Field(None, description="ISO country code (VN, US, etc)")
    remote_eligible: bool = Field(default=False, description="Can work remotely")
    
    class Config:
        frozen = False
    
    def __str__(self) -> str:
        """Display location"""
        parts = []
        if self.city:
            parts.append(self.city)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts) if parts else "Unknown"


class ContactInfo(BaseModel):
    """Enhanced contact information with E.164 phone normalization"""
    name: Optional[str] = Field(None, description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number (E.164 format)")
    location: Optional[LocationFormat] = Field(None, description="Structured location")
    linkedin: Optional[str] = Field(None, description="LinkedIn URL")
    github: Optional[str] = Field(None, description="GitHub profile")
    portfolio: Optional[str] = Field(None, description="Portfolio website")
    
    class Config:
        frozen = False
    
    @field_validator('phone')
    def normalize_phone(cls, v):
        """Normalize phone to E.164 format"""
        if not v:
            return None
        normalized = PhoneValidator.normalize_e164(v)
        if not normalized:
            raise ValueError(f"Invalid phone number format: {v}")
        return normalized


# ============================================================================
# CERTIFICATIONS & LANGUAGES
# ============================================================================

class Certification(BaseModel):
    """Structured certification"""
    name: str = Field(..., description="Certification name")
    issuer: str = Field(..., description="Issuing organization")
    issue_date: Optional[str] = Field(None, description="Issue date (YYYY-MM)")
    expiry_date: Optional[str] = Field(None, description="Expiry date (YYYY-MM), None if non-expiring")
    credential_id: Optional[str] = Field(None, description="Credential ID or certificate URL")
    is_current: bool = Field(default=True, description="Is certification still valid")
    confidence: float = Field(default=0.7, ge=0, le=1, description="Extraction confidence")
    
    class Config:
        frozen = False
    
    @field_validator('issue_date')
    def normalize_issue_date(cls, v):
        """Normalize date to YYYY-MM format"""
        if not v:
            return None
        normalized = DateValidator.normalize_date(v)
        if not normalized:
            raise ValueError(f"Invalid date format: {v}")
        return normalized
    
    @field_validator('expiry_date')
    def normalize_expiry_date(cls, v):
        """Normalize date to YYYY-MM format"""
        if not v:
            return None
        normalized = DateValidator.normalize_date(v)
        if not normalized and v.lower() not in ['never', 'non-expiring']:
            raise ValueError(f"Invalid date format: {v}")
        return normalized
    
    @model_validator(mode='before')
    def check_date_order(cls, values):
        """Ensure issue_date <= expiry_date"""
        if isinstance(values, dict):
            issue = values.get('issue_date')
            expiry = values.get('expiry_date')
            
            if issue and expiry:
                if issue > expiry:
                    raise ValueError("Issue date cannot be after expiry date")
        
        return values


class Language(BaseModel):
    """Structured language proficiency"""
    name: str = Field(..., description="Language name (English, Vietnamese, etc)")
    cefr_level: CEFRLEVEL = Field(..., description="CEFR level (A1-C2, NATIVE)")
    native: bool = Field(default=False, description="Is native language")
    confidence: float = Field(default=0.6, ge=0, le=1, description="Extraction confidence")
    
    class Config:
        frozen = False


# ============================================================================
# SKILLS & EVIDENCE
# ============================================================================

class SkillEvidence(BaseModel):
    """Evidence for a skill"""
    skill_name: str = Field(..., description="Skill name from evidence")
    context: str = Field(..., description="Where skill was used (project/role)")
    evidence_text: str = Field(..., description="Quote or explanation from CV")
    metrics: List[str] = Field(default_factory=list, description="Metrics/outcomes")
    confidence: float = Field(default=0.8, ge=0, le=1, description="Confidence in evidence")
    
    class Config:
        frozen = False


class Skill(BaseModel):
    """Enhanced skill with normalization and confidence tracking"""
    name: str = Field(..., description="Skill name as extracted from CV")
    normalized_name: Optional[str] = Field(None, description="Normalized skill name (lowercase, standardized)")
    level: Optional[SeniorityLevel] = Field(default=SeniorityLevel.MID, description="Proficiency level")
    years_experience: float = Field(default=0, ge=0, description="Years of experience")
    evidence: List[SkillEvidence] = Field(default_factory=list, description="Evidence where used")
    confidence: float = Field(default=0.7, ge=0, le=1, description="Overall confidence in skill")
    last_used: Optional[str] = Field(None, description="When skill was last used (YYYY-MM)")
    frequency: int = Field(default=1, ge=1, description="How many times mentioned")
    
    class Config:
        frozen = False
    
    @model_validator(mode='before')
    def normalize_skill_name(cls, values):
        """Auto-normalize skill name if not provided"""
        if isinstance(values, dict):
            v = values.get('normalized_name')
            name = values.get('name')
            
            if v:
                values['normalized_name'] = v.lower().strip()
            elif name:
                # Simple normalization: lowercase, remove versions
                normalized = re.sub(r'[\s\d\.\+\-#]', '', name.lower())
                normalized = re.sub(r'(\.js|\.net|\.io|3\.0)', '', normalized)
                values['normalized_name'] = normalized
        
        return values


# ============================================================================
# PROJECTS & EXPERIENCE
# ============================================================================

class Project(BaseModel):
    """Project with evidence and metrics"""
    name: str = Field(..., description="Project/product name")
    role: str = Field(..., description="Role in project")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM)")
    duration_months: int = Field(default=0, ge=0, description="Duration in months (auto-computed)")
    description: Optional[str] = Field(None, description="Project description")
    tech_stack: List[str] = Field(default_factory=list, description="Technologies used")
    skills_used: List[str] = Field(default_factory=list, description="Skills applied")
    contributions: List[str] = Field(default_factory=list, description="Key contributions")
    metrics: List[str] = Field(default_factory=list, description="Quantifiable outcomes")
    ownership: Literal["owned", "led", "contributed", "supported"] = Field(
        default="contributed", description="Level of ownership"
    )
    complexity_score: int = Field(default=3, ge=1, le=5, description="Technical complexity")
    impact_score: int = Field(default=3, ge=1, le=5, description="Business impact")
    evidence_strength: float = Field(default=0.6, ge=0, le=1, description="Confidence in details")
    
    class Config:
        frozen = False
    
    @model_validator(mode='before')
    def compute_duration(cls, values):
        """Auto-compute duration_months from dates"""
        if isinstance(values, dict):
            start_date = values.get('start_date')
            end_date = values.get('end_date')
            
            if start_date:
                duration = DateValidator.compute_months(start_date, end_date)
                values['duration_months'] = duration
        
        return values


class CareerProgression(BaseModel):
    """Experience entry with skills and impact tracking"""
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    start_date: str = Field(..., description="Start date (YYYY-MM)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM), None if current")
    duration_months: int = Field(default=0, ge=0, description="Duration in months (auto-computed)")
    is_current: bool = Field(default=False, description="Is this current role")
    description: Optional[str] = Field(None, description="Role description")
    skills_used: List[str] = Field(default_factory=list, description="Skills used in this role")
    achievements: List[str] = Field(default_factory=list, description="Key achievements")
    impact_score: int = Field(default=3, ge=1, le=5, description="Business impact")
    evidence_strength: float = Field(default=0.6, ge=0, le=1, description="Confidence in details")
    
    class Config:
        frozen = False
    
    @model_validator(mode='before')
    def compute_duration_and_current(cls, values):
        """Auto-compute duration and is_current"""
        if isinstance(values, dict):
            start_date = values.get('start_date')
            end_date = values.get('end_date')
            
            if start_date:
                duration = DateValidator.compute_months(start_date, end_date)
                values['duration_months'] = duration
                values['is_current'] = end_date is None
        
        return values


class Education(BaseModel):
    """Enhanced education with degree hierarchy"""
    institution: str = Field(..., description="School/university name")
    degree: str = Field(..., description="Degree obtained")
    field_of_study: Optional[str] = Field(None, description="Field of study")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM)")
    gpa: Optional[float] = Field(None, ge=0, le=4, description="GPA (0-4 scale)")
    honors: Optional[str] = Field(None, description="Honors (cum laude, magna cum laude, etc)")
    description: Optional[str] = Field(None, description="Additional details")
    
    class Config:
        frozen = False


# ============================================================================
# DERIVED FIELDS & METADATA
# ============================================================================

class DerivedFields(BaseModel):
    """Auto-computed derived fields for ML and matching"""
    total_experience_months: int = Field(default=0, description="Total career months")
    seniority: SeniorityLevel = Field(default=SeniorityLevel.MID, description="Auto-computed seniority")
    skill_count: int = Field(default=0, description="Number of unique skills")
    skill_vector: Optional[Dict[str, float]] = Field(None, description="Skill confidence scores for embeddings")
    avg_project_impact: float = Field(default=0, ge=0, le=1, description="Average project impact score")
    current_role: Optional[str] = Field(None, description="Current job title")
    years_in_current_role: float = Field(default=0, description="Years in current role")
    education_level: Optional[str] = Field(None, description="Highest education level")
    languages_spoken: int = Field(default=0, description="Number of languages")
    certifications_count: int = Field(default=0, description="Number of certifications")
    
    class Config:
        frozen = False
    
    @staticmethod
    def compute_seniority(total_months: int) -> SeniorityLevel:
        """Compute seniority from total experience months"""
        years = total_months / 12
        if years < 2:
            return SeniorityLevel.JUNIOR
        elif years < 5:
            return SeniorityLevel.MID
        elif years < 10:
            return SeniorityLevel.SENIOR
        elif years < 15:
            return SeniorityLevel.LEAD
        else:
            return SeniorityLevel.PRINCIPAL


class ParsingMetadata(BaseModel):
    """Metadata about CV parsing process"""
    parser_version: str = Field(..., description="Version of parser used")
    extraction_method: str = Field(..., description="PDF extraction method")
    confidence_score: float = Field(default=0.0, ge=0, le=1, description="Overall extraction confidence")
    parsed_at: datetime = Field(default_factory=datetime.utcnow, description="Parsing timestamp")
    raw_text_length: int = Field(default=0, description="Length of raw extracted text")
    source_language: str = Field(default="en", description="Detected source language")
    translation_required: bool = Field(default=False, description="Was translation needed")
    extraction_errors: List[str] = Field(default_factory=list, description="Any extraction errors")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    
    class Config:
        frozen = False


# ============================================================================
# CANDIDATE PROFILE
# ============================================================================

class CandidateProfile(BaseModel):
    """Enhanced candidate profile with all structured data"""
    contact: ContactInfo = Field(default_factory=ContactInfo, description="Contact information")
    summary: Optional[str] = Field(None, description="Professional summary")
    skills: List[Skill] = Field(default_factory=list, description="Skills with normalization")
    experience: List[CareerProgression] = Field(default_factory=list, description="Work experience")
    projects: List[Project] = Field(default_factory=list, description="Projects with metrics")
    education: List[Education] = Field(default_factory=list, description="Education history")
    certifications: List[Certification] = Field(default_factory=list, description="Structured certifications")
    languages: List[Language] = Field(default_factory=list, description="Structured languages")
    risk_flags: List['RiskFlag'] = Field(default_factory=list, description="Risk flags")
    derived_fields: Optional[DerivedFields] = Field(None, description="Auto-computed fields")
    parsing_metadata: Optional[ParsingMetadata] = Field(None, description="Parsing process metadata")
    
    class Config:
        frozen = False
    
    def compute_derived_fields(self) -> DerivedFields:
        """Compute all derived fields"""
        total_months = sum(exp.duration_months for exp in self.experience)
        seniority = DerivedFields.compute_seniority(total_months)
        
        # Skill vector: {normalized_name: max_confidence}
        skill_vector = {}
        for skill in self.skills:
            normalized = skill.normalized_name or skill.name.lower()
            skill_vector[normalized] = max(
                skill_vector.get(normalized, 0),
                skill.confidence
            )
        
        # Current role
        current_exp = next((e for e in self.experience if e.is_current), None)
        current_role = current_exp.title if current_exp else None
        years_in_current = (current_exp.duration_months / 12) if current_exp else 0
        
        # Average project impact
        avg_impact = (
            sum(p.impact_score for p in self.projects) / len(self.projects)
            if self.projects else 0
        ) / 5.0  # Normalize to 0-1
        
        # Education level
        degree_levels = {
            'high school': 1, 'bachelor': 3, 'master': 4, 'phd': 5, 'doctorate': 5
        }
        education_level = None
        if self.education:
            level = max(
                (degree_levels.get(e.degree.lower(), 0), e.degree)
                for e in self.education
            )
            education_level = level[1]
        
        return DerivedFields(
            total_experience_months=total_months,
            seniority=seniority,
            skill_count=len(self.skills),
            skill_vector=skill_vector,
            avg_project_impact=avg_impact,
            current_role=current_role,
            years_in_current_role=years_in_current,
            education_level=education_level,
            languages_spoken=len(self.languages),
            certifications_count=len(self.certifications)
        )


class RiskFlag(BaseModel):
    """Risk flag with details"""
    flag_type: RiskFlagType = Field(..., description="Type of risk")
    severity: RiskLevel = Field(..., description="Severity level")
    description: str = Field(..., description="Description of the risk")
    evidence: Optional[str] = Field(None, description="Evidence for the flag")
    field_name: Optional[str] = Field(None, description="Which field has the risk")
    remediation: Optional[str] = Field(None, description="How to remediate")
    
    class Config:
        frozen = False


# Update forward references for RiskFlag
CandidateProfile.model_rebuild()
