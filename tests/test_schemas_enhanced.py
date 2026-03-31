"""
Tests for Enhanced Schemas - Phase 3B
Comprehensive validation tests for all new models
"""

import pytest
from datetime import datetime
from src.schemas import (
    # Validators
    PhoneValidator,
    DateValidator,
    
    # Models
    ContactInfo,
    Certification,
    Language,
    Skill,
    CareerProgression,
    Project,
    CandidateProfile,
    MatchingScore,
    LocationFormat,
    ParsingMetadata,
    DerivedFields,
    ExtractionMethod,
    CEFRLEVEL,
    SeniorityLevel,
)


# ============================================================================
# PHONE VALIDATION TESTS
# ============================================================================

class TestPhoneValidator:
    """Test E.164 phone validation and normalization"""
    
    def test_normalize_e164_vietnam_with_zero(self):
        """Vietnamese phone with 0 prefix → +84 format"""
        phone = "0912345678"
        result = PhoneValidator.normalize_e164(phone)
        assert result == "+84912345678"
    
    def test_normalize_e164_vietnam_with_plus(self):
        """Vietnamese phone with +84 prefix"""
        phone = "+84912345678"
        result = PhoneValidator.normalize_e164(phone)
        assert result == "+84912345678"
    
    def test_normalize_e164_us_10_digits(self):
        """US phone 10 digits → +1"""
        phone = "2025551234"
        result = PhoneValidator.normalize_e164(phone)
        assert result == "+12025551234"
    
    def test_normalize_with_separators(self):
        """Phone with separators"""
        phone = "(202) 555-1234"
        result = PhoneValidator.normalize_e164(phone)
        assert result == "+12025551234"
    
    def test_normalize_with_spaces(self):
        """Phone with spaces"""
        phone = "+84 912 345 678"
        result = PhoneValidator.normalize_e164(phone)
        assert result == "+84912345678"
    
    def test_invalid_phone(self):
        """Invalid phone returns None"""
        phone = "abc123xyz"
        result = PhoneValidator.normalize_e164(phone)
        assert result is None
    
    def test_empty_phone(self):
        """Empty phone returns None"""
        assert PhoneValidator.normalize_e164("") is None
        assert PhoneValidator.normalize_e164(None) is None


# ============================================================================
# DATE VALIDATION TESTS
# ============================================================================

class TestDateValidator:
    """Test date normalization"""
    
    def test_normalize_date_yyyy_mm(self):
        """YYYY-MM format"""
        result = DateValidator.normalize_date("2024-01")
        assert result == "2024-01"
    
    def test_normalize_date_mm_yyyy(self):
        """MM/YYYY format → YYYY-MM"""
        result = DateValidator.normalize_date("01/2024")
        assert result == "2024-01"
    
    def test_normalize_date_month_year(self):
        """Month Year format"""
        result = DateValidator.normalize_date("January 2024")
        assert result == "2024-01"
    
    def test_normalize_date_short_month(self):
        """Short month format"""
        result = DateValidator.normalize_date("Jan 2024")
        assert result == "2024-01"
    
    def test_normalize_date_full_date(self):
        """Full date format"""
        result = DateValidator.normalize_date("2024-01-15")
        assert result == "2024-01"
    
    def test_normalize_current_keyword(self):
        """Present/Current keywords"""
        assert DateValidator.normalize_date("Present") is None
        assert DateValidator.normalize_date("Current") is None
        assert DateValidator.normalize_date("Ongoing") is None
    
    def test_compute_months_duration(self):
        """Compute duration between dates"""
        months = DateValidator.compute_months("2022-01", "2024-01")
        assert months == 24
    
    def test_compute_months_same_month(self):
        """Same month duration"""
        months = DateValidator.compute_months("2024-01", "2024-01")
        assert months == 0
    
    def test_compute_months_current(self):
        """Current date computation (approximate)"""
        # Just test it returns a positive number
        months = DateValidator.compute_months("2024-01", None)
        assert months > 0


