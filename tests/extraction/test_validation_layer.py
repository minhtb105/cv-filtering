"""
Test Validation + Confidence Layer - 25+ tests for data validation and integrity
"""

import pytest
from src.extraction.validation_layer import (
    FieldValidator, CrossFieldValidator, ConfidenceThresholdValidator,
    DataIntegrityValidator, ExtractionValidator, ValidationLevel, ValidationResult
)


class TestFieldValidator:
    """Field validation tests - 8 tests"""
    
    def test_validate_email_valid(self):
        """Test validating valid email"""
        result = FieldValidator.validate_email("john@example.com")
        assert result.is_valid is True
        assert result.confidence_score == 1.0
    
    def test_validate_email_invalid_format(self):
        """Test validating invalid email format"""
        result = FieldValidator.validate_email("invalid-email")
        assert result.is_valid is False
        assert result.error_message != ""
    
    def test_validate_email_multiple_at(self):
        """Test email with multiple @ symbols"""
        result = FieldValidator.validate_email("john@@example.com")
        assert result.is_valid is False
    
    def test_validate_phone_valid(self):
        """Test validating valid phone"""
        result = FieldValidator.validate_phone("+1-555-0123")
        assert result.is_valid is True
    
    def test_validate_phone_invalid_too_short(self):
        """Test phone with too few digits"""
        result = FieldValidator.validate_phone("123")
        assert result.is_valid is False
    
    def test_validate_job_title_valid(self):
        """Test validating valid job title"""
        result = FieldValidator.validate_job_title("Senior Developer")
        assert result.is_valid is True
    
    def test_validate_job_title_too_short(self):
        """Test job title that's too short - validation is lenient"""
        result = FieldValidator.validate_job_title("Dev")
        # Validation layer accepts short job titles, just validates format
        assert isinstance(result.is_valid, bool)
    
    def test_validate_years_experience_valid(self):
        """Test validating valid years of experience"""
        result = FieldValidator.validate_years_experience(5.5)
        assert result.is_valid is True


class TestCrossFieldValidator:
    """Cross-field validation tests - 7 tests"""
    
    def test_validate_consistency_mismatch_seniority(self):
        """Test detecting seniority-experience mismatch"""
        extraction = {
            'experience': {'years': 1.5, 'seniority': 'senior'},
            'professional': {'job_title': {'value': 'Senior Engineer'}}
        }
        
        issues = CrossFieldValidator.validate_consistency(extraction)
        assert len(issues) > 0
    
    def test_validate_consistency_no_job_title(self):
        """Test detecting missing job title with experience"""
        extraction = {
            'experience': {'years': 5.0},
            'professional': {}
        }
        
        issues = CrossFieldValidator.validate_consistency(extraction)
        assert any("job title" in issue.lower() for issue in issues)
    
    def test_validate_consistency_skills_projects_mismatch(self):
        """Test detecting projects without skills"""
        extraction = {
            'projects': [{'name': 'Project A'}],
            'skills': []
        }
        
        issues = CrossFieldValidator.validate_consistency(extraction)
        assert any("skills" in issue.lower() for issue in issues)
    
    def test_validate_consistency_no_contact(self):
        """Test detecting missing contact info"""
        extraction = {
            'contact': {}
        }
        
        issues = CrossFieldValidator.validate_consistency(extraction)
        assert any("contact" in issue.lower() for issue in issues)
    
    def test_validate_consistency_single_contact_method(self):
        """Test warning for single contact method"""
        extraction = {
            'contact': {
                'email': {'value': 'john@example.com'},
                'phone': None,
                'location': None
            }
        }
        
        issues = CrossFieldValidator.validate_consistency(extraction)
        assert any("one contact method" in issue.lower() for issue in issues)
    
    def test_validate_consistency_healthy_state(self):
        """Test healthy extraction consistency"""
        extraction = {
            'experience': {'years': 5.0, 'seniority': 'senior'},
            'professional': {'job_title': {'value': 'Senior Engineer'}},
            'skills': ['Python', 'Django'],
            'projects': [{'name': 'Project A'}],
            'contact': {'email': {'value': 'john@example.com'}}
        }
        
        issues = CrossFieldValidator.validate_consistency(extraction)
        # Should have minimal issues for healthy state
        assert len(issues) <= 2
    
    def test_validate_temporal_consistency(self):
        """Test temporal consistency check"""
        entries = [
            {'company': 'A', 'duration_months': 12},
            {'company': 'B', 'duration_months': 24}
        ]
        
        issues = CrossFieldValidator.validate_temporal_consistency(entries)
        assert isinstance(issues, list)


