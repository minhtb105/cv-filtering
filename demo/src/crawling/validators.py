"""
Validation and normalization utilities for job description data

Provides consistent data cleaning and validation across different job board sources.
"""

import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

from src.models import JobDescription


class JobDescriptionValidator:
    """Validates and normalizes job description data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_job_description(self, job: JobDescription) -> bool:
        """Validate a job description object"""
        try:
            # Check required fields
            required_fields = ['title', 'company', 'location', 'category', 'source', 'url']
            for field in required_fields:
                if not getattr(job, field):
                    self.logger.warning(f"Missing required field: {field} in job {job.title}")
                    return False
            
            # Validate salary range
            if job.salary_min is not None and job.salary_max is not None:
                if job.salary_min > job.salary_max:
                    self.logger.warning(f"Invalid salary range: min > max for job {job.title}")
                    return False
            
            # Validate experience level
            valid_experience_levels = ['Entry', 'Junior', 'Mid', 'Senior', 'Lead', 'Manager', 'Director', 'Executive']
            if job.experience_level and job.experience_level not in valid_experience_levels:
                self.logger.warning(f"Unusual experience level: {job.experience_level} for job {job.title}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation error for job {job.title}: {str(e)}")
            return False
    
    def normalize_salary(self, salary_text: str) -> Dict[str, Optional[int]]:
        """Normalize salary text to structured format"""
        if not salary_text or salary_text.lower() in ['thỏa thuận', 'negotiable', 'competitive']:
            return {"min": None, "max": None, "currency": "VND"}
        
        # Remove common prefixes/suffixes
        salary_text = re.sub(r'^(lương|salary|thu nhập|income):\s*', '', salary_text, flags=re.IGNORECASE)
        salary_text = re.sub(r'\s*\(.*?\)$', '', salary_text)  # Remove parenthetical info
        
        # Extract currency
        currency = "VND"
        if 'usd' in salary_text.lower() or '$' in salary_text:
            currency = "USD"
        elif 'eur' in salary_text.lower() or '€' in salary_text:
            currency = "EUR"
        
        # Remove currency symbols for processing
        salary_text = re.sub(r'[$€]', '', salary_text)
        
        # Extract numbers and ranges
        numbers = re.findall(r'\d{1,3}(?:\.\d{3})*(?:,\d+)?', salary_text.replace(',', ''))
        
        if not numbers:
            return {"min": None, "max": None, "currency": currency}
        
        # Convert to integers
        values = []
        for num in numbers:
            # Handle decimal numbers (e.g., 10.5)
            if '.' in num:
                try:
                    values.append(float(num.replace('.', '')))
                except ValueError:
                    continue
            else:
                try:
                    values.append(int(num.replace('.', '')))
                except ValueError:
                    continue
        
        if not values:
            return {"min": None, "max": None, "currency": currency}
        
        # Determine min/max
        if len(values) == 1:
            # Single value - assume it's the minimum or exact value
            return {"min": values[0], "max": values[0], "currency": currency}
        elif len(values) >= 2:
            # Range found
            return {"min": min(values), "max": max(values), "currency": currency}
        
        return {"min": None, "max": None, "currency": currency}
    
    def normalize_location(self, location_text: str) -> str:
        """Normalize location to standard format"""
        if not location_text:
            return "Unknown"
        
        # Standardize Vietnamese locations
        location_mapping = {
            'hà nội': 'Hà Nội',
            'ha noi': 'Hà Nội',
            'hanoi': 'Hà Nội',
            'tp.hcm': 'TP.HCM',
            'tp hcm': 'TP.HCM',
            'hồ chí minh': 'TP.HCM',
            'ho chi minh': 'TP.HCM',
            'hcm': 'TP.HCM',
            'đà nẵng': 'Đà Nẵng',
            'da nang': 'Đà Nẵng',
            'dn': 'Đà Nẵng',
            'hải phòng': 'Hải Phòng',
            'hai phong': 'Hải Phòng',
            'hp': 'Hải Phòng',
        }
        
        normalized = location_text.strip().lower()
        return location_mapping.get(normalized, location_text.strip())
    
    def normalize_job_type(self, job_type_text: str) -> str:
        """Normalize job type to standard format"""
        if not job_type_text:
            return "Full-time"
        
        job_type_mapping = {
            'full time': 'Full-time',
            'full-time': 'Full-time',
            'part time': 'Part-time',
            'part-time': 'Part-time',
            'contract': 'Contract',
            'intern': 'Internship',
            'internship': 'Internship',
            'freelance': 'Freelance',
            'temporary': 'Temporary',
            'bán thời gian': 'Part-time',
            'toàn thời gian': 'Full-time',
            'thực tập': 'Internship',
        }
        
        normalized = job_type_text.strip().lower()
        return job_type_mapping.get(normalized, job_type_text.strip())
    
    def normalize_experience_level(self, experience_text: str) -> str:
        """Normalize experience level to standard format"""
        if not experience_text:
            return "Entry"
        
        experience_mapping = {
            'entry': 'Entry',
            'junior': 'Junior',
            'fresher': 'Entry',
            'new grad': 'Entry',
            'beginner': 'Entry',
            'mid': 'Mid',
            'mid-level': 'Mid',
            'intermediate': 'Mid',
            'senior': 'Senior',
            'lead': 'Lead',
            'manager': 'Manager',
            'director': 'Director',
            'executive': 'Executive',
            'mới tốt nghiệp': 'Entry',
            'fresher': 'Entry',
            'cần 1 năm kinh nghiệm': 'Entry',
            'cần 2 năm kinh nghiệm': 'Mid',
            'cần 3-5 năm kinh nghiệm': 'Senior',
            'trên 5 năm kinh nghiệm': 'Senior',
        }
        
        normalized = experience_text.strip().lower()
        return experience_mapping.get(normalized, experience_text.strip())
    
    def extract_skills_from_description(self, description: str) -> Dict[str, List[str]]:
        """Extract skills from job description"""
        if not description:
            return {"required": [], "nice_to_have": []}
        
        # Keywords for required skills
        required_keywords = [
            'yêu cầu', 'requirement', 'require', 'must have', 'cần có', 'bắt buộc',
            'requirement', 'require', 'must', 'need', 'should have', 'should'
        ]
        
        # Keywords for nice-to-have skills
        nice_to_have_keywords = [
            'ưu tiên', 'nice to have', 'plus', 'bonus', 'thêm vào', 'advantage',
            'preferred', 'advantage', 'benefit', 'good to have', 'would be nice'
        ]
        
        required_skills = []
        nice_to_have_skills = []
        
        # Common skill patterns
        skill_patterns = [
            r'\b(Python|Java|JavaScript|C\+\+|C#|Ruby|PHP|Go|Swift|Kotlin)\b',
            r'\b(SQL|MySQL|PostgreSQL|MongoDB|Redis)\b',
            r'\b(React|Vue|Angular|Node\.js|Django|Flask)\b',
            r'\b(AWS|Azure|GCP|Docker|Kubernetes)\b',
            r'\b(Git|GitHub|GitLab|Bitbucket)\b',
            r'\b(Excel|Word|PowerPoint|Outlook)\b',
            r'\b(Photoshop|Illustrator|Figma|Sketch)\b',
            r'\b(English|Tiếng Anh|Vietnamese|Tiếng Việt)\b',
        ]
        
        lines = description.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Check if this line contains skill-related keywords
            is_required_section = any(keyword in line_lower for keyword in required_keywords)
            is_nice_to_have_section = any(keyword in line_lower for keyword in nice_to_have_keywords)
            
            # Extract skills from this line
            for pattern in skill_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    skill = match.strip()
                    if is_required_section:
                        if skill not in required_skills:
                            required_skills.append(skill)
                    elif is_nice_to_have_section:
                        if skill not in nice_to_have_skills:
                            nice_to_have_skills.append(skill)
                    else:
                        # If no clear section, add to required (safer assumption)
                        if skill not in required_skills and skill not in nice_to_have_skills:
                            required_skills.append(skill)
        
        return {
            "required": required_skills,
            "nice_to_have": nice_to_have_skills
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common job board artifacts
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\t+', ' ', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[!]{3,}', '!', text)
        text = re.sub(r'[\?]{3,}', '?', text)
        
        return text.strip()
    
    def normalize_job_description(self, job: JobDescription) -> JobDescription:
        """Apply all normalization to a job description"""
        # Clean text fields
        job.title = self.clean_text(job.title)
        job.company = self.clean_text(job.company)
        job.location = self.normalize_location(job.location)
        job.description = self.clean_text(job.description)
        
        # Normalize structured fields
        job.job_type = self.normalize_job_type(job.job_type)
        job.experience_level = self.normalize_experience_level(job.experience_level)
        
        # Normalize skills
        if not job.skills_required and not job.skills_nice_to_have:
            # Extract skills from description if not provided
            skills = self.extract_skills_from_description(job.description)
            job.skills_required.extend(skills['required'])
            job.skills_nice_to_have.extend(skills['nice_to_have'])
        
        # Normalize requirements and benefits
        job.requirements = [self.clean_text(req) for req in job.requirements if req.strip()]
        job.benefits = [self.clean_text(benefit) for benefit in job.benefits if benefit.strip()]
        
        # Validate the result
        if not self.validate_job_description(job):
            self.logger.warning(f"Job description validation failed after normalization: {job.title}")
        
        return job


class SalaryParser:
    """Advanced salary parsing utilities"""
    
    @staticmethod
    def parse_salary_range(salary_text: str) -> Tuple[Optional[int], Optional[int], str]:
        """Parse salary text and return min, max, currency"""
        validator = JobDescriptionValidator()
        result = validator.normalize_salary(salary_text)
        return result['min'], result['max'], result['currency']
    
    @staticmethod
    def format_salary_display(min_salary: Optional[int], max_salary: Optional[int], currency: str) -> str:
        """Format salary for display"""
        if min_salary is None and max_salary is None:
            return "Thỏa thuận"
        
        if min_salary == max_salary:
            return f"{min_salary:,} {currency}"
        
        if min_salary and max_salary:
            return f"{min_salary:,} - {max_salary:,} {currency}"
        
        if min_salary:
            return f"Từ {min_salary:,} {currency}"
        
        if max_salary:
            return f"Đến {max_salary:,} {currency}"
        
        return "Thỏa thuận"