# ============================================================================
# CONTACT INFO TESTS
# ============================================================================

class TestContactInfo:
    """Test contact information validation"""
    
    def test_phone_normalization_on_creation(self):
        """Phone auto-normalizes on creation"""
        contact = ContactInfo(
            name="John Doe",
            email="john@example.com",
            phone="0912345678"  # Vietnam format
        )
        assert contact.phone == "+84912345678"
    
    def test_location_format(self):
        """Location structure"""
        contact = ContactInfo(
            name="John Doe",
            location=LocationFormat(
                city="Ho Chi Minh",
                country="Vietnam",
                country_code="VN",
                remote_eligible=True
            )
        )
        assert contact.location.city == "Ho Chi Minh"
        assert str(contact.location) == "Ho Chi Minh, Vietnam"
    
    def test_invalid_phone_raises_error(self):
        """Invalid phone raises validation error"""
        with pytest.raises(ValueError):
            ContactInfo(
                name="John",
                phone="invalid_number"
            )


# ============================================================================
# CERTIFICATION TESTS
# ============================================================================

class TestCertification:
    """Test certification model"""
    
    def test_certification_creation(self):
        """Create certification with proper dates"""
        cert = Certification(
            name="AWS Solutions Architect",
            issuer="Amazon Web Services",
            issue_date="2023-01",
            expiry_date="2025-01",
            credential_id="CERT-123456"
        )
        assert cert.name == "AWS Solutions Architect"
        assert cert.is_current is True
    
    def test_certification_date_normalization(self):
        """Dates auto-normalize"""
        cert = Certification(
            name="AWS",
            issuer="AWS",
            issue_date="Jan 2023",
            expiry_date="01/2025"
        )
        assert cert.issue_date == "2023-01"
        assert cert.expiry_date == "2025-01"
    
    def test_certification_date_order_validation(self):
        """Issue date cannot be after expiry date"""
        with pytest.raises(ValueError):
            Certification(
                name="AWS",
                issuer="AWS",
                issue_date="2025-01",
                expiry_date="2023-01"
            )
    
    def test_certification_non_expiring(self):
        """Non-expiring certification"""
        cert = Certification(
            name="Bachelor's Degree",
            issuer="MIT",
            issue_date="2020-05",
            expiry_date=None
        )
        assert cert.expiry_date is None


# ============================================================================
# LANGUAGE TESTS
# ============================================================================

class TestLanguage:
    """Test language model"""
    
    def test_language_cefr_levels(self):
        """All CEFR levels supported"""
        for level in ["A1", "A2", "B1", "B2", "C1", "C2", "NATIVE", "FLUENT"]:
            lang = Language(
                name="English",
                cefr_level=CEFRLEVEL(level)
            )
            assert lang.cefr_level == CEFRLEVEL(level)
    
    def test_native_language(self):
        """Native language flag"""
        lang = Language(
            name="Vietnamese",
            cefr_level=CEFRLEVEL.NATIVE,
            native=True
        )
        assert lang.native is True


# ============================================================================
# SKILL TESTS
# ============================================================================

class TestSkill:
    """Test skill model with normalization"""
    
    def test_skill_normalization(self):
        """Skill name auto-normalizes"""
        skill = Skill(
            name="Python 3.10"
        )
        # Normalization removes versions and numbers
        assert skill.normalized_name is not None
        assert "python" in skill.normalized_name.lower()
    
    def test_skill_with_evidence(self):
        """Skill with evidence linking"""
        from src.schemas import SkillEvidence
        
        skill = Skill(
            name="React.js",
            years_experience=3,
            confidence=0.9,
            evidence=[
                SkillEvidence(
                    skill_name="React",
                    context="E-commerce Platform",
                    evidence_text="Built responsive UI components with React",
                    metrics=["40% faster page load"],
                    confidence=0.95
                )
            ]
        )
        assert len(skill.evidence) == 1
        assert skill.evidence[0].confidence == 0.95


