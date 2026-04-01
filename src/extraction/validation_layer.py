"""
Task 5 Phase 2: Validation + Confidence Layer
Cross-field validation, schema enforcement, and data integrity checks
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation strictness levels"""
    STRICT = 0.95  # > 95% confidence required
    PRODUCTION = 0.80  # > 80% confidence
    ACCEPTABLE = 0.65  # > 65% confidence
    WARNING = 0.50  # > 50% confidence (warn but allow)
    PERMISSIVE = 0.00  # Any value allowed


@dataclass
class ValidationResult:
    """Result of field validation"""
    field_name: str
    is_valid: bool
    confidence_score: float
    error_message: str = ""
    warnings: List[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class ExtractionValidation:
    """Complete validation result for extraction"""
    is_valid: bool
    total_fields: int
    valid_fields: int
    average_confidence: float
    field_results: Dict[str, ValidationResult]
    cross_field_issues: List[str]
    
    def get_summary(self) -> str:
        """Get human-readable validation summary"""
        return f"{self.valid_fields}/{self.total_fields} fields valid (avg confidence: {self.average_confidence:.2f})"


class FieldValidator:
    """Validates individual extracted fields"""
    
    # Validation patterns
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_PATTERN = r'^[\+\d\-\(\)\s]{7,20}$'
    YEAR_PATTERN = r'^\d{4}$'
    DURATION_PATTERN = r'^[0-9]+\.?[0-9]*$'
    
    @staticmethod
    def validate_email(email: str, confidence: float = 1.0) -> ValidationResult:
        """Validate email format"""
        result = ValidationResult(
            field_name='email',
            is_valid=False,
            confidence_score=confidence
        )
        
        if not email or not isinstance(email, str):
            result.error_message = "Email is empty or not a string"
            return result
        
        email = email.strip().lower()
        
        if not re.match(FieldValidator.EMAIL_PATTERN, email):
            result.error_message = f"Invalid email format: {email}"
            result.suggestions = [f"Check email format: {email}"]
            return result
        
        # Additional checks
        if email.count('@') != 1:
            result.error_message = "Email must contain exactly one @"
            return result
        
        parts = email.split('@')
        if len(parts[0]) < 1:
            result.error_message = "Email local part is too short"
            return result
        
        if '..' in parts[1]:
            result.error_message = "Email domain contains consecutive dots"
            return result
        
        result.is_valid = True
        return result
    
    @staticmethod
    def validate_phone(phone: str, confidence: float = 1.0) -> ValidationResult:
        """Validate phone number"""
        result = ValidationResult(
            field_name='phone',
            is_valid=False,
            confidence_score=confidence
        )
        
        if not phone or not isinstance(phone, str):
            result.error_message = "Phone is empty or not a string"
            return result
        
        phone = phone.strip()
        
        # Check format
        if not re.match(FieldValidator.PHONE_PATTERN, phone):
            result.error_message = f"Invalid phone format: {phone}"
            return result
        
        # Check digit count (should have 7-15 digit characters)
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) < 7 or len(digits) > 15:
            result.error_message = f"Phone should have 7-15 digits, got {len(digits)}"
            return result
        
        result.is_valid = True
        return result
    
    @staticmethod
    def validate_job_title(title: str, confidence: float = 1.0) -> ValidationResult:
        """Validate job title"""
        result = ValidationResult(
            field_name='job_title',
            is_valid=False,
            confidence_score=confidence
        )
        
        if not title or not isinstance(title, str):
            result.error_message = "Job title is empty or not a string"
            return result
        
        title = title.strip()
        
        if len(title) < 3:
            result.error_message = "Job title too short (< 3 characters)"
            return result
        
        if len(title) > 100:
            result.error_message = "Job title too long (> 100 characters)"
            result.suggestions = [f"Truncate: {title[:99]}"]
            return result
        
        # Should contain mostly letters
        letter_ratio = sum(1 for c in title if c.isalpha()) / len(title)
        if letter_ratio < 0.5:
            result.warnings = ["Contains unusual characters"]
        
        result.is_valid = True
        return result    
    
    @staticmethod
    def validate_years_experience(years: float, confidence: float = 1.0) -> ValidationResult:
        """Validate years of experience"""
        result = ValidationResult(
            field_name='years_experience',
            is_valid=False,
            confidence_score=confidence
        )
        
        if not isinstance(years, (int, float)):
            result.error_message = f"Years experience must be number, got {type(years)}"
            return result
        
        if years < 0:
            result.error_message = "Years experience cannot be negative"
            return result
        
        if years > 70:
            result.warnings = ["Possibly data entry error"]
        
        if confidence < 0.5:
            result.warnings.append("Low confidence in experience calculation")
        
        result.is_valid = True
        return result
    
    @staticmethod
    def validate_company_name(company: str, confidence: float = 1.0) -> ValidationResult:
        """Validate company name"""
        result = ValidationResult(
            field_name='company',
            is_valid=False,
            confidence_score=confidence
        )
        
        if not company or not isinstance(company, str):
            result.error_message = "Company name is empty or not a string"
            return result
        
        company = company.strip()
        
        if len(company) < 2:
            result.error_message = "Company name too short (< 2 characters)"
            return result
        
        if len(company) > 200:
            result.error_message = "Company name too long (> 200 characters)"
            return result
        
        result.is_valid = True
        return result
    
    @staticmethod
    def validate_skills(skills: List[str], confidence: float = 1.0) -> ValidationResult:
        """Validate skills list"""
        result = ValidationResult(
            field_name='skills',
            is_valid=False,
            confidence_score=confidence
        )
        
        if not isinstance(skills, list):
            result.error_message = "Skills must be a list"
            return result
        
        if len(skills) == 0:
            result.error_message = "Skills list is empty"
            result.suggestions = ["Extract at least one skill from CV"]
            return result
        
        if len(skills) > 50:
            result.warnings = [f"Truncating to top 50 of {len(skills)} skills"]
        
        result.is_valid = True
        
        return result


