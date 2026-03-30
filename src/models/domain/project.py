"""
Project Models

Enhanced project data structures with normalization, validation, and metrics.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from dateutil.relativedelta import relativedelta


@dataclass
class ProjectDuration:
    """Project duration information with normalization"""
    start_month: Optional[int] = None
    start_year: Optional[int] = None
    end_month: Optional[int] = None
    end_year: Optional[int] = None
    duration_months: float = 0.0
    
    def normalize_dates(self) -> None:
        """Normalize date components to valid ranges"""
        if self.start_month and (self.start_month < 1 or self.start_month > 12):
            self.start_month = None
        if self.end_month and (self.end_month < 1 or self.end_month > 12):
            self.end_month = None
    
    def calculate_duration(self) -> float:
        """Calculate duration in months from start/end dates"""
        if not self.start_year or not self.start_month:
            return 0.0
        
        start_date = datetime(self.start_year, self.start_month, 1)
        end_date = datetime(self.end_year or datetime.now(datetime.timezone.utc).year, self.end_month or datetime.now(datetime.timezone.utc).month, 1)
        
        diff = relativedelta(end_date, start_date)
        return diff.years * 12 + diff.months + (diff.days / 30.0)


@dataclass
class LLMProject:
    """LLM-extracted project data with comprehensive validation"""
    name: str
    company: str
    description: str
    technologies: List[str] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    role: str = ""
    duration: ProjectDuration = field(default_factory=ProjectDuration)
    complexity_level: str = "medium"  # low, medium, high
    ownership: str = "contributor"  # contributor, owner, technical_lead
    confidence: float = 0.75
    extraction_method: str = "llm"
    evidence_snippets: List[str] = field(default_factory=list)
    normalized_technologies: List[str] = field(default_factory=list)
    impact_score: float = 0.0
    business_value: str = ""
    team_size: Optional[int] = None
    project_type: str = "unknown"  # web, mobile, desktop, api, etc.
    start_date_str: Optional[str] = None
    end_date_str: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        self.normalize_technologies()
        self.validate_ownership()
        self.validate_complexity()
        self.normalize_dates()
    
    def normalize_technologies(self) -> None:
        """Normalize technology names to lowercase without special characters"""
        self.normalized_technologies = [
            tech.lower().strip().replace('.', '').replace('#', 'sharp')
            for tech in self.technologies
        ]
    
    def validate_ownership(self) -> None:
        """Validate ownership level"""
        valid_ownerships = ['contributor', 'owner', 'technical_lead']
        if self.ownership not in valid_ownerships:
            self.ownership = 'contributor'
    
    def validate_complexity(self) -> None:
        """Validate complexity level"""
        valid_levels = ['low', 'medium', 'high']
        if self.complexity_level not in valid_levels:
            self.complexity_level = 'medium'
    
    def normalize_dates(self) -> None:
        """Normalize date strings to YYYY-MM format"""
        if self.start_date_str:
            self.duration.start_year, self.duration.start_month = self._parse_date_str(self.start_date_str)
        if self.end_date_str:
            self.duration.end_year, self.duration.end_month = self._parse_date_str(self.end_date_str)
        
        self.duration.normalize_dates()
        self.duration.duration_months = self.duration.calculate_duration()
    
    def _parse_date_str(self, date_str: str) -> tuple:
        """Parse date string to year and month"""
        if not date_str:
            return None, None
        
        date_str = date_str.strip().lower()
        
        # Handle "present" or "current"
        if date_str in ['present', 'current', 'now', 'hiện tại', 'đến nay']:
            return datetime.now(datetime.timezone.utc).year, datetime.now(datetime.timezone.utc).month
        
        # Try YYYY-MM format
        try:
            if '-' in date_str and len(date_str) == 7:
                year, month = date_str.split('-')
                return int(year), int(month)
        except ValueError:
            pass
        
        # Try YYYY/MM format
        try:
            if '/' in date_str and len(date_str) == 7:
                year, month = date_str.split('/')
                return int(year), int(month)
        except ValueError:
            pass
        
        # Try Month YYYY format
        try:
            import re
            month_map = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
                'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }
            
            match = re.match(r'(\w+)\s+(\d{4})', date_str)
            if match:
                month_name, year = match.groups()
                month = month_map.get(month_name.lower())
                if month:
                    return int(year), month
        except Exception:
            pass
        
        return None, None
    
    def get_duration_years(self) -> float:
        """Get duration in years"""
        return self.duration.duration_months / 12.0
    
    def get_ownership_level(self) -> int:
        """Get numeric ownership level for scoring (contributor=1, technical_lead=2, owner=3)"""
        ownership_map = {'contributor': 1, 'technical_lead': 2, 'owner': 3}
        return ownership_map.get(self.ownership, 1)
    
    def get_complexity_score(self) -> int:
        """Get numeric complexity score (low=1, medium=2, high=3)"""
        complexity_map = {'low': 1, 'medium': 2, 'high': 3}
        return complexity_map.get(self.complexity_level, 2)
    
    def calculate_project_score(self) -> float:
        """Calculate overall project score based on various factors"""
        base_score = self.confidence * 10  # Base score from confidence
        
        # Add complexity bonus
        base_score += self.get_complexity_score() * 2
        
        # Add ownership bonus
        base_score += self.get_ownership_level() * 1.5
        
        # Add duration bonus (capped at 5 years)
        duration_bonus = min(self.get_duration_years(), 5) * 0.5
        base_score += duration_bonus
        
        # Add technology count bonus
        tech_bonus = min(len(self.technologies), 10) * 0.2
        base_score += tech_bonus
        
        return min(base_score, 20.0)  # Cap at 20
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'company': self.company,
            'description': self.description,
            'technologies': self.technologies,
            'normalized_technologies': self.normalized_technologies,
            'metrics': self.metrics,
            'role': self.role,
            'duration': {
                'start_month': self.duration.start_month,
                'start_year': self.duration.start_year,
                'end_month': self.duration.end_month,
                'end_year': self.duration.end_year,
                'duration_months': self.duration.duration_months
            },
            'complexity_level': self.complexity_level,
            'ownership': self.ownership,
            'confidence': self.confidence,
            'extraction_method': self.extraction_method,
            'evidence_snippets': self.evidence_snippets,
            'impact_score': self.impact_score,
            'business_value': self.business_value,
            'team_size': self.team_size,
            'project_type': self.project_type,
            'start_date_str': self.start_date_str,
            'end_date_str': self.end_date_str,
            'project_score': self.calculate_project_score()
        }