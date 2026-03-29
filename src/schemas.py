"""
Enhanced Pydantic schemas for CV Intelligence Platform
Comprehensive ATS-standard data models with normalization, validation, and matching

Features:
- ✅ Structured certifications (issuer, dates, credential tracking)
- ✅ Structured languages (CEFR levels A1-C2)
- ✅ E.164 phone normalization
- ✅ Derived fields (total_experience_months, skill_vector, seniority)
- ✅ Metadata tracking (parser_version, extraction_method, confidence_score)
- ✅ Matching model with score components
- ✅ Enhanced validation constraints
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime, date
from enum import Enum
import re
from typing import Callable


# ============================================================================

# ENUMERATIONS

# ============================================================================

class CEFRLEVEL(str, Enum):
    """Common European Framework of Reference Language Levels"""
    A1 = "A1"  # Beginner
    A2 = "A2"  # Elementary
    B1 = "B1"  # Intermediate
    B2 = "B2"  # Upper-intermediate
    C1 = "C1"  # Advanced
    C2 = "C2"  # Mastery
    NATIVE = "NATIVE"  # Native speaker
    FLUENT = "FLUENT"  # Fluent (maps to C1-C2)


class SeniorityLevel(str, Enum):
    """Candidate/Role seniority levels"""
    JUNIOR = "junior"  # 0-2 years
    MID = "mid"  # 2-5 years
    SENIOR = "senior"  # 5-10 years
    LEAD = "lead"  # 10-15 years
    PRINCIPAL = "principal"  # 15+ years


class ExtractionMethod(str, Enum):
    """PDF extraction method"""
    PYMUPDF = "pymupdf"
    PDFPLUMBER = "pdfplumber"
    OCR = "ocr"
    MANUAL = "manual"


class RiskFlagType(str, Enum):
    """Types of risk flags"""
    WEAK_EVIDENCE = "weak_evidence"
    NO_METRICS = "no_metrics"
    TIMELINE_GAP = "timeline_gap"
    INCONSISTENCY = "inconsistency"
    OVERSTATEMENT = "overstatement"
    MISSING_REQUIRED_SKILL = "missing_required_skill"
    MISSING_EXPERIENCE = "missing_experience"
    OUTDATED_SKILL = "outdated_skill"


class RiskLevel(str, Enum):
    """Risk severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DecisionType(str, Enum):
    """Decision outcomes"""
    REUSE = "REUSE"
    RESCORE = "RESCORE"
    LIGHT_RESCREEN = "LIGHT_RESCREEN"
    DEEP_INTERVIEW = "DEEP_INTERVIEW"
    REJECT = "REJECT"


class InterviewRound(str, Enum):
    """Interview round types"""
    SCREENING = "screening"
    ROUND1 = "round1"
    ROUND2 = "round2"
    FINAL = "final"


class InterviewDecision(str, Enum):
    """Interview outcomes"""
    PASS = "PASS"
    FAIL = "FAIL"


# ============================================================================

# VALIDATORS

# ============================================================================

class PhoneValidator:
    """E.164 phone number validation and normalization"""
    
    @staticmethod
    def normalize_e164(phone: str) -> Optional[str]:
        """
        Normalize phone to E.164 format: +<country_code><number>
        Examples: "+84912345678", "+12025551234"
        """
        if not phone:
            return None
        
        # Remove common separators and spaces
        cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)
        
        # If already E.164 format
        if cleaned.startswith('+'):
            if re.match(r'^\+\d{10,15}$', cleaned):
                return cleaned
            else:
                return None  # Invalid E.164
        
        # Convert 0 prefix to country code (Vietnam: 0 → +84)
        if cleaned.startswith('0') and len(cleaned) >= 10:
            cleaned = '+84' + cleaned[1:]
            return cleaned if re.match(r'^\+84\d{9}$', cleaned) else None
        
        # If no + and 10-15 digits, assume US (+1)
        if re.match(r'^\d{10,15}$', cleaned):
            return '+1' + cleaned
        
        return None
    
    @staticmethod
    def validate_e164(phone: str) -> bool:
        """Validate E.164 format"""
        return bool(re.match(r'^\+\d{10,15}$', phone))