# ============================================================================
# CAREER PROGRESSION TESTS
# ============================================================================

class TestCareerProgression:
    """Test experience entry"""
    
    def test_duration_auto_computation(self):
        """Duration auto-computed from dates"""
        exp = CareerProgression(
            company="Tech Corp",
            title="Senior Engineer",
            start_date="2022-01",
            end_date="2024-01"
        )
        assert exp.duration_months == 24
    
    def test_current_role_detection(self):
        """Current role detected when no end_date"""
        exp = CareerProgression(
            company="Tech Corp",
            title="Senior Engineer",
            start_date="2023-01"
            # No end_date
        )
        assert exp.is_current is True
        assert exp.end_date is None
    
    def test_past_role_detection(self):
        """Past role detected with end_date"""
        exp = CareerProgression(
            company="Old Corp",
            title="Junior Engineer",
            start_date="2020-01",
            end_date="2022-01"
        )
        assert exp.is_current is False


# ============================================================================
# PROJECT TESTS
# ============================================================================

class TestProject:
    """Test project model"""
    
    def test_project_duration_computation(self):
        """Project duration auto-computed"""
        project = Project(
            name="E-commerce Platform",
            role="Lead Developer",
            start_date="2023-01",
            end_date="2024-06"
        )
        assert project.duration_months == 17
    
    def test_project_impact_scoring(self):
        """Project impact scores"""
        project = Project(
            name="Infrastructure Optimization",
            role="Architect",
            complexity_score=5,
            impact_score=5,
            metrics=["30% cost reduction", "50% faster deployment"]
        )
        assert project.complexity_score == 5
        assert project.impact_score == 5


# ============================================================================
# DERIVED FIELDS TESTS
# ============================================================================

class TestDerivedFields:
    """Test auto-computed fields"""
    
    def test_seniority_computation(self):
        """Seniority computed from experience"""
        assert DerivedFields.compute_seniority(12) == SeniorityLevel.JUNIOR  # <2 years
        assert DerivedFields.compute_seniority(36) == SeniorityLevel.MID  # 3 years
        assert DerivedFields.compute_seniority(72) == SeniorityLevel.SENIOR  # 6 years
        assert DerivedFields.compute_seniority(132) == SeniorityLevel.LEAD  # 11 years
        assert DerivedFields.compute_seniority(180) == SeniorityLevel.PRINCIPAL  # 15 years


# ============================================================================
# CANDIDATE PROFILE TESTS
# ============================================================================

class TestCandidateProfile:
    """Test complete candidate profile"""
    
    def test_candidate_profile_creation(self):
        """Full profile creation"""
        profile = CandidateProfile(
            contact=ContactInfo(
                name="Alice Engineer",
                email="alice@example.com",
                phone="0912345678"
            ),
            skills=[
                Skill(name="Python", years_experience=5, confidence=0.95),
                Skill(name="React", years_experience=3, confidence=0.85)
            ],
            experience=[
                CareerProgression(
                    company="Tech Corp",
                    title="Senior Engineer",
                    start_date="2022-01",
                    end_date="2024-01"
                )
            ]
        )
        assert len(profile.skills) == 2
        assert profile.contact.phone == "+84912345678"
    
    def test_derived_fields_computation(self):
        """Compute all derived fields"""
        profile = CandidateProfile(
            skills=[
                Skill(name="Python", confidence=0.9),
                Skill(name="React", confidence=0.8),
                Skill(name="Django", confidence=0.85)
            ],
            experience=[
                CareerProgression(
                    company="Company A",
                    title="Engineer",
                    start_date="2022-01",
                    end_date="2023-01"  # 12 months
                ),
                CareerProgression(
                    company="Company B",
                    title="Senior Engineer",
                    start_date="2023-01",
                    end_date="2024-01"  # 12 months
                )
            ]
        )
        
        derived = profile.compute_derived_fields()
        
        # Total: 24 months (12 + 12)
        assert derived.total_experience_months == 24
        assert derived.seniority == SeniorityLevel.MID  # 2 years = MID
        assert derived.skill_count == 3
        assert derived.current_role == "Senior Engineer"
        assert derived.years_in_current_role > 0

