"""
Core data models for CV Intelligence Platform
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json


@dataclass
class ContactInfo:
    """Contact information extracted from CV"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None


@dataclass
class Experience:
    """Work experience entry"""
    title: str
    company: str
    duration: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Education:
    """Education entry"""
    degree: str
    field: str
    institution: str
    graduation_date: Optional[str] = None


@dataclass
class StructuredProfile:
    """Structured extracted data from CV"""
    contact: ContactInfo = field(default_factory=ContactInfo)
    summary: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    experiences: List[Experience] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    years_experience: float = 0.0
    
    def to_dict(self):
        return asdict(self)


@dataclass
class CVVersion:
    """Single version of a CV"""
    version_id: str  # timestamp-based
    file_name: str
    file_path: str
    raw_text: str
    structured_data: StructuredProfile
    embedding: Optional[List[float]] = None
    file_format: str = "pdf"  # pdf, docx, image
    extraction_quality: float = 1.0  # 0-1 score
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self):
        return {
            "version_id": self.version_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "raw_text": self.raw_text[:500],  # truncate for display
            "structured_data": self.structured_data.to_dict(),
            "embedding": None if self.embedding is None else "computed",
            "file_format": self.file_format,
            "extraction_quality": self.extraction_quality,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class Candidate:
    """Candidate profile with version history"""
    candidate_id: str
    cv_versions: List[CVVersion] = field(default_factory=list)
    category: Optional[str] = None  # from folder name
    job_fit_scores: Dict[str, float] = field(default_factory=dict)
    risk_flags: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    notes: str = ""
    
    @property
    def latest_version(self) -> Optional[CVVersion]:
        """Get most recent CV version"""
        if not self.cv_versions:
            return None
        return sorted(self.cv_versions, key=lambda x: x.created_at)[-1]
    
    @property
    def contact_info(self) -> Optional[ContactInfo]:
        """Get contact info from latest version"""
        if self.latest_version:
            return self.latest_version.structured_data.contact
        return None
    
    @property
    def skills(self) -> List[str]:
        """Get skills from latest version"""
        if self.latest_version:
            return self.latest_version.structured_data.skills
        return []
    
    @property
    def embedding(self) -> Optional[List[float]]:
        """Get embedding from latest version"""
        if self.latest_version:
            return self.latest_version.embedding
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "category": self.category,
            "latest_version": self.latest_version.to_dict() if self.latest_version else None,
            "version_count": len(self.cv_versions),
            "skills": self.skills,
            "risk_flags": self.risk_flags,
            "last_updated": self.last_updated.isoformat(),
            "notes": self.notes
        }


# Test instantiation
if __name__ == "__main__":
    contact = ContactInfo(name="John Doe", email="john@example.com")
    profile = StructuredProfile(contact=contact, skills=["Python", "API Design"])
    version = CVVersion(
        version_id="v1_20240320",
        file_name="john_doe.pdf",
        file_path="/data/john_doe.pdf",
        raw_text="John Doe is a software engineer...",
        structured_data=profile
    )
    candidate = Candidate(
        candidate_id="cand_001",
        cv_versions=[version],
        category="ENGINEERING"
    )
    print(json.dumps(candidate.to_dict(), indent=2, default=str))
