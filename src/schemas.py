"""
Pydantic schemas for CV Intelligence Platform
Covers: CVs, Jobs, Assessments, Decisions, Interview Feedback
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class SeniorityLevel(str, Enum):
    """Candidate/Role seniority levels"""
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"


class RiskFlagType(str, Enum):
    """Types of risk flags"""
    WEAK_EVIDENCE = "weak_evidence"
    NO_METRICS = "no_metrics"
    TIMELINE_GAP = "timeline_gap"
    INCONSISTENCY = "inconsistency"
    OVERSTATEMENT = "overstatement"
    MISSING_REQUIRED_SKILL = "missing_required_skill"
    MISSING_EXPERIENCE = "missing_experience"


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


class RiskLevel(str, Enum):
    """Risk severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SkillEvidence(BaseModel):
    """Evidence for a skill"""
    skill_name: str = Field(..., description="Name of the skill")
    project_name: str = Field(..., description="Project where skill was used")
    evidence_text: str = Field(..., description="Quote or explanation from CV")
    metrics: List[str] = Field(default_factory=list, description="Metrics/outcomes")
    confidence: float = Field(default=0.8, ge=0, le=1, description="Confidence in evidence")

    class Config:
        frozen = False


class Project(BaseModel):
    """Project from CV with evidence breakdown"""
    name: str = Field(..., description="Project/company name")
    role: str = Field(..., description="Role in project")
    duration_months: int = Field(default=0, ge=0, description="Duration in months")
    description: Optional[str] = Field(None, description="Project description/overview")
    tech_stack: List[str] = Field(default_factory=list, description="Technologies used")
    contributions: List[str] = Field(default_factory=list, description="Key contributions")
    metrics: List[str] = Field(default_factory=list, description="Quantifiable outcomes")
    ownership: Literal["owned", "led", "contributed", "supported"] = Field(
        default="contributed", description="Level of ownership/leadership"
    )
    complexity_score: int = Field(default=3, ge=1, le=5, description="Technical complexity 1-5")
    impact_score: int = Field(default=3, ge=1, le=5, description="Business impact 1-5")
    evidence_strength: float = Field(default=0.5, ge=0, le=1, description="Confidence in project details")

    class Config:
        frozen = False


class Skill(BaseModel):
    """Skill with evidence linking"""
    name: str = Field(..., description="Skill name")
    level: SeniorityLevel = Field(default=SeniorityLevel.MID, description="Proficiency level")
    years_experience: float = Field(default=0, ge=0, description="Years of experience with skill")
    evidence: List[SkillEvidence] = Field(default_factory=list, description="Evidence where skill was used")
    confidence: float = Field(default=0.5, ge=0, le=1, description="Overall skill confidence")

    class Config:
        frozen = False


class RiskFlag(BaseModel):
    """Risk flag with details"""
    flag_type: RiskFlagType = Field(..., description="Type of risk")
    severity: RiskLevel = Field(..., description="Severity level")
    description: str = Field(..., description="Description of the risk")
    evidence: Optional[str] = Field(None, description="Evidence for the flag")

    class Config:
        frozen = False


class ContactInfo(BaseModel):
    """Contact information"""
    name: Optional[str] = Field(None, description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="Location/address")
    linkedin: Optional[str] = Field(None, description="LinkedIn URL")
    portfolio: Optional[str] = Field(None, description="Portfolio/website")

    class Config:
        frozen = False


class Education(BaseModel):
    """Education history"""
    institution: str = Field(..., description="School/university name")
    degree: str = Field(..., description="Degree obtained")
    field_of_study: Optional[str] = Field(None, description="Field of study")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date")
    gpa: Optional[float] = Field(None, description="GPA")

    class Config:
        frozen = False


class CareerProgression(BaseModel):
    """Career progression timeline"""
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    start_date: str = Field(..., description="Start date")
    end_date: Optional[str] = Field(None, description="End date (None if current)")
    duration_months: int = Field(default=0, description="Duration in months")

    class Config:
        frozen = False