class DateValidator:
    """Date format validation and normalization"""
    
    @staticmethod
    def normalize_date(date_str: str) -> Optional[str]:
        """Normalize date to YYYY-MM format"""
        if not date_str or date_str.lower() in ['present', 'current', 'ongoing']:
            return None
        
        # Try various date formats
        formats = [
            '%Y-%m',           # 2024-01
            '%Y/%m',           # 2024/01
            '%m/%Y',           # 01/2024
            '%B %Y',           # January 2024
            '%b %Y',           # Jan 2024
            '%Y-%m-%d',        # 2024-01-15
            '%Y/%m/%d',        # 2024/01/15
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str.strip(), fmt)
                return parsed.strftime('%Y-%m')
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def compute_months(start_date: str, end_date: Optional[str] = None) -> int:
        """
        Compute duration in months between two dates (YYYY-MM format)
        If end_date is None, use current date
        """
        try:
            start = datetime.strptime(start_date, '%Y-%m')
            end = end_date
            
            if not end:
                end = datetime.now()
            else:
                end = datetime.strptime(end_date, '%Y-%m')
            
            months = (end.year - start.year) * 12 + (end.month - start.month)
            return max(0, months)
        except (ValueError, AttributeError):
            return 0


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
    
    @validator('phone', pre=True, always=True)
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
    
    @validator('issue_date', pre=True, always=True)
    def normalize_issue_date(cls, v):
        """Normalize date to YYYY-MM format"""
        if not v:
            return None
        normalized = DateValidator.normalize_date(v)
        if not normalized:
            raise ValueError(f"Invalid date format: {v}")
        return normalized
    
    @validator('expiry_date', pre=True, always=True)
    def normalize_expiry_date(cls, v):
        """Normalize date to YYYY-MM format"""
        if not v:
            return None
        normalized = DateValidator.normalize_date(v)
        if not normalized and v.lower() not in ['never', 'non-expiring']:
            raise ValueError(f"Invalid date format: {v}")
        return normalized
    
    @root_validator(skip_on_failure=True)
    def check_date_order(cls, values):
        """Ensure issue_date <= expiry_date"""
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
    
    @validator('normalized_name', pre=True, always=True)
    def normalize_skill_name(cls, v, values):
        """Auto-normalize skill name if not provided"""
        if v:
            return v.lower().strip()
        
        if 'name' in values:
            name = values['name']
            # Simple normalization: lowercase, remove versions
            normalized = re.sub(r'[\s\d\.\+\-#]', '', name.lower())
            normalized = re.sub(r'(\.js|\.net|\.io|3\.0)', '', normalized)
            return normalized
        
        return None


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
    
    @root_validator(skip_on_failure=True)
    def compute_duration(cls, values):
        """Auto-compute duration_months from dates"""
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
    
    @root_validator(skip_on_failure=True)
    def compute_duration_and_current(cls, values):
        """Auto-compute duration and is_current"""
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
    extraction_method: ExtractionMethod = Field(..., description="PDF extraction method")
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


# ============================================================================

# MATCHING & SCORING

# ============================================================================

class MatchingScore(BaseModel):
    """Detailed matching score between candidate and job"""
    candidate_id: str = Field(..., description="Candidate ID")
    job_id: str = Field(..., description="Job ID")
    
    # Component scores (0-1)
    skill_match: float = Field(default=0.0, ge=0, le=1, description="Required skills match %")
    skill_match_required: float = Field(default=0.0, ge=0, le=1, description="Required skills coverage")
    skill_match_preferred: float = Field(default=0.0, ge=0, le=1, description="Preferred skills match")
    
    experience_match: float = Field(default=0.0, ge=0, le=1, description="Experience level match")
    experience_years_match: float = Field(default=0.0, ge=0, le=1, description="Years of experience match")
    seniority_fit: float = Field(default=0.0, ge=0, le=1, description="Seniority level fit")
    
    project_relevance: float = Field(default=0.0, ge=0, le=1, description="Project relevance score")
    education_fit: float = Field(default=0.0, ge=0, le=1, description="Education requirements fit")
    
    location_fit: float = Field(default=0.5, ge=0, le=1, description="Location/remote fit")
    language_fit: float = Field(default=0.5, ge=0, le=1, description="Language requirements fit")
    
    # Gaps
    missing_required_skills: List[str] = Field(default_factory=list, description="Required skills missing")
    missing_preferred_skills: List[str] = Field(default_factory=list, description="Preferred skills missing")
    experience_gap_months: int = Field(default=0, description="Experience deficit in months")
    
    # Overall
    overall_score: float = Field(default=0.0, ge=0, le=1, description="Weighted overall match")
    match_percentage: float = Field(default=0.0, ge=0, le=100, description="Match percentage (0-100)")
    
    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow, description="When calculated")
    matching_model_version: str = Field(default="1.0", description="Matching model version")
    
    class Config:
        frozen = False
    
    def compute_overall_score(
        self,
        skill_weight: float = 0.35,
        experience_weight: float = 0.35,
        education_weight: float = 0.20,
        location_weight: float = 0.05,
        language_weight: float = 0.05
    ) -> float:
        """
        Compute weighted overall score
        Default weights: skills 35%, experience 35%, education 20%, location 5%, language 5%
        """
        self.overall_score = (
            self.skill_match * skill_weight +
            self.experience_match * experience_weight +
            self.education_fit * education_weight +
            self.location_fit * location_weight +
            self.language_fit * language_weight
        )
        self.match_percentage = round(self.overall_score * 100, 1)
        return self.overall_score