class CrossFieldValidator:
    """Validates relationships between fields"""
    
    @staticmethod
    def validate_consistency(extraction: Dict[str, Any]) -> List[str]:
        """Check for cross-field consistency issues"""
        issues = []
        
        # If has experience, should have some job title
        years = extraction.get('experience', {}).get('years', 0)
        job_title = extraction.get('professional', {}).get('job_title')
        
        if years > 2 and not job_title:
            issues.append("Has experience but no job title extracted")
        
        # Seniority should match years
        seniority = extraction.get('experience', {}).get('seniority', '').lower()
        
        if years < 2 and seniority in ['senior', 'principal', 'lead']:
            issues.append(f"Seniority '{seniority}' conflicts with {years} years experience")
        
        if years > 10 and seniority in ['junior']:
            issues.append(f"Seniority '{seniority}' conflicts with {years} years experience")
        
        # Skills and projects should relate
        skills = extraction.get('skills', [])
        projects = extraction.get('projects', [])
        
        if projects and not skills:
            issues.append("Has projects but no skills extracted")
        
        # Contact info completeness
        contact = extraction.get('contact', {})
        contact_fields = sum(1 for v in contact.values() if v)
        
        if contact_fields == 0:
            issues.append("No contact information extracted")
        elif contact_fields == 1:
            issues.append("Only one contact method found (email, phone, etc.)")
        
        return issues
    
    @staticmethod
    def validate_temporal_consistency(entries: List[Dict]) -> List[str]:
        """Check for temporal inconsistencies (gaps, overlaps, etc.)"""
        issues = []
        
        if not entries or len(entries) < 2:
            return issues
        
        # This would integrate with ExperienceEngine
        # Check for unrealistic gaps (>5 years)
        # etc.
        
        return issues


class ConfidenceThresholdValidator:
    """Enforces confidence thresholds by validation level"""
    
    def __init__(self, level: ValidationLevel = ValidationLevel.PRODUCTION):
        self.level = level
        self.threshold = level.value
    
    def should_accept_field(self, field_name: str, confidence: float) -> bool:
        """Check if field meets confidence threshold"""
        return confidence >= self.threshold
    
    def get_field_status(self, field_name: str, confidence: float) -> str:
        """Get status of field vs threshold"""
        if confidence >= self.threshold:
            return 'accepted'
        elif confidence >= 0.5:
            return 'warning'
        else:
            return 'rejected'