class CandidateProfile(BaseModel):
    """Complete candidate profile"""
    contact: ContactInfo = Field(default_factory=ContactInfo, description="Contact information")
    summary: Optional[str] = Field(None, description="Professional summary")
    skills: List[Skill] = Field(default_factory=list, description="Extracted skills")
    experience: List[CareerProgression] = Field(default_factory=list, description="Work experience")
    projects: List[Project] = Field(default_factory=list, description="Projects")
    education: List[Education] = Field(default_factory=list, description="Education")
    certifications: List[str] = Field(default_factory=list, description="Certifications")
    languages: List[str] = Field(default_factory=list, description="Languages")
    risk_flags: List[RiskFlag] = Field(default_factory=list, description="Risk flags identified")

    class Config:
        frozen = False


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


class JobDescription(BaseModel):
    """Job description schema"""
    jd_id: Optional[str] = Field(None, description="JD ID")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: str = Field(..., description="Job description text")
    requirements: List[str] = Field(default_factory=list, description="Job requirements")
    responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities")
    required_skills: List[str] = Field(default_factory=list, description="Required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred skills")
    seniority_level: Optional[SeniorityLevel] = Field(None, description="Expected seniority")
    location: Optional[str] = Field(None, description="Job location")
    salary_range: Optional[str] = Field(None, description="Salary range")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Created timestamp")

    class Config:
        frozen = False


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown"""
    skill_match: float = Field(default=0.0, ge=0, le=1, description="Skill match score")
    experience_match: float = Field(default=0.0, ge=0, le=1, description="Experience match score")
    project_relevance: float = Field(default=0.0, ge=0, le=1, description="Project relevance score")
    seniority_fit: float = Field(default=0.0, ge=0, le=1, description="Seniority fit score")
    overall_score: float = Field(default=0.0, ge=0, le=1, description="Overall matching score")

    class Config:
        frozen = False


class Assessment(BaseModel):
    """Assessment result"""
    assessment_id: str = Field(..., description="Unique assessment ID")
    cv_id: str = Field(..., description="CV ID")
    jd_id: str = Field(..., description="JD ID")
    profile: CandidateProfile = Field(..., description="Candidate profile")
    job: JobDescription = Field(..., description="Job description")
    scores: ScoreBreakdown = Field(default_factory=ScoreBreakdown, description="Score breakdown")
    decision: DecisionType = Field(..., description="Assessment decision")
    risk_flags: List[RiskFlag] = Field(default_factory=list, description="Identified risks")
    assessed_at: datetime = Field(default_factory=datetime.utcnow, description="Assessment timestamp")
    model_version: str = Field(..., description="Model version used")

    class Config:
        frozen = False


class DecisionResult(BaseModel):
    """Decision result with reasoning"""
    decision: DecisionType = Field(..., description="Final decision")
    reasoning: str = Field(..., description="Decision reasoning")
    score_breakdown: Optional[ScoreBreakdown] = Field(None, description="Detailed score breakdown")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    next_steps: List[str] = Field(default_factory=list, description="Suggested next steps")

    class Config:
        frozen = False


class InterviewFeedback(BaseModel):
    """Interview feedback"""
    interview_id: str = Field(..., description="Interview ID")
    assessment_id: str = Field(..., description="Assessment ID")
    round: InterviewRound = Field(..., description="Interview round")
    interviewer: str = Field(..., description="Interviewer name")
    decision: InterviewDecision = Field(..., description="Interview decision")
    technical_score: Optional[float] = Field(None, ge=0, le=1, description="Technical score")
    communication_score: Optional[float] = Field(None, ge=0, le=1, description="Communication score")
    culture_fit_score: Optional[float] = Field(None, ge=0, le=1, description="Culture fit score")
    strengths: List[str] = Field(default_factory=list, description="Candidate strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Areas for improvement")
    notes: Optional[str] = Field(None, description="Additional notes")
    conducted_at: datetime = Field(default_factory=datetime.utcnow, description="Interview date")

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


__all__ = [
    "SeniorityLevel",
    "RiskFlagType",
    "DecisionType",
    "InterviewRound",
    "InterviewDecision",
    "RiskLevel",
    "SkillEvidence",
    "Project",
    "Skill",
    "RiskFlag",
    "ContactInfo",
    "Education",
    "CareerProgression",
    "CandidateProfile",
    "CVVersion",
    "JobDescription",
    "ScoreBreakdown",
    "Assessment",
    "DecisionResult",
    "InterviewFeedback",
    "ExtractCVRequest",
    "ExtractCVResponse",
    "NormalizeJDRequest",
    "NormalizeJDResponse",
    "AssessRequest",
    "AssessResponse",
    "SearchReuseRequest",
    "SearchReuseResponse",
    "HealthCheckResponse",
]
