"""
Post-Processing Layer - Data enrichment after LLM extraction

Handles:
1. Date normalization (various formats → YYYY-MM-DD)
2. Experience calculation (total years from career entries)
3. Seniority level assignment (based on years + title keywords)

Architecture: Clean separation of concerns, no LLM re-processing, trust LLM extraction
"""

from copy import copy
import logging
import re
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from src.models.domain.candidate import (
    CandidateProfile
)
from src.models.validation.enums import SeniorityLevel

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of post-processing"""
    success: bool
    profile: Optional[CandidateProfile] = None
    total_years_experience: float = 0.0
    seniority_level: Optional[SeniorityLevel] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class PostProcessor:
    """
    Post-processing layer for CV extraction results.
    
    Operates AFTER LLM extraction:
    - Normalizes dates to ISO format (YYYY-MM-DD)
    - Calculates total years of experience
    - Assigns seniority level based on experience + title signals
    
    Design principle: Trust LLM output, add value through computation only
    """
    
    # Seniority level thresholds based on years of experience
    SENIORITY_THRESHOLDS = {
        SeniorityLevel.JUNIOR: (0, 2),          # 0-2 years
        SeniorityLevel.MID: (2, 5),             # 2-5 years
        SeniorityLevel.SENIOR: (5, 10),         # 5-10 years
        SeniorityLevel.LEAD: (10, 15),          # 10-15 years
        SeniorityLevel.PRINCIPAL: (15, 100),    # 15+ years
    }
    
    # Title keywords for seniority signal boosting
    SENIORITY_KEYWORDS = {
        "lead": SeniorityLevel.LEAD,
        "principal": SeniorityLevel.PRINCIPAL,
        "director": SeniorityLevel.LEAD,
        "architect": SeniorityLevel.SENIOR,
        "staff": SeniorityLevel.SENIOR,
        "senior": SeniorityLevel.SENIOR,
        "junior": SeniorityLevel.JUNIOR,
        "intern": SeniorityLevel.JUNIOR,
        "trainee": SeniorityLevel.JUNIOR,
        "head": SeniorityLevel.LEAD,
        "manager": SeniorityLevel.LEAD,
        "executive": SeniorityLevel.LEAD,
        "cto": SeniorityLevel.PRINCIPAL,
        "ceo": SeniorityLevel.PRINCIPAL,
        "cfo": SeniorityLevel.PRINCIPAL,
    }
    
    def __init__(self):
        """Initialize post-processor"""
        pass
    
    def process(self, profile: CandidateProfile) -> ProcessingResult:
        """
        Post-process extracted CV profile.
        
        Args:
            profile: CandidateProfile from LLM extraction
            
        Returns:
            ProcessingResult with enriched profile and metadata
        """
        errors = []
        profile_copy = copy.deepcopy(profile)
        
        try:
            # Step 1: Normalize dates across all sections
            self._normalize_candidate_dates(profile, errors)
            
            # Step 2: Calculate total years of experience
            total_years = self._calculate_total_experience(profile)
            
            # Step 3: Assign seniority level based on experience + titles
            seniority_level = self._assign_seniority_level(profile, total_years)
            
            # Step 4: Enrich profile with computed values
            profile_copy.total_years_of_experience = total_years
            profile_copy.seniority_level = seniority_level
            
            return ProcessingResult(
                success=True,
                profile=profile_copy,
                total_years_experience=total_years,
                seniority_level=seniority_level,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Post-processing failed: {e}")
            return ProcessingResult(
                success=False,
                profile=profile,
                errors=[str(e)]
            )
    
    # ==========================================================================
    # Date Normalization
    # ==========================================================================
    
    def _normalize_candidate_dates(self, profile: CandidateProfile, errors: List[str]) -> None:
        """Normalize all dates in profile to YYYY-MM-DD format"""
        
        # Normalize experience dates
        if profile.experience:
            for entry in profile.experience:
                if entry.start_date:
                    try:
                        entry.start_date = self.normalize_date(entry.start_date, errors)
                    except Exception as e:
                        errors.append(f"Failed to normalize start_date: {entry.start_date}")
                
                if entry.end_date:
                    try:
                        entry.end_date = self.normalize_date(entry.end_date, errors)
                    except Exception as e:
                        errors.append(f"Failed to parse end date for experience entry: {e}")
        
        # Normalize project dates
        if profile.projects:
            for project in profile.projects:
                if project.start_date:
                    try:
                        project.start_date = self.normalize_date(project.start_date, errors)
                    except Exception as e:
                        errors.append(f"Failed to normalize start_date for project entry: {project.start_date}")

                if project.end_date:
                    try:
                        project.end_date = self.normalize_date(project.end_date, errors)
                    except Exception as e:
                        errors.append(f"Failed to parse end date for project entry: {e}")

        # Normalize education dates
        if profile.education:
            for edu in profile.education:
                if edu.start_date:
                    try:
                        edu.start_date = self.normalize_date(edu.start_date, errors)
                    except Exception as e:
                        errors.append(f"Failed to normalize start_date for education entry: {edu.start_date}")
                
                if edu.end_date:
                    try:
                        edu.end_date = self.normalize_date(edu.end_date, errors)
                    except Exception as e:
                        errors.append(f"Failed to normalize end_date for education entry: {edu.end_date}")

        # Normalize certification dates
        if profile.certifications:
            for cert in profile.certifications:
                if cert.issue_date:
                    try:
                        cert.issue_date = self.normalize_date(cert.issue_date, errors)
                    except Exception as e:
                        errors.append(f"Failed to normalize issue_date for certification entry: {cert.issue_date}")
                
                if cert.expiry_date:
                    try:
                        cert.expiry_date = self.normalize_date(cert.expiry_date, errors)
                    except Exception as e:
                        errors.append(f"Failed to normalize expiry_date for certification entry: {cert.expiry_date}")

    @staticmethod
    def normalize_date(date_input: str, errors: List[str]) -> str:
        """
        Normalize date to ISO format YYYY-MM-DD.
        
        Supports formats:
        - YYYY-MM, YYYY/MM (→ YYYY-MM-01)
        - YYYY-MM-DD, YYYY/MM/DD (→ YYYY-MM-DD)
        - Month YYYY (Jan 2024 → 2024-01-01)
        - DD.MM.YYYY (European format → YYYY-MM-DD)
        - YYYY年MM月 (Chinese/Japanese format → YYYY-MM-01)
        - "Present", "Current" → today's date
        
        Args:
            date_input: Date string in various formats
            
        Returns:
            Date in YYYY-MM-DD format
        """
        if not isinstance(date_input, str):
            return date_input  # Return as-is if already a date object or other type
        
        date_str = date_input.strip()
        
        # Check for "present" indicators
        if date_str.lower() in ["present", "current", "now", "hiện tại", "đến nay"]:
            return datetime.now().strftime("%Y-%m-%d")
        
        # Try multiple date patterns
        patterns = [
            # YYYY-MM-DD or YYYY/MM/DD
            (r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", lambda m: f"{m[1]}-{m[2].zfill(2)}-{m[3].zfill(2)}"),
            
            # YYYY-MM or YYYY/MM (add day 01)
            (r"^(\d{4})[-/](\d{1,2})$", lambda m: f"{m[1]}-{m[2].zfill(2)}-01"),
            
            # MM/YYYY or M/YYYY (European)
            (r"^(\d{1,2})/(\d{4})$", lambda m: f"{m[2]}-{m[1].zfill(2)}-01"),
            
            # Mon YYYY or Month YYYY
            (r"^(january|february|march|april|may|june|july|august|september|october|november|december|"
             r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{4})$",
             PostProcessor._parse_month_year),
            
            # DD.MM.YYYY (European format)
            (r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", lambda m: f"{m[3]}-{m[2].zfill(2)}-{m[1].zfill(2)}"),
            
            # YYYY年MM月 or YYYY年MM月DD日 (Chinese/Japanese)
            (r"^(\d{4})年(\d{1,2})月(?:(\d{1,2})日)?$",
             lambda m: f"{m[1]}-{m[2].zfill(2)}-{(m[3] or '01').zfill(2)}"),
            
            # YYYY/MM/DD (ISO with slashes)
            (r"^(\d{4})/(\d{1,2})/(\d{1,2})$", lambda m: f"{m[1]}-{m[2].zfill(2)}-{m[3].zfill(2)}"),
        ]
        
        for pattern, transformer in patterns:
            match = re.match(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    if callable(transformer):
                        return transformer(groups)
                except Exception as e:
                    logger.warning(f"Failed to parse date '{date_str}': {e}")
                    errors.append(f"Failed to parse date '{date_str}")
                    continue
        
        # If no pattern matches, try to parse with dateutil as last resort
        try:
            from dateutil import parser as date_parser
            parsed = date_parser.parse(date_str, fuzzy=False)
            return parsed.strftime("%Y-%m-%d")
        except Exception as e:
            logger.warning(f"Could not normalize date '{date_str}': {e}")
            errors.append(f"Could not normalize date '{date_str}': {e}")
            return date_input
    
    @staticmethod
    def _parse_month_year(groups):
        """Parse (month_name, year) tuple to YYYY-MM-01"""
        month_map = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12',
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'sept': '09', 'oct': '10', 'nov': '11', 'dec': '12',
        }
        month_name = groups[0].lower()
        year = groups[1]
        month = month_map.get(month_name, '01')
        return f"{year}-{month}-01"
    
    # ==========================================================================
    # Experience Calculation
    # ==========================================================================
    
    def _calculate_total_experience(self, profile: CandidateProfile) -> float:
        """
        Calculate total years of experience from all career entries.
        
        Logic:
        - Sum duration_months from all experience entries
        - Include overlapping periods (count 1:1 towards total)
        - Convert to years (months / 12)
        
        Args:
            profile: CandidateProfile
            
        Returns:
            Total years as float (e.g., 5.5 for 5 years 6 months)
        """
        if not profile.experience:
            return 0.0
        
        total_months = 0
        
        for entry in profile.experience:
            # Use existing duration_months if available (should be set by CandidateProfile)
            if hasattr(entry, 'duration_months') and entry.duration_months:
                total_months += entry.duration_months
            else:
                # Fallback: calculate from dates if duration_months not set
                if entry.start_date:
                    try:
                        start = self._parse_date_for_calc(entry.start_date)
                        end = self._parse_date_for_calc(entry.end_date) if entry.end_date else datetime.now()
                        diff = relativedelta(end, start)
                        months = diff.years * 12 + diff.months
                        total_months += max(0, months)
                    except Exception as e:
                        logger.warning(f"Failed to calculate duration for {entry.company}: {e}")
        
        return round(total_months / 12.0, 1)  # Convert to years, round to 1 decimal
    
    @staticmethod
    def _parse_date_for_calc(date_str: str) -> datetime:
        """Parse date string to datetime for calculation"""
        if isinstance(date_str, datetime):
            return date_str
        if isinstance(date_str, date):
            return datetime.combine(date_str, datetime.min.time())
        
        # Try standard formats
        for fmt in ["%Y-%m-%d", "%Y-%m", "%Y/%m/%d"]:
            try:
                return datetime.strptime(date_str[:10], fmt)
            except:
                continue
        
        # Try month-year format
        try:
            normalized = PostProcessor.normalize_date(date_str)
            if normalized:
                return datetime.strptime(normalized, "%Y-%m-%d")
        except (ValueError, TypeError):
            pass
        
        raise ValueError(f"Cannot parse date: {date_str}")
    
    # ==========================================================================
    # Seniority Assignment
    # ==========================================================================
    
    def _assign_seniority_level(
        self,
        profile: CandidateProfile,
        total_years: float
    ) -> SeniorityLevel:
        """
        Assign seniority level based on:
        1. Years of experience (primary signal from SENIORITY_THRESHOLDS)
        2. Title keywords from most recent role (secondary signal for boosting)
        
        Algorithm:
        - Step 1: Determine level from years alone
        - Step 2: Check recent title keywords (up to +1 level boost)
        - Step 3: Cap boost (can't exceed PRINCIPAL)
        
        Args:
            profile: CandidateProfile
            total_years: Total years of experience
            
        Returns:
            SeniorityLevel (intern, fresher, junior, mid, senior, lead, principal)
        """
        
        # Step 1: Determine base level from years
        base_level = self._get_level_from_experience(total_years)
        
        # Step 2: Check recent role title for seniority keywords (boost signal)
        boosted_level = base_level
        
        if profile.experience and len(profile.experience) > 0:
            # Find most recent role by start_date
            most_recent = max(
                (e for e in profile.experience if e.start_date),
                key=lambda e: e.start_date,
                default=profile.experience[0]
            )
            most_recent_title = most_recent.title
            if most_recent_title:
                most_recent_title = most_recent_title.lower()
                # Check if title contains seniority keywords
                title_level = self._extract_level_from_title(most_recent_title)
            else:
                title_level = None            
            # Boost logic: if title suggests higher level, use it (but not degrade)
            if title_level and self._level_to_rank(title_level) > self._level_to_rank(base_level):
                boosted_level = title_level        
            
        return boosted_level
    
    @staticmethod
    def _get_level_from_experience(total_years: float) -> SeniorityLevel:
        """Get seniority level based on years of experience"""
        for level, (min_years, max_years) in PostProcessor.SENIORITY_THRESHOLDS.items():
            if min_years <= total_years < max_years:
                return level
        # Default to principal if above all thresholds
        return SeniorityLevel.PRINCIPAL
    
    @staticmethod
    def _extract_level_from_title(title: str) -> Optional[SeniorityLevel]:
        """Extract seniority level from job title based on keywords"""
        for keyword, level in PostProcessor.SENIORITY_KEYWORDS.items():
            if keyword in title:
                return level
        return None
    
    @staticmethod
    def _level_to_rank(level: SeniorityLevel) -> int:
        """Convert SeniorityLevel to numeric rank for comparison"""
        rank_map = {
            SeniorityLevel.JUNIOR: 1,
            SeniorityLevel.MID: 2,
            SeniorityLevel.SENIOR: 3,
            SeniorityLevel.LEAD: 4,
            SeniorityLevel.PRINCIPAL: 5,
        }
        return rank_map.get(level, 0)
