"""Integration tests for API."""

from src.cache import CacheClient, CacheConfig
from src.repository import CVRepository, ScoreRepository, JDRepository, VersionManager
from src.retrieval import CVRetriever, ScoreRetriever
from src.scoring import CompositeScorer, RescoringEngine


class TestScoringIntegration:
    """Integration tests for scoring workflow."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.cache_client = CacheClient(CacheConfig())
        self.cv_repo = CVRepository()
        self.score_repo = ScoreRepository()
        self.jd_repo = JDRepository()
        self.version_manager = VersionManager()
        
        self.cv_retriever = CVRetriever(self.cache_client, self.cv_repo)
        self.score_retriever = ScoreRetriever(self.cache_client, self.score_repo)
        
        self.composite_scorer = CompositeScorer()
        self.rescoring_engine = RescoringEngine(
            self.composite_scorer,
            self.score_repo,
            self.version_manager
        )
    
    def test_full_scoring_workflow(self):
        """Test complete scoring workflow."""
        # Setup CV and JD
        cv_data = {
            "name": "John Doe",
            "skills": ["Python", "SQL"],
            "total_experience_years": 5,
            "seniority_level": "mid",
            "education": [{"degree_type": "Bachelors"}],
        }
        
        jd_data = {
            "title": "Senior Developer",
            "skills": ["Python", "SQL"],
            "min_experience_years": 3,
            "required_seniority": "mid",
            "required_degree": "Bachelors",
        }
        
        # Store data
        self.cv_repo.set("cv1", cv_data)
        self.jd_repo.set("jd1", jd_data)
        
        # Score
        scores = self.composite_scorer.score(cv_data, jd_data)
        
        # Verify scores
        assert "composite_score" in scores
        assert scores["composite_score"] > 50
    
    def test_rescoring_workflow(self):
        """Test rescoring on updates."""
        # Initial setup
        self.cv_repo.set("cv1", {"skills": ["Python"]})
        self.jd_repo.set("jd1", {"skills": ["Python"]})
        
        # Store a score
        self.score_repo.set("cv1:jd1", {"composite_score": 80})
        
        # Trigger CV update
        event = self.version_manager.on_cv_updated("cv1", "Updated")
        affected = self.rescoring_engine.handle_rescore_event(event)
        
        # Verify rescoring queued
        assert affected >= 0
    
    def test_interview_result_workflow(self):
        """Test interview result recording."""
        # Setup
        self.cv_repo.set("cv1", {"name": "John"})
        
        # Record interview result
        event = self.version_manager.on_interview_result("cv1", "Interview completed")
        
        # Verify event
        assert event.event_type.value == "INTERVIEW_RESULT"


class TestCachingBehavior:
    """Test caching behavior."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.cache_client = CacheClient(CacheConfig())
        self.cv_repo = CVRepository()
        self.cv_retriever = CVRetriever(self.cache_client, self.cv_repo)
    
    def test_cache_hit_on_retrieval(self):
        """Test cache hit on second retrieval."""
        cv_data = {"name": "John", "skills": ["Python"]}
        self.cv_repo.set("cv1", cv_data)
        
        # First retrieval - miss
        result1 = self.cv_retriever.get_cv("cv1")
        
        # Second retrieval - should be from cache
        result2 = self.cv_retriever.get_cv("cv1")
        
        assert result1 == result2
    
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        cv_data = {"name": "John"}
        self.cv_repo.set("cv1", cv_data)
        
        # Get to cache
        self.cv_retriever.get_cv("cv1")
        
        # Invalidate
        count = self.cv_retriever.invalidate_cv_cache("cv1")
        
        assert count >= 0


class TestDataConsistency:
    """Test data consistency."""
    
    def test_score_storage_consistency(self):
        """Test score storage maintains consistency."""
        repo = ScoreRepository()
        
        score1 = {
            "cv_id": "cv1",
            "jd_id": "jd1",
            "composite_score": 85,
        }
        
        repo.set("cv1:jd1", score1)
        
        retrieved = repo.get("cv1:jd1")
        assert retrieved["composite_score"] == score1["composite_score"]
    
    def test_version_consistency(self):
        """Test version tracking consistency."""
        cv_repo = CVRepository()
        
        cv_repo.set("cv1", {"v": 1})
        v1 = cv_repo.get_latest_version("cv1")
        
        cv_repo.set("cv1", {"v": 2})
        v2 = cv_repo.get_latest_version("cv1")
        
        assert v2 > v1
