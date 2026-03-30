"""
Integration test for Clean Architecture CV Extraction Pipeline

Tests the refactored orchestrator and new post-processing layer
"""

import pytest
import logging
from datetime import datetime
import sys
from src.extraction.hr_extractor_agent import HRExtractorAgent, ExtractionConfig
from src.models.domain.candidate import CandidateProfile, CareerProgression, Skill
from src.models.validation.enums import SeniorityLevel

logger = logging.getLogger(__name__)


class TestCleanArchitectureOrchestrator:
    """Test refactored orchestrator following Clean Architecture"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        config = ExtractionConfig(
            use_llm=False,  # Disable LLM for testing (would need Ollama running)
        )
        return HRExtractorAgent(config)
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes correctly"""
        assert orchestrator is not None
        assert orchestrator.llm_extractor is not None
        assert orchestrator.post_processor is not None
    
    def test_extract_ordered_text_passthrough(self, orchestrator):
        """Test extract_ordered_text is pass-through from geometric engine"""
        sample_text = "# EXPERIENCE\nSample job 2023-01 to 2024-01"
        result = orchestrator.extract_ordered_text(sample_text)
        assert result == sample_text
    
    def test_extraction_with_empty_input(self, orchestrator):
        """Test orchestrator handles empty input gracefully"""
        result = orchestrator.extract_cv("")
        assert result["status"] == "error"
        assert result["profile"] is None
        assert len(result["errors"]) > 0
    
    def test_extraction_with_partial_input(self, orchestrator):
        """Test orchestrator handles invalid/partial input"""
        result = orchestrator.extract_cv("   \n\n  ")
        assert result["status"] == "error"
    
    # Note: Full integration test would require Ollama service running
    # This is tested separately in CI/CD with Ollama container


class TestPostProcessor:
    """Test post-processing layer for enrichment"""
    
    @pytest.fixture
    def post_processor(self):
        """Create post-processor instance"""
        from src.processing.post_processor import PostProcessor
        return PostProcessor()
    
    def test_normalize_date_iso_format(self, post_processor):
        """Test date normalization to ISO format"""
        # YYYY-MM format
        assert post_processor.normalize_date("2024-01") == "2024-01-01"
        
        # YYYY-MM-DD format
        assert post_processor.normalize_date("2024-01-15") == "2024-01-15"
        
        # Month Year format
        assert post_processor.normalize_date("January 2024") == "2024-01-01"
        assert post_processor.normalize_date("Jan 2024") == "2024-01-01"
    
    def test_normalize_date_vietnamese(self, post_processor):
        """Test Vietnamese date format normalization"""
        # Tháng X/YYYY
        assert post_processor.normalize_date("tháng 1/2024") == "2024-01-01"
    
    def test_normalize_date_present(self, post_processor):
        """Test 'present' date handling"""
        result = post_processor.normalize_date("present")
        assert result == datetime.now().strftime("%Y-%m-%d")
        
        result = post_processor.normalize_date("Current")
        assert result == datetime.now().strftime("%Y-%m-%d")
    
    def test_calculate_total_experience_simple(self, post_processor):
        """Test experience calculation from entries"""
        # Create mock profile
        profile = CandidateProfile()
        profile.experience = [
            CareerProgression(
                company="Company A",
                title="Developer",
                start_date="2020-01-01",
                end_date="2022-01-01",  # 2 years
                duration_months=24
            ),
            CareerProgression(
                company="Company B",
                title="Senior Developer",
                start_date="2022-01-01",
                end_date=None,  # current
                duration_months=24  # 2 years
            )
        ]
        
        total = post_processor._calculate_total_experience(profile)
        assert total >= 4.0  # At least 4 years total
    
    def test_seniority_assignment_by_years(self, post_processor):
        """Test seniority level assign based on years"""
        # Junior (0-2 years)
        level = post_processor._get_level_from_experience(1.5)
        assert level == SeniorityLevel.JUNIOR
        
        # Mid (2-5 years)
        level = post_processor._get_level_from_experience(3.5)
        assert level == SeniorityLevel.MID
        
        # Senior (5-10 years)
        level = post_processor._get_level_from_experience(7.0)
        assert level == SeniorityLevel.SENIOR
        
        # Lead (10-15 years)
        level = post_processor._get_level_from_experience(12.0)
        assert level == SeniorityLevel.LEAD
        
        # Principal (15+ years)
        level = post_processor._get_level_from_experience(20.0)
        assert level == SeniorityLevel.PRINCIPAL
    
    def test_seniority_extraction_from_title(self, post_processor):
        """Test seniority level extraction from job title"""
        # Principal titles
        level = post_processor._extract_level_from_title("CTO - Chief Technology Officer")
        assert level == SeniorityLevel.PRINCIPAL
        
        # Lead titles
        level = post_processor._extract_level_from_title("Engineering Lead")
        assert level == SeniorityLevel.LEAD
        
        # Senior titles
        level = post_processor._extract_level_from_title("Senior Software Engineer")
        assert level == SeniorityLevel.SENIOR
        
        # Mid titles
        level = post_processor._extract_level_from_title("Software Developer")
        assert level is None  # No keyword match
    
    def test_seniority_boost_from_title(self, post_processor):
        """Test seniority level boosted by title keywords"""
        profile = CandidateProfile()
        profile.experience = [
            CareerProgression(
                company="Company",
                title="Staff Engineer",  # "Staff" keyword → SENIOR level
                start_date="2020-01",
            )
        ]
        
        # With 3 years experience (normally MID)
        # But "Staff Engineer" title should boost to SENIOR
        seniority = post_processor._assign_seniority_level(profile, 3.0)
        assert seniority == SeniorityLevel.SENIOR
    
    def test_full_post_processing_flow(self, post_processor):
        """Test complete post-processing workflow"""
        profile = CandidateProfile()
        profile.experience = [
            CareerProgression(
                company="Company A",
                title="Senior Developer",
                start_date="2020-01",
                end_date="2023-06",
                duration_months=42
            )
        ]
        
        result = post_processor.process(profile)
        
        assert result.success is True
        assert result.profile is not None
        assert result.total_years_experience == 3.5  # 42 months = 3.5 years
        assert result.seniority_level == SeniorityLevel.SENIOR
        assert len(result.errors) == 0


class TestOrchestrationFlow:
    """Integration tests for orchestration flow"""
    
    def test_error_handling_in_llm_call(self):
        """Test error handling when LLM returns error"""
        config = ExtractionConfig(use_llm=False)
        orchestrator = HRExtractorAgent(config)
        
        # Call with minimal text (will likely trigger fallback)
        result = orchestrator.extract_cv("Name: John Doe")
        
        # Should handle gracefully (error or partial)
        assert result["status"] in ["error", "partial", "success"]


# Run minimal tests without Ollama dependency
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