class DataIntegrityValidator:
    """Checks for data integrity issues"""
    
    @staticmethod
    def validate_no_nulls_in_required_fields(extraction: Dict, required_fields: Set[str]) -> List[str]:
        """Check that required fields are not null/empty"""
        issues = []
        
        for field in required_fields:
            value = extraction.get(field)
            if not value or (isinstance(value, (list, dict)) and len(value) == 0):
                issues.append(f"Required field '{field}' is empty")
        
        return issues
    
    @staticmethod
    def validate_no_duplicate_entries(experience_entries: List[Dict]) -> List[str]:
        """Check for duplicate experience entries"""
        issues = []
        seen = set()
        
        for entry in experience_entries:
            key = (
                entry.get('company', '').lower(),
                entry.get('position', '').lower()
            )
            
            if key in seen and key != ('', ''):
                issues.append(f"Duplicate entry: {entry.get('company')} - {entry.get('position')}")
            else:
                seen.add(key)
        
        return issues
    
    @staticmethod
    def validate_no_corrupted_data(extraction: Dict) -> List[str]:
        """Check for corrupted/malformed data"""
        issues = []
        
        # Check for strings that look corrupted
        for field, value in extraction.items():
            if isinstance(value, str) and len(value) > 0:
                # Check for excessive special characters
                special_chars = sum(1 for c in value if not c.isalnum() and c not in ' -._@+')
                if len(value) > 10 and special_chars / len(value) > 0.3:
                    issues.append(f"Field '{field}' may be corrupted (too many special chars)")
                
                # Check for random characters
                if value.count('\x00') > 0:
                    issues.append(f"Field '{field}' contains null characters")
        
        return issues


class ExtractionValidator:
    """Main validator orchestrating all validation layers"""
    
    def __init__(self, threshold_level: ValidationLevel = ValidationLevel.PRODUCTION):
        self.threshold_validator = ConfidenceThresholdValidator(threshold_level)
        self.data_integrity = DataIntegrityValidator()
        self.field_validator = FieldValidator()
        self.cross_field_validator = CrossFieldValidator()
    
    def validate_extraction(
        self,
        extraction: Dict[str, Any],
        required_fields: Optional[Set[str]] = None
    ) -> ExtractionValidation:
        """Validate complete extraction result"""
        
        field_results = {}
        valid_count = 0
        total_fields = 0
        confidence_sum = 0.0
        cross_field_issues = []
        
        # Validate individual fields
        if 'contact' in extraction:
            contact = extraction['contact']
            
            # Email validation
            if 'email' in contact and contact.get('email'):
                total_fields += 1
                email_value = contact['email'].get('value', '')
                email_conf = contact['email'].get('confidence', 0.5)
                result = self.field_validator.validate_email(email_value, email_conf)
                field_results['email'] = result
                if result.is_valid:
                    valid_count += 1
                confidence_sum += result.confidence_score
            
            # Phone validation
            if 'phone' in contact and contact.get('phone'):
                total_fields += 1
                phone_value = contact['phone'].get('value', '')
                phone_conf = contact['phone'].get('confidence', 0.5)
                result = self.field_validator.validate_phone(phone_value, phone_conf)
                field_results['phone'] = result
                if result.is_valid:
                    valid_count += 1
                confidence_sum += result.confidence_score
        
        # Validate professional fields
        if 'professional' in extraction:
            professional = extraction['professional']
            
            if 'job_title' in professional and professional.get('job_title'):
                total_fields += 1
                title_value = professional['job_title'].get('value', '')
                title_conf = professional['job_title'].get('confidence', 0.5)
                result = self.field_validator.validate_job_title(title_value, title_conf)
                field_results['job_title'] = result
                if result.is_valid:
                    valid_count += 1
                confidence_sum += result.confidence_score
        
        # Validate experience
        if 'experience' in extraction:
            experience = extraction['experience']
            
            if 'years' in experience and experience['years'] is not None:
                total_fields += 1
            if 'years' in experience and experience['years'] is not None:
                total_fields += 1
                years_value = experience['years']
                years_conf = experience.get('confidence', 0.5)
                result = self.field_validator.validate_years_experience(years_value, years_conf)
                field_results['years_experience'] = result
                if result.is_valid:
                    valid_count += 1
                confidence_sum += result.confidence_score        # Data integrity checks
        data_integrity_issues = self.data_integrity.validate_no_corrupted_data(extraction)
        cross_field_issues.extend(data_integrity_issues)
        
        # Cross-field consistency checks
        consistency_issues = self.cross_field_validator.validate_consistency(extraction)
        cross_field_issues.extend(consistency_issues)
        
        # Calculate average confidence
        avg_conf = confidence_sum / total_fields if total_fields > 0 else 0.0
        
        is_valid = valid_count == total_fields or (total_fields > 0 and valid_count / total_fields >= 0.8)
        
        return ExtractionValidation(
            is_valid=is_valid,
            total_fields=total_fields,
            valid_fields=valid_count,
            average_confidence=avg_conf,
            field_results=field_results,
            cross_field_issues=cross_field_issues
        )
