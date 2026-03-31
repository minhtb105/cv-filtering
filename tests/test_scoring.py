"""Tests for scoring layer."""

from src.scoring import (
    SkillScorer,
    ExperienceScorer,
    EducationScorer,
    InterviewScorer,
    CompositeScorer,
)


class TestSkillScorer:
    """Test skill scorer."""
    
    def test_skill_score_perfect_match(self):
        """Test perfect skill match."""
        scorer = SkillScorer()
        
        cv_data = {"skills": ["Python", "SQL", "Docker"]}
        jd_data = {"skills": ["Python", "SQL"]}
        
        score = scorer.score(cv_data, jd_data)
        assert score >= 80  # Should have high score
    
    def test_skill_score_no_match(self):
        """Test no skill match."""
        scorer = SkillScorer()
        
        cv_data = {"skills": ["Java", "PHP"]}
        jd_data = {"skills": ["Python", "SQL"]}
        
        score = scorer.score(cv_data, jd_data)
        assert score < 50  # Should have low score
    
    def test_skill_score_no_jd_skills(self):
        """Test scoring with no JD skills."""
        scorer = SkillScorer()
        
        cv_data = {"skills": ["Python"]}
        jd_data = {}
        
        score = scorer.score(cv_data, jd_data)
        assert score == 50  # Default score


class TestExperienceScorer:
    """Test experience scorer."""
    
    def test_experience_score_sufficient(self):
        """Test sufficient experience."""
        scorer = ExperienceScorer()
        
        cv_data = {
            "total_experience_years": 5,
            "seniority_level": "senior",
        }
        jd_data = {
            "min_experience_years": 3,
            "required_seniority": "mid",
        }
        
        score = scorer.score(cv_data, jd_data)
        assert score > 70
    
    def test_experience_score_insufficient(self):
        """Test insufficient experience."""
        scorer = ExperienceScorer()
        
        cv_data = {
            "total_experience_years": 1,
            "seniority_level": "junior",
        }
        jd_data = {
            "min_experience_years": 5,
            "required_seniority": "senior",
        }
        
        score = scorer.score(cv_data, jd_data)
        assert score < 50


class TestEducationScorer:
    """Test education scorer."""
    
    def test_degree_match(self):
        """Test degree matching."""
        scorer = EducationScorer()
        
        cv_data = {
            "education": [{"degree_type": "Bachelors"}],
            "certifications": [],
        }
        jd_data = {
            "required_degree": "Bachelors",
        }
        
        score = scorer.score(cv_data, jd_data)
        assert score >= 85  # Close match (70% degree + cert scoring)
    
    def test_degree_overqualified(self):
        """Test overqualified education."""
        scorer = EducationScorer()
        
        cv_data = {
            "education": [{"degree_type": "Master"}],
            "certifications": [],
        }
        jd_data = {
            "required_degree": "Bachelors",
        }
        
        score = scorer.score(cv_data, jd_data)
        assert score >= 80  # Bonus for higher degree (70% degree match)


class TestInterviewScorer:
    """Test interview scorer."""
    
    def test_interview_scoring(self):
        """Test interview scoring."""
        scorer = InterviewScorer()
        
        cv_data = {}
        jd_data = {}
        interview_result = {
            "technical_score": 85,
            "soft_skills_score": 90,
            "cultural_fit_score": 80,
        }
        
        score = scorer.score(cv_data, jd_data, interview_result)
        assert 80 <= score <= 90
    
    def test_no_interview_data(self):
        """Test scoring without interview data."""
        scorer = InterviewScorer()
        
        cv_data = {}
        jd_data = {}
        
        score = scorer.score(cv_data, jd_data, None)
        assert score == 50  # Default


class TestCompositeScorer:
    """Test composite scorer."""
    
    def test_composite_score_calculation(self):
        """Test composite score calculation."""
        scorer = CompositeScorer()
        
        cv_data = {
            "skills": ["Python"],
            "total_experience_years": 5,
            "seniority_level": "mid",
            "education": [{"degree_type": "Bachelors"}],
            "certifications": [],
        }
        
        jd_data = {
            "skills": ["Python"],
            "min_experience_years": 3,
            "required_seniority": "mid",
            "required_degree": "Bachelors",
        }
        
        scores = scorer.score(cv_data, jd_data)
        
        assert "composite_score" in scores
        assert 0 <= scores["composite_score"] <= 100
        assert scores["has_interview"] is False    
    def test_weight_update(self):
        """Test updating scorer weights."""
        scorer = CompositeScorer()
        
        new_weights = {
            "skill": 0.4,
            "experience": 0.3,
            "education": 0.2,
            "interview": 0.1,
        }
        
        scorer.update_weights(new_weights)
        current = scorer.get_weights()
        
        assert current == new_weights
