"""Tests for repository layer."""

from src.repository import (
    CVRepository,
    ScoreRepository,
    InterviewRepository,
    JDRepository,
    VersionManager,
    ChangeType,
)


class TestCVRepository:
    """Test CV repository."""

    def test_store_and_retrieve_cv(self):
        """Test storing and retrieving CV."""
        repo = CVRepository()
        cv_data = {"name": "John", "skills": ["Python", "SQL"]}

        repo.set("cv1", cv_data)
        retrieved = repo.get("cv1")

        assert retrieved is not None
        assert retrieved["name"] == "John"

    def test_cv_versioning(self):
        """Test CV versioning."""
        repo = CVRepository()

        repo.set("cv1", {"version": 1})
        repo.set("cv1", {"version": 2})

        versions = repo.get_versions("cv1")
        assert len(versions) == 2

        latest = repo.get_latest_version("cv1")
        assert latest == 2

    def test_get_cv_by_version(self):
        """Test getting CV at specific version."""
        repo = CVRepository()

        repo.set("cv1", {"name": "v1"})
        repo.set("cv1", {"name": "v2"})

        cv_v1 = repo.get_cv_by_version("cv1", 1)
        assert cv_v1 is not None

        cv_v2 = repo.get_cv_by_version("cv1", 2)
        assert cv_v2 is not None


class TestScoreRepository:
    """Test score repository."""

    def test_store_and_retrieve_score(self):
        """Test storing and retrieving score."""
        repo = ScoreRepository()
        score_data = {
            "cv_id": "cv1",
            "jd_id": "jd1",
            "composite_score": 85.5,
        }

        repo.set("cv1:jd1", score_data)
        retrieved = repo.get("cv1:jd1")

        assert retrieved is not None
        assert retrieved["composite_score"] == 85.5

    def test_score_history(self):
        """Test score history tracking."""
        repo = ScoreRepository()

        repo.set("cv1:jd1", {"score": 80})
        repo.set("cv1:jd1", {"score": 85})

        history = repo.get_history("cv1:jd1")
        assert len(history) == 2

    def test_invalidate_cv_scores(self):
        """Test invalidating scores for a CV."""
        repo = ScoreRepository()

        repo.set("cv1:jd1", {"score": 80})
        repo.set("cv1:jd2", {"score": 85})

        count = repo.invalidate_scores_for_cv("cv1")
        assert count == 2

        assert repo.get("cv1:jd1") is None


class TestInterviewRepository:
    """Test interview repository."""

    def test_store_interview_result(self):
        """Test storing interview result."""
        repo = InterviewRepository()

        result = {
            "technical_score": 85,
            "soft_skills_score": 90,
        }

        repo.set("cv1", result)
        retrieved = repo.get("cv1")

        assert retrieved is not None
        assert retrieved["technical_score"] == 85

    def test_interview_history(self):
        """Test interview history."""
        repo = InterviewRepository()

        repo.set("cv1", {"score": 80})
        repo.set("cv1", {"score": 85})

        all_interviews = repo.get_all_interviews("cv1")
        assert len(all_interviews) == 2


class TestJDRepository:
    """Test JD repository."""

    def test_store_and_retrieve_jd(self):
        """Test storing and retrieving JD."""
        repo = JDRepository()
        jd_data = {"title": "Senior Developer", "skills": ["Python"]}

        repo.set("jd1", jd_data)
        retrieved = repo.get("jd1")

        assert retrieved is not None
        assert retrieved["title"] == "Senior Developer"

    def test_jd_versioning(self):
        """Test JD versioning."""
        repo = JDRepository()

        repo.set("jd1", {"title": "Dev 1"})
        repo.set("jd1", {"title": "Dev 2"})

        versions = repo.get_versions("jd1")
        assert len(versions) == 2

    def test_get_jd_by_version(self):
        """Test getting JD at specific version."""
        repo = JDRepository()

        repo.set("jd1", {"title": "v1", "skills": ["Python"]})
        repo.set("jd1", {"title": "v2", "skills": ["Python", "SQL"]})

        jd_v1 = repo.get_jd_by_version("jd1", 1)
        assert jd_v1 is not None
        assert jd_v1["title"] == "v1"
        assert jd_v1["skills"] == ["Python"]

        jd_v2 = repo.get_jd_by_version("jd1", 2)
        assert jd_v2 is not None
        assert jd_v2["title"] == "v2"
        assert jd_v2["skills"] == ["Python", "SQL"]

        # Test boundary conditions
        assert repo.get_jd_by_version("jd1", 0) is None
        assert repo.get_jd_by_version("jd1", 3) is None


class TestVersionManager:
    """Test version manager."""

    def test_cv_update_event(self):
        """Test CV update event."""
        manager = VersionManager()

        event = manager.on_cv_updated("cv1", "Updated")
        assert event.event_type == ChangeType.CV_UPDATED
        assert event.entity_id == "cv1"
        assert event.status == "QUEUED"

    def test_jd_update_event(self):
        """Test JD update event."""
        manager = VersionManager()

        event = manager.on_jd_updated("jd1", "Updated")
        assert event.event_type == ChangeType.JD_UPDATED

    def test_interview_result_event(self):
        """Test interview result event."""
        manager = VersionManager()

        event = manager.on_interview_result("cv1", "Interview done")
        assert event.event_type == ChangeType.INTERVIEW_RESULT

    def test_version_tracking(self):
        """Test version tracking."""
        manager = VersionManager()

        manager.on_cv_updated("cv1")
        manager.on_cv_updated("cv1")

        version = manager.get_cv_version("cv1")
        assert version == 2

    def test_event_history(self):
        """Test event history."""
        manager = VersionManager()

        manager.on_cv_updated("cv1")
        manager.on_cv_updated("cv2")

        events = manager.get_events()
        assert len(events) == 2

        cv1_events = manager.get_events("cv1")
        assert len(cv1_events) == 1