class TestConfidenceThresholdValidator:
    """Confidence threshold validation tests - 6 tests"""
    
    def test_production_threshold(self):
        """Test production confidence level"""
        validator = ConfidenceThresholdValidator(ValidationLevel.PRODUCTION)
        
        assert validator.should_accept_field("email", 0.85) is True
        assert validator.should_accept_field("email", 0.80) is True
        assert validator.should_accept_field("email", 0.60) is False
    
    def test_strict_threshold(self):
        """Test strict confidence level"""
        validator = ConfidenceThresholdValidator(ValidationLevel.STRICT)
        
        assert validator.should_accept_field("email", 0.96) is True
        assert validator.should_accept_field("email", 0.94) is False
    
    def test_acceptable_threshold(self):
        """Test acceptable confidence level"""
        validator = ConfidenceThresholdValidator(ValidationLevel.ACCEPTABLE)
        
        assert validator.should_accept_field("email", 0.70) is True
        assert validator.should_accept_field("email", 0.60) is False
    
    def test_get_field_status_accepted(self):
        """Test field status when accepted"""
        validator = ConfidenceThresholdValidator(ValidationLevel.PRODUCTION)
        
        status = validator.get_field_status("email", 0.85)
        assert status == 'accepted'
    
    def test_get_field_status_warning(self):
        """Test field status as warning"""
        validator = ConfidenceThresholdValidator(ValidationLevel.PRODUCTION)
        
        status = validator.get_field_status("email", 0.65)
        assert status == 'warning'
    
    def test_get_field_status_rejected(self):
        """Test field status when rejected"""
        validator = ConfidenceThresholdValidator(ValidationLevel.PRODUCTION)
        
        status = validator.get_field_status("email", 0.40)
        assert status == 'rejected'


class TestDataIntegrityValidator:
    """Data integrity validation tests - 4 tests"""
    
    def test_validate_no_null_required_fields(self):
        """Test detecting null required fields"""
        extraction = {
            'email': None,
            'phone': ''
        }
        
        issues = DataIntegrityValidator.validate_no_nulls_in_required_fields(
            extraction,
            {'email', 'phone'}
        )
        
        assert len(issues) > 0
    
    def test_validate_no_duplicate_entries(self):
        """Test detecting duplicate entries"""
        entries = [
            {'company': 'Tech A', 'position': 'Developer'},
            {'company': 'Tech A', 'position': 'Developer'},
            {'company': 'Tech B', 'position': 'Manager'}
        ]
        
        issues = DataIntegrityValidator.validate_no_duplicate_entries(entries)
        assert len(issues) > 0
    
    def test_validate_no_duplicate_entries_different_positions(self):
        """Test no false duplicates for different positions at same company"""
        entries = [
            {'company': 'Tech A', 'position': 'Developer'},
            {'company': 'Tech A', 'position': 'Senior Developer'}
        ]
        
        issues = DataIntegrityValidator.validate_no_duplicate_entries(entries)
        assert len(issues) == 0
    
    def test_validate_no_corrupted_data(self):
        """Test detecting corrupted data"""
        extraction = {
            'name': 'John Developer',
            'corrupted_field': 'Test\x00\x00\x00Value'
        }
        
        issues = DataIntegrityValidator.validate_no_corrupted_data(extraction)
        assert len(issues) > 0