# ============================================================================
# MATCHING SCORE TESTS
# ============================================================================

class TestMatchingScore:
    """Test matching score computation"""
    
    def test_overall_score_computation(self):
        """Compute weighted overall score"""
        match = MatchingScore(
            candidate_id="C001",
            job_id="J001",
            skill_match=0.9,
            experience_match=0.8,
            education_fit=0.7,
            location_fit=0.6,
            language_fit=0.9
        )
        
        # Default weights: skills 35%, experience 35%, education 20%, location 5%, language 5%
        overall = match.compute_overall_score()
        
        expected = (0.9 * 0.35) + (0.8 * 0.35) + (0.7 * 0.20) + (0.6 * 0.05) + (0.9 * 0.05)
        assert abs(overall - expected) < 0.01
        assert match.match_percentage == round(overall * 100, 1)
    
    def test_missing_skills_tracking(self):
        """Track missing required and preferred skills"""
        match = MatchingScore(
            candidate_id="C001",
            job_id="J001",
            missing_required_skills=["Kubernetes", "AWS"],
            missing_preferred_skills=["Machine Learning"],
            skill_match=0.5
        )
        assert len(match.missing_required_skills) == 2
        assert len(match.missing_preferred_skills) == 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests"""
    
    def test_full_cv_parsing_workflow(self):
        """Simulate full CV parsing workflow"""
        profile = CandidateProfile(
            contact=ContactInfo(
                name="Bob Senior",
                email="bob@example.com",
                phone="+84987654321",
                location=LocationFormat(
                    city="Ho Chi Minh",
                    country="Vietnam",
                    country_code="VN",
                    remote_eligible=True
                )
            ),
            summary="Experienced software engineer with 10+ years",
            skills=[
                Skill(
                    name="Python",
                    years_experience=10,
                    confidence=0.95,
                    level=SeniorityLevel.SENIOR
                )
            ],
            experience=[
                CareerProgression(
                    company="Startup A",
                    title="Engineer",
                    start_date="2015-01",  # Adjusted to 9 years total
                    end_date="2018-01",
                    skills_used=["Python", "Django"]
                ),
                CareerProgression(
                    company="Tech Corp",
                    title="Senior Engineer",
                    start_date="2018-01",  # 2018-01 to 2024-01 = 6 years
                    skills_used=["Python", "React", "AWS"]
                )
            ],
            education=[
                {
                    "institution": "Stanford",
                    "degree": "Bachelor",
                    "field_of_study": "Computer Science"
                }
            ],
            certifications=[
                Certification(
                    name="AWS Solutions Architect",
                    issuer="AWS",
                    issue_date="2022-01"
                )
            ],
            languages=[
                Language(name="English", cefr_level=CEFRLEVEL.C2),
                Language(name="Vietnamese", cefr_level=CEFRLEVEL.NATIVE, native=True)
            ],
            parsing_metadata=ParsingMetadata(
                parser_version="1.0",
                extraction_method=ExtractionMethod.PYMUPDF,
                confidence_score=0.92
            )
        )
        
        # Compute derived fields
        profile.derived_fields = profile.compute_derived_fields()
        
        # Verify
        assert profile.contact.phone == "+84987654321"
        assert profile.derived_fields.total_experience_months > 0
        # ~11 years total (varies with current date) = SENIOR or LEAD
        assert profile.derived_fields.seniority in [SeniorityLevel.SENIOR, SeniorityLevel.LEAD]
        assert len(profile.languages) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