# ============================================================================

# JOB DESCRIPTION & ASSESSMENT

# ============================================================================

class JobDescription(BaseModel):
    """Job description schema"""
    jd_id: Optional[str] = Field(None, description="Job ID")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: str = Field(..., description="Full job description")
    requirements: List[str] = Field(default_factory=list, description="Job requirements")
    responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities")
    required_skills: List[str] = Field(default_factory=list, description="Required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred skills")
    seniority_level: Optional[SeniorityLevel] = Field(None, description="Expected seniority")
    experience_years_min: Optional[int] = Field(None, ge=0, description="Minimum years experience")
    experience_years_max: Optional[int] = Field(None, ge=0, description="Maximum years (if junior)")
    location: Optional[LocationFormat] = Field(None, description="Job location")
    salary_range: Optional[str] = Field(None, description="Salary range")
    languages_required: List[str] = Field(default_factory=list, description="Required languages")
    remote_eligible: bool = Field(default=False, description="Remote/hybrid eligible")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Created timestamp")
    
    class Config:
        frozen = False


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown"""
    skill_match: float = Field(default=0.0, ge=0, le=1, description="Skill match")
    experience_match: float = Field(default=0.0, ge=0, le=1, description="Experience match")
    project_relevance: float = Field(default=0.0, ge=0, le=1, description="Project relevance")
    seniority_fit: float = Field(default=0.0, ge=0, le=1, description="Seniority fit")
    overall_score: float = Field(default=0.0, ge=0, le=1, description="Overall score")
    
    class Config:
        frozen = False


class Assessment(BaseModel):
    """Assessment result"""
    assessment_id: str = Field(..., description="Unique assessment ID")
    candidate_id: str = Field(..., description="Candidate ID")
    job_id: str = Field(..., description="Job ID")
    profile: CandidateProfile = Field(..., description="Candidate profile")
    job: JobDescription = Field(..., description="Job description")
    matching_score: Optional[MatchingScore] = Field(None, description="Detailed matching score")
    scores: ScoreBreakdown = Field(default_factory=ScoreBreakdown, description="Score breakdown")
    decision: DecisionType = Field(..., description="Assessment decision")
    decision_reasoning: str = Field(..., description="Why this decision was made")
    risk_flags: List[RiskFlag] = Field(default_factory=list, description="Identified risks")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    assessed_at: datetime = Field(default_factory=datetime.utcnow, description="Assessment timestamp")
    model_version: str = Field(..., description="Model version used")
    
    class Config:
        frozen = False


# ============================================================================

# INTERVIEW & DECISION

# ============================================================================

class InterviewFeedback(BaseModel):
    """Interview feedback"""
    interview_id: str = Field(..., description="Interview ID")
    assessment_id: str = Field(..., description="Assessment ID")
    round: InterviewRound = Field(..., description="Interview round")
    interviewer: str = Field(..., description="Interviewer name")
    decision: InterviewDecision = Field(..., description="Pass/fail decision")
    technical_score: Optional[float] = Field(None, ge=0, le=1, description="Technical score")
    communication_score: Optional[float] = Field(None, ge=0, le=1, description="Communication score")
    culture_fit_score: Optional[float] = Field(None, ge=0, le=1, description="Culture fit")
    strengths: List[str] = Field(default_factory=list, description="Strengths observed")
    weaknesses: List[str] = Field(default_factory=list, description="Areas for improvement")
    notes: Optional[str] = Field(None, description="Additional notes")
    conducted_at: datetime = Field(default_factory=datetime.utcnow, description="Interview date")
    
    class Config:
        frozen = False


class DecisionResult(BaseModel):
    """Decision result with reasoning"""
    decision: DecisionType = Field(..., description="Final decision")
    reasoning: str = Field(..., description="Decision reasoning")
    score_breakdown: Optional[MatchingScore] = Field(None, description="Score details")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    next_steps: List[str] = Field(default_factory=list, description="Suggested next steps")
    
    class Config:
        frozen = False


# ============================================================================

# CV VERSION & API REQUESTS/RESPONSES

# ============================================================================

class CVVersion(BaseModel):
    """CV version for tracking"""
    version: str = Field(..., description="Version identifier")
    extracted_at: datetime = Field(default_factory=datetime.utcnow, description="Extraction timestamp")
    source_type: Literal["pdf", "docx", "text"] = Field(..., description="Source document type")
    raw_text: Optional[str] = Field(None, description="Raw extracted text")
    normalized_text: Optional[str] = Field(None, description="Normalized markdown text")
    profile: Optional[CandidateProfile] = Field(None, description="Parsed candidate profile")
    language: Optional[str] = Field(None, description="Detected language (vi/en)")
    translation_status: Literal["pending", "completed", "failed"] = Field(
        default="pending", description="Translation status"
    )
    extraction_confidence: float = Field(default=0.0, ge=0, le=1, description="Extraction confidence score")

    class Config:
        frozen = False


class ExtractCVRequest(BaseModel):
    """Request to extract CV"""
    file_path: Optional[str] = Field(None, description="Path to CV file")
    file_content: Optional[bytes] = Field(None, description="CV file content (base64)")
    file_url: Optional[str] = Field(None, description="URL to CV file")
    translate: bool = Field(default=True, description="Translate to English")

    class Config:
        frozen = False


class ExtractCVResponse(BaseModel):
    """Response from CV extraction"""
    cv_id: str = Field(..., description="Extracted CV ID")
    profile: CandidateProfile = Field(..., description="Candidate profile")
    raw_text: str = Field(..., description="Raw extracted text")
    normalized_text: str = Field(..., description="Normalized markdown")
    language: str = Field(..., description="Detected language")
    extraction_confidence: float = Field(..., description="Extraction confidence")

    class Config:
        frozen = False


class NormalizeJDRequest(BaseModel):
    """Request to normalize JD"""
    jd_text: Optional[str] = Field(None, description="JD text content")
    jd_id: Optional[str] = Field(None, description="Existing JD ID")

    class Config:
        frozen = False


class NormalizeJDResponse(BaseModel):
    """Response from JD normalization"""
    jd_id: str = Field(..., description="JD ID")
    job: JobDescription = Field(..., description="Normalized job description")
    normalization_confidence: float = Field(..., description="Normalization confidence")

    class Config:
        frozen = False


class AssessRequest(BaseModel):
    """Request to assess CV against JD"""
    cv_id: str = Field(..., description="CV ID to assess")
    jd_id: str = Field(..., description="JD ID to assess against")
    force_reassess: bool = Field(default=False, description="Force reassessment")

    class Config:
        frozen = False


class AssessResponse(BaseModel):
    """Response from assessment"""
    assessment: Assessment = Field(..., description="Assessment result")
    decision: DecisionResult = Field(..., description="Decision result")

    class Config:
        frozen = False


class SearchReuseRequest(BaseModel):
    """Request to search for reusable CVs"""
    jd_id: str = Field(..., description="JD ID to match")
    min_score: float = Field(default=0.7, ge=0, le=1, description="Minimum match score")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")

    class Config:
        frozen = False


class SearchReuseResponse(BaseModel):
    """Response from search"""
    matches: List[Assessment] = Field(default_factory=list, description="Matched assessments")
    total: int = Field(default=0, description="Total matches")

    class Config:
        frozen = False


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    mongodb: bool = Field(..., description="MongoDB connection status")
    ollama: bool = Field(..., description="Ollama service status")
    version: str = Field(..., description="API version")

    class Config:
        frozen = False


class MatchCandidateRequest(BaseModel):
    """Request to match candidate with job"""
    candidate_id: str = Field(..., description="Candidate ID")
    job_id: str = Field(..., description="Job ID")
    use_cached: bool = Field(default=True, description="Use cached results if available")
    
    class Config:
        frozen = False


class MatchCandidateResponse(BaseModel):
    """Response from matching"""
    matching_score: MatchingScore = Field(..., description="Detailed matching score")
    recommendation: str = Field(..., description="Whether to proceed")
    
    class Config:
        frozen = False


# Update forward references for RiskFlag
CandidateProfile.update_forward_refs()

# ============================================================================

# EXPORT

# ============================================================================

__all__ = [
    # Enumerations
    'CEFRLEVEL', 'SeniorityLevel', 'ExtractionMethod',
    'RiskFlagType', 'RiskLevel', 'DecisionType',
    'InterviewRound', 'InterviewDecision',
    
    # Validators & Utilities
    'PhoneValidator', 'DateValidator',
    
    # Models
    'LocationFormat', 'ContactInfo',
    'Certification', 'Language',
    'SkillEvidence', 'Skill',
    'Project', 'CareerProgression', 'Education',
    'DerivedFields', 'ParsingMetadata',
    'CandidateProfile', 'RiskFlag',
    'MatchingScore',
    'JobDescription', 'ScoreBreakdown',
    'Assessment',
    'InterviewFeedback', 'DecisionResult',
    'CVVersion',
    'ExtractCVRequest', 'ExtractCVResponse',
    'NormalizeJDRequest', 'NormalizeJDResponse',
    'AssessRequest', 'AssessResponse',
    'SearchReuseRequest', 'SearchReuseResponse',
    'HealthCheckResponse',
    'MatchCandidateRequest', 'MatchCandidateResponse',
]