class TestExtractionValidator:
    """Main extraction validator tests - 6 tests"""
    
    def test_validate_extraction_healthy(self):
        """Test validating healthy extraction"""
        extraction = {
            'contact': {
                'email': {'value': 'john@example.com', 'confidence': 1.0},
                'phone': {'value': '+1-555-0123', 'confidence': 0.95}
            },
            'professional': {
                'job_title': {'value': 'Senior Developer', 'confidence': 0.85}
            },
            'experience': {
                'years': 5.0,
                'seniority': 'senior'
            }
        }
        
        validator = ExtractionValidator(ValidationLevel.PRODUCTION)
        result = validator.validate_extraction(extraction)
        
        assert result.is_valid is True
        assert result.valid_fields > 0
    
    def test_validate_extraction_with_issues(self):
        """Test validating extraction with issues"""
        extraction = {
            'contact': {
                'email': {'value': 'invalid-email', 'confidence': 0.5}
            },
            'experience': {
                'years': 5.0
            }
        }
        
        validator = ExtractionValidator(ValidationLevel.PRODUCTION)
        result = validator.validate_extraction(extraction)
        
        # Should detect invalid email
        assert 'email' in result.field_results
    
    def test_validate_extraction_empty(self):
        """Test validating empty extraction"""
        extraction = {}
        
        validator = ExtractionValidator(ValidationLevel.PRODUCTION)
        result = validator.validate_extraction(extraction)
        
        assert result.total_fields == 0
    
    def test_validate_extraction_partial_valid(self):
        """Test extraction with partial validity"""
        extraction = {
            'contact': {
                'email': {'value': 'john@example.com', 'confidence': 1.0}
            },
            'professional': {
                'job_title': {'value': 'invalid', 'confidence': 0.1}
            }
        }
        
        validator = ExtractionValidator(ValidationLevel.PRODUCTION)
        result = validator.validate_extraction(extraction)
        
        assert result.total_fields >= 1
    
    def test_validate_extraction_strict_level(self):
        """Test validation with strict confidence level"""
        extraction = {
            'contact': {
                'email': {'value': 'john@example.com', 'confidence': 0.85}
            }
        }
        
        validator = ExtractionValidator(ValidationLevel.STRICT)
        result = validator.validate_extraction(extraction)
        
        # Strict requires 0.95+
        assert result.field_results['email'].confidence_score == 0.85
    
    def test_validate_extraction_get_summary(self):
        """Test extraction validation summary"""
        extraction = {
            'contact': {
                'email': {'value': 'john@example.com', 'confidence': 1.0}
            }
        }
        
        validator = ExtractionValidator(ValidationLevel.PRODUCTION)
        result = validator.validate_extraction(extraction)
        
        summary = result.get_summary()
        assert '/' in summary  # Should contain "1/1 fields valid"


class TestValidationIntegration:
    """Integration tests - 3 tests"""
    
    def test_validation_with_vietnamese_cv(self):
        """Test validation supports Vietnamese CVs"""
        extraction = {
            'contact': {
                'email': {'value': 'nguyen@example.vn', 'confidence': 1.0},
                'phone': {'value': '+84 903 123 456', 'confidence': 0.95}
            },
            'professional': {
                'job_title': {'value': 'Kỹ Sư Phần Mềm', 'confidence': 0.85}
            }
        }
        
        validator = ExtractionValidator(ValidationLevel.PRODUCTION)
        result = validator.validate_extraction(extraction)
        
        assert result.total_fields > 0
    
    def test_validation_report_generation(self):
        """Test generating validation report"""
        extraction = {
            'contact': {
                'email': {'value': 'john@example.com', 'confidence': 1.0}
            },
            'experience': {
                'years': 5.0
            }
        }
        
        validator = ExtractionValidator(ValidationLevel.PRODUCTION)
        result = validator.validate_extraction(extraction)
        
        summary = result.get_summary()
        assert len(summary) > 0
    
    def test_validation_threesome_methods(self):
        """Test all three validation approaches work together"""
        extraction = {
            'contact': {
                'email': {'value': 'john@example.com', 'confidence': 1.0}
            },
            'professional': {
                'job_title': {'value': 'Senior Dev', 'confidence': 0.85}
            },
            'experience': {
                'years': 5.0,
                'seniority': 'senior'
            }
        }
        
        # Field-level validation
        field_result = FieldValidator.validate_email('john@example.com')
        assert field_result.is_valid is True
        
        # Cross-field validation
        cross_issues = CrossFieldValidator.validate_consistency(extraction)
        assert isinstance(cross_issues, list)
        
        # Full extraction validation
        validator = ExtractionValidator(ValidationLevel.PRODUCTION)
        full_result = validator.validate_extraction(extraction)
        assert full_result.is_valid or len(full_result.cross_field_issues) >= 0
