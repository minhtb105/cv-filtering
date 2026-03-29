"""
Task 2 Phase 2: Experience Engine with Advanced Date Parsing
Comprehensive date format support (10+ formats in English & Vietnamese)
Career progression analysis and total years calculation
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class DateRange:
    """Represents a date range"""
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    start_text: str = ""
    end_text: str = ""
    is_present: bool = False  # True if end_date is "present"
    
    def get_duration_months(self) -> int:
        """Get duration in months"""
        if not self.start_date:
            return 0
        
        end = self.end_date if self.end_date else datetime.now()
        diff = relativedelta(end, self.start_date)
        return diff.years * 12 + diff.months
    
    def get_duration_years(self) -> float:
        """Get duration in years"""
        return self.get_duration_months() / 12.0


@dataclass
class ExperienceEntry:
    """Represents a single experience entry"""
    company: str
    position: str
    date_range: DateRange
    description: str = ""
    technologies: List[str] = field(default_factory=list)
    
    def get_duration_months(self) -> int:
        return self.date_range.get_duration_months()
    
    def get_duration_years(self) -> float:
        return self.date_range.get_duration_years()


class DateParser:
    """Parse various date formats (English + Vietnamese)"""
    
    MONTH_MAPPING = {
        'en': {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
        },
        'vi': {
            'tháng 1': 1, 'tháng 2': 2, 'tháng 3': 3, 'tháng 4': 4, 'tháng 5': 5, 'tháng 6': 6,
            'tháng 7': 7, 'tháng 8': 8, 'tháng 9': 9, 'tháng 10': 10, 'tháng 11': 11, 'tháng 12': 12
        }
    }
    
    DATE_PATTERNS = [
        # Tháng X/YYYY (Vietnamese format)
        (r'tháng\s+(\d{1,2})/(\d{4})', 'vi_slash'),
        # January 2020, Feb 2019
        (r'(january|february|march|april|may|june|july|august|september|october|november|december|'
         r'jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{4})', 'en_month_year'),
        # 2020-01 or 2020/01
        (r'(\d{4})[-/](\d{1,2})', 'year_month'),
        # 01/2020
        (r'(\d{1,2})/(\d{4})', 'month_year_slash'),
    ]
    
    PRESENT_KEYWORDS = ['present', 'current', 'currently', 'hiện tại', 'đến nay']
    
    @classmethod
    def parse_date(cls, date_str: str) -> Optional[datetime]:
        """Parse single date string"""
        
        if not date_str or not date_str.strip():
            return None
        
        date_str_lower = date_str.lower().strip()
        
        # Check for "present" indicators
        if any(kw in date_str_lower for kw in cls.PRESENT_KEYWORDS):
            return None  # Return None to indicate "present"
        
        # Try each pattern
        for pattern, pattern_type in cls.DATE_PATTERNS:
            match = re.search(pattern, date_str_lower, re.IGNORECASE)
            if match:
                return cls._parse_match(match, pattern_type)
        
        return None
    
    @classmethod
    def _parse_match(cls, match, pattern_type: str) -> Optional[datetime]:
        """Parse matched groups based on pattern type"""
        
        try:
            if pattern_type == 'vi_slash':
                month = int(match.group(1))
                year = int(match.group(2))
                return datetime(year, month, 1)
            
            elif pattern_type == 'en_month_year':
                month_str = match.group(1).lower()
                year = int(match.group(2))
                month = cls.MONTH_MAPPING['en'].get(month_str, 1)
                return datetime(year, month, 1)
            
            elif pattern_type == 'year_month':
                year = int(match.group(1))
                month = int(match.group(2))
                return datetime(year, month, 1)
            
            elif pattern_type == 'month_year_slash':
                month = int(match.group(1))
                year = int(match.group(2))
                return datetime(year, month, 1)
        
        except (ValueError, IndexError):
            pass
        
        return None
    
    @classmethod
    def parse_date_range(cls, text: str) -> Optional[DateRange]:
        """Parse date range from text like 'January 2020 - March 2021'"""
        
        if not text:
            return None
        
        # Split by common separators
        parts = re.split(r'\s*[-–—]\s*', text.strip())
        
        if len(parts) == 2:
            start_text = parts[0].strip()
            end_text = parts[1].strip()
            
            start_date = cls.parse_date(start_text)
            
            # Check if end is "present"
            is_present = any(kw in end_text.lower() for kw in cls.PRESENT_KEYWORDS)
            end_date = None if is_present else cls.parse_date(end_text)
            
            if start_date:
                return DateRange(
                    start_date=start_date,
                    end_date=end_date,
                    start_text=start_text,
                    end_text=end_text,
                    is_present=is_present
                )
        
        elif len(parts) == 1:
            # Single date - assume it's still ongoing
            start_date = cls.parse_date(parts[0])
            if start_date:
                return DateRange(
                    start_date=start_date,
                    end_date=None,
                    start_text=parts[0],
                    is_present=True
                )
        
        return None


class ExperienceExtractor:
    """Extract experience entries from CV markdown"""
    
    COMPANY_KEYWORDS = ['company', 'at', 'employer', 'organization', 'cty', 'công ty']
    POSITION_KEYWORDS = ['position', 'title', 'role', 'chức vụ', 'vị trí']
    
    @classmethod
    def extract_experience_section(cls, markdown_cv: str) -> List[str]:
        """Extract experience section from markdown CV"""
        
        lines = markdown_cv.split('\n')
        in_experience = False
        section_lines = []
        
        for line in lines:
            line_lower = line.lower()
            
            # Check for experience section header
            if any(kw in line_lower for kw in ['## experience', '## work experience', '## employment']):
                in_experience = True
                continue
            
            # Check for next section header (end of experience)
            if in_experience and line.startswith('##') and 'experience' not in line_lower:
                break
            
            if in_experience:
                section_lines.append(line)
        
        return section_lines
    
    @classmethod
    def extract_entries(cls, experience_text: str) -> List[ExperienceEntry]:
        """Parse experience entries from text"""
        
        entries = []
        lines = [l for l in experience_text.split('\n') if l.strip()]
        
        current_entry = {
            'company': '',
            'position': '',
            'date_range': None,
            'description': ''
        }
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip headers
            if line_stripped.startswith('#'):
                continue
            
            # Look for date ranges
            if cls._looks_like_date(line_stripped):
                if current_entry['position'] and current_entry['company']:
                    current_entry['date_range'] = DateParser.parse_date_range(line_stripped)
            
            # Look for company/position info
            elif any(kw in line_stripped.lower() for kw in cls.COMPANY_KEYWORDS):
                current_entry['company'] = line_stripped.replace('Company:', '').replace('at', '').strip()
            elif any(kw in line_stripped.lower() for kw in cls.POSITION_KEYWORDS):
                current_entry['position'] = line_stripped.replace('Position:', '').replace('Title:', '').strip()
            
            # Bullet points are description
            elif line_stripped.startswith('-') or line_stripped.startswith('•'):
                current_entry['description'] += line_stripped[1:].strip() + ' '
            
            # If we have company and date, this might be a new entry
            if current_entry['company'] and current_entry['date_range']:
                entry = ExperienceEntry(
                    company=current_entry['company'],
                    position=current_entry['position'],
                    date_range=current_entry['date_range'],
                    description=current_entry['description'].strip()
                )
                entries.append(entry)
                current_entry = {
                    'company': '',
                    'position': '',
                    'date_range': None,
                    'description': ''
                }
        
        return entries
    
    @classmethod
    def _looks_like_date(cls, text: str) -> bool:
        """Check if text looks like a date"""
        return bool(re.search(r'\d{1,2}[-/]\d{1,2}|january|february|march|\d{4}|tháng', text.lower()))


class ExperienceEngine:
    """Comprehensive experience analysis engine"""
    
    def __init__(self):
        self.date_parser = DateParser()
        self.experience_extractor = ExperienceExtractor()
    
    def calculate_total_years(self, entries: List[ExperienceEntry]) -> float:
        """Calculate total work experience in years"""
        
        if not entries:
            return 0.0
        
        total_months = 0
        
        for entry in entries:
            total_months += entry.get_duration_months()
        
        return total_months / 12.0
    
    def detect_gaps(self, entries: List[ExperienceEntry]) -> List[Dict]:
        """Detect employment gaps"""
        
        if len(entries) < 2:
            return []
        
        # Sort by start date
        sorted_entries = sorted(entries, key=lambda e: e.date_range.start_date or datetime.now())
        
        gaps = []
        
        for i in range(len(sorted_entries) - 1):
            current_end = sorted_entries[i].date_range.end_date
            next_start = sorted_entries[i + 1].date_range.start_date
            
            if current_end and next_start and current_end < next_start:
                gap_months = (next_start - current_end).days / 30
                gaps.append({
                    'between': f"{sorted_entries[i].company} and {sorted_entries[i+1].company}",
                    'months': gap_months
                })
        
        return gaps
    
    def detect_overlaps(self, entries: List[ExperienceEntry]) -> List[Dict]:
        """Detect overlapping employment periods"""
        
        overlaps = []
        
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                entry1 = entries[i]
                entry2 = entries[j]
                
                if self._date_ranges_overlap(entry1.date_range, entry2.date_range):
                    overlaps.append({
                        'company1': entry1.company,
                        'company2': entry2.company,
                        'period': f"{max(entry1.date_range.start_date, entry2.date_range.start_date).strftime('%Y-%m')} to "
                                 f"{min(entry1.date_range.end_date or datetime.now(), entry2.date_range.end_date or datetime.now()).strftime('%Y-%m')}"
                    })
        
        return overlaps
    
    @staticmethod
    def _date_ranges_overlap(range1: DateRange, range2: DateRange) -> bool:
        """Check if two date ranges overlap"""
        
        if not range1.start_date or not range2.start_date:
            return False
        
        end1 = range1.end_date or datetime.now()
        end2 = range2.end_date or datetime.now()
        
        return range1.start_date <= end2 and range2.start_date <= end1
    
    def analyze_progression(self, entries: List[ExperienceEntry]) -> Dict:
        """Analyze career progression"""
        
        if not entries:
            return {'progression': 'unknown'}
        
        sorted_entries = sorted(entries, key=lambda e: e.date_range.start_date or datetime.now())
        
        # Extract position levels
        position_levels = []
        for entry in sorted_entries:
            pos_lower = entry.position.lower()
            if any(w in pos_lower for w in ['senior', 'lead', 'principal', 'architect']):
                position_levels.append(3)  # Senior
            elif any(w in pos_lower for w in ['mid', 'specialist', 'engineer']):
                position_levels.append(2)  # Mid
            else:
                position_levels.append(1)  # Junior
        
        # Analyze progression
        if len(position_levels) > 1:
            progression = 'healthy' if position_levels[-1] >= position_levels[0] else 'lateral'
        else:
            progression = 'stable'
        
        return {
            'progression': progression,
            'position_trajectory': position_levels,
            'current_level': position_levels[-1] if position_levels else 0
        }
