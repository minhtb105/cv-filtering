"""
Tests cho Interview Decision Engine và JD Parser

Covers:
- Decision engine: first-time candidate
- Decision engine: returning candidate với various deltas
- Decision engine: threshold adjustment logic
- JD parser: regex fallback
- JD parser: Jaccard similarity
- Integration: full pipeline mock
"""

import pytest
from datetime import datetime, timedelta
from src.decision.interview_decision_engine import (
    InterviewDecisionEngine,
    MatchScore,
    PreviousAssessment,
    DeltaAnalysis,
)
from src.extraction.jd_parser import JDParser, JobRequirements


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def make_score(
    composite=70.0,
    skill=70.0,
    experience=70.0,
    education=70.0,
    missing_required=None,
    missing_preferred=None,
) -> MatchScore:
    return MatchScore(
        composite_score=composite,
        skill_score=skill,
        experience_score=experience,
        education_score=education,
        missing_required_skills=missing_required or [],
        missing_preferred_skills=missing_preferred or [],
    )


def make_previous(
    days_ago=90,
    composite=75.0,
    cv_skills=None,
    jd_skills=None,
) -> PreviousAssessment:
    return PreviousAssessment(
        assessment_id="test-001",
        assessed_at=datetime.utcnow() - timedelta(days=days_ago),
        composite_score=composite,
        cv_skills_snapshot=cv_skills or ["python", "django", "postgresql"],
        jd_skills_snapshot=jd_skills or ["python", "django", "docker"],
    )


# ---------------------------------------------------------------------------
# First-time candidate tests
# ---------------------------------------------------------------------------

class TestFirstTimeDecision:
    def setup_method(self):
        self.engine = InterviewDecisionEngine()
    
    def test_reject_low_score(self):
        score = make_score(composite=30.0)
        result = self.engine.decide(score)
        assert result.decision == "REJECT"
        assert result.is_first_time is True
        assert result.confidence > 0.5
    
    def test_deep_interview_mid_score(self):
        score = make_score(composite=52.0)
        result = self.engine.decide(score)
        assert result.decision == "DEEP_INTERVIEW"
        assert result.is_first_time is True
        assert result.recommended_interview_duration is not None
    
    def test_light_rescreen_good_score(self):
        score = make_score(composite=80.0)
        result = self.engine.decide(score)
        assert result.decision == "LIGHT_RESCREEN"
        assert result.is_first_time is True
        assert "30 phút" in result.recommended_interview_duration
    
    def test_no_reuse_for_first_time(self):
        """First-time candidate không được REUSE dù score cao."""
        score = make_score(composite=95.0)
        result = self.engine.decide(score)
        # Max cho first-time là LIGHT_RESCREEN
        assert result.decision in ("LIGHT_RESCREEN",)
    
    def test_evidence_contains_score(self):
        score = make_score(composite=65.0, missing_required=["kubernetes", "terraform"])
        result = self.engine.decide(score)
        evidence_text = " ".join(result.evidence)
        assert "65" in evidence_text or "65.0" in evidence_text
    
    def test_missing_skills_in_focus_areas(self):
        score = make_score(
            composite=55.0,
            missing_required=["kubernetes", "terraform"],
        )
        result = self.engine.decide(score)
        focus_text = " ".join(result.focus_areas)
        assert "kubernetes" in focus_text.lower() or "terraform" in focus_text.lower()


# ---------------------------------------------------------------------------
# Returning candidate tests
# ---------------------------------------------------------------------------

class TestReturningDecision:
    def setup_method(self):
        self.engine = InterviewDecisionEngine()
    
    def test_reuse_high_score_recent(self):
        """Score cao, interview gần đây, JD không đổi → REUSE."""
        score = make_score(composite=90.0)
        prev = make_previous(days_ago=30, composite=88.0)
        result = self.engine.decide(score, previous_assessment=prev)
        assert result.decision == "REUSE"
        assert result.is_first_time is False
    
    def test_rescore_good_score_no_change(self):
        """Score tốt, không có thay đổi → RESCORE."""
        score = make_score(composite=80.0)
        prev = make_previous(days_ago=45, composite=78.0)
        result = self.engine.decide(score, previous_assessment=prev)
        assert result.decision in ("REUSE", "RESCORE")
    
    def test_deep_interview_after_long_time(self):
        """Score vừa, lâu ngày → DEEP_INTERVIEW do threshold tăng."""
        score = make_score(composite=68.0)
        prev = make_previous(days_ago=400, composite=70.0)  # > 1 năm
        result = self.engine.decide(score, previous_assessment=prev)
        # Sau 400 ngày, threshold tăng 7 → DEEP_INTERVIEW dễ hơn
        assert result.decision in ("DEEP_INTERVIEW", "LIGHT_RESCREEN")
    
    def test_light_rescreen_with_new_cv_skills(self):
        """Score trung bình nhưng CV có skills mới → threshold giảm."""
        score = make_score(composite=72.0)
        prev = make_previous(
            days_ago=60,
            composite=65.0,
            cv_skills=["python", "django"],
        )
        # Current CV có thêm: kubernetes, terraform, aws
        result = self.engine.decide(
            score,
            previous_assessment=prev,
            cv_current_skills=["python", "django", "kubernetes", "terraform", "aws"],
        )
        # New skills → threshold giảm → decision dễ hơn
        assert result.decision in ("LIGHT_RESCREEN", "RESCORE", "REUSE")
    
    def test_stricter_when_jd_changed(self):
        """JD thay đổi nhiều → threshold tăng → quyết định khó hơn."""
        from src.extraction.jd_parser import JobRequirements
        score = make_score(composite=78.0)
        prev = make_previous(
            days_ago=60,
            jd_skills=["python", "django", "postgresql"],  # JD cũ
        )
        
        # JD mới hoàn toàn khác
        new_jd = JobRequirements(
            required_skills=["java", "spring", "kafka", "kubernetes"],
        )
        
        result = self.engine.decide(
            score,
            previous_assessment=prev,
            jd_current=new_jd,
        )
        # JD thay đổi lớn → threshold tăng → decision khó hơn
        # Score 78 bình thường = RESCORE, nhưng sau adjustment có thể = LIGHT_RESCREEN
        assert result.delta_analysis is not None
        assert result.delta_analysis.jd_similarity < 0.3  # JDs rất khác nhau
    
    def test_delta_in_evidence(self):
        """Evidence phải chứa thông tin delta."""
        score = make_score(composite=75.0)
        prev = make_previous(days_ago=200, composite=70.0)
        result = self.engine.decide(score, previous_assessment=prev)
        evidence_text = " ".join(result.evidence)
        assert "200" in evidence_text or "delta" in evidence_text.lower()


# ---------------------------------------------------------------------------
# DeltaAnalysis tests
# ---------------------------------------------------------------------------

class TestDeltaAnalysis:
    def test_no_changes_zero_adjustment(self):
        delta = DeltaAnalysis(
            new_skills_count=0,
            new_experience_months=0,
            cv_updated=False,
            jd_similarity=1.0,
            jd_required_skills_added=0,
            days_since_last_interview=30,  # recent
        )
        adj = delta.threshold_adjustment()
        assert -2 <= adj <= 2  # gần zero
    
    def test_many_new_skills_lower_threshold(self):
        delta = DeltaAnalysis(
            new_skills_count=5,
            jd_similarity=1.0,
            days_since_last_interview=30,
        )
        adj = delta.threshold_adjustment()
        assert adj < 0  # threshold giảm
    
    def test_jd_major_change_raises_threshold(self):
        delta = DeltaAnalysis(
            new_skills_count=0,
            jd_similarity=0.2,  # JD thay đổi 80%
            days_since_last_interview=30,
        )
        adj = delta.threshold_adjustment()
        assert adj > 5  # threshold tăng đáng kể
    
    def test_very_old_interview_raises_threshold(self):
        delta = DeltaAnalysis(
            new_skills_count=0,
            jd_similarity=1.0,
            days_since_last_interview=400,  # > 1 năm
        )
        adj = delta.threshold_adjustment()
        assert adj >= 7
    
    def test_adjustment_clamped(self):
        """Adjustment không vượt [-15, 15]."""
        # Worst case: everything bad
        delta = DeltaAnalysis(
            new_skills_count=0,
            jd_similarity=0.0,
            jd_required_skills_added=10,
            days_since_last_interview=1000,
        )
        adj = delta.threshold_adjustment()
        assert -15 <= adj <= 15
    
    def test_summary_includes_key_info(self):
        delta = DeltaAnalysis(
            new_skills_count=3,
            jd_similarity=0.6,
            days_since_last_interview=200,
        )
        summary = delta.summary()
        assert "skills" in summary.lower() or "new" in summary.lower()


# ---------------------------------------------------------------------------
# JD Parser tests
# ---------------------------------------------------------------------------

class TestJDParser:
    def setup_method(self):
        self.parser = JDParser()
        self.parser._ollama_available = False  # Force regex fallback
    
    def test_parse_basic_jd(self):
        jd_text = """
        Senior Python Developer
        
        Requirements:
        - Python 3+ years experience
        - Django, FastAPI
        - PostgreSQL, Redis
        - Docker, Kubernetes
        
        Nice to have: Kafka, Elasticsearch
        
        Minimum 5 years of experience required.
        """
        result = self.parser.parse(jd_text)
        assert isinstance(result, JobRequirements)
        assert "python" in result.required_skills
        assert result.min_experience_years >= 3.0
        assert result.extraction_method == "regex"
    
    def test_detect_remote(self):
        jd_text = "Python Developer - Remote OK. Work from home allowed."
        result = self.parser.parse(jd_text)
        assert result.remote_eligible is True
    
    def test_no_remote_by_default(self):
        jd_text = "Python Developer needed for office in Hanoi."
        result = self.parser.parse(jd_text)
        assert result.remote_eligible is False
    
    def test_infer_seniority_from_title(self):
        jd_text = "Senior Backend Engineer"
        result = self.parser.parse(jd_text)
        assert result.required_seniority == "senior"
    
    def test_infer_seniority_from_experience(self):
        jd_text = """
        Backend Engineer
        Minimum 8 years of experience required.
        """
        result = self.parser.parse(jd_text)
        # 8 years → lead
        assert result.required_seniority in ("lead", "senior")
    
    def test_to_scoring_dict(self):
        req = JobRequirements(
            required_skills=["python", "django"],
            min_experience_years=3.0,
            required_seniority="senior",
        )
        d = req.to_scoring_dict()
        assert "skills" in d
        assert d["skills"] == ["python", "django"]
        assert d["min_experience_years"] == 3.0


class TestJDJaccardSimilarity:
    def test_identical_jds(self):
        jd1 = JobRequirements(required_skills=["python", "django", "docker"])
        jd2 = JobRequirements(required_skills=["python", "django", "docker"])
        assert jd1.jaccard_similarity(jd2) == 1.0
    
    def test_completely_different_jds(self):
        jd1 = JobRequirements(required_skills=["python", "django"])
        jd2 = JobRequirements(required_skills=["java", "spring"])
        assert jd1.jaccard_similarity(jd2) == 0.0
    
    def test_partial_overlap(self):
        jd1 = JobRequirements(required_skills=["python", "django", "docker"])
        jd2 = JobRequirements(required_skills=["python", "fastapi", "kubernetes"])
        sim = jd1.jaccard_similarity(jd2)
        assert 0.0 < sim < 1.0
        # Intersection: {python} = 1
        # Union: {python, django, docker, fastapi, kubernetes} = 5
        assert abs(sim - 1/5) < 0.01
    
    def test_empty_jds(self):
        jd1 = JobRequirements(required_skills=[])
        jd2 = JobRequirements(required_skills=[])
        assert jd1.jaccard_similarity(jd2) == 1.0
    
    def test_one_empty(self):
        jd1 = JobRequirements(required_skills=["python"])
        jd2 = JobRequirements(required_skills=[])
        assert jd1.jaccard_similarity(jd2) == 0.0


# ---------------------------------------------------------------------------
# Confidence calculation tests
# ---------------------------------------------------------------------------

class TestConfidenceCalculation:
    def test_high_confidence_far_from_threshold(self):
        engine = InterviewDecisionEngine()
        conf = engine._calc_confidence(score=20.0, threshold=40.0, direction="below")
        assert conf > 0.8  # Far below threshold → high confidence REJECT
    
    def test_low_confidence_near_threshold(self):
        engine = InterviewDecisionEngine()
        conf = engine._calc_confidence(score=39.0, threshold=40.0, direction="below")
        assert conf < 0.6  # Just below threshold → low confidence
    
    def test_confidence_range(self):
        engine = InterviewDecisionEngine()
        for score in [0, 20, 40, 60, 80, 100]:
            conf = engine._calc_confidence(score, 50.0, "below")
            assert 0 <= conf <= 1


# ---------------------------------------------------------------------------
# Integration test (no external dependencies)
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_full_first_time_workflow(self):
        """Simulate toàn bộ workflow cho candidate lần đầu."""
        engine = InterviewDecisionEngine()
        
        # Simulate scoring output
        score = MatchScore(
            composite_score=72.0,
            skill_score=68.0,
            experience_score=75.0,
            education_score=80.0,
            missing_required_skills=["kubernetes"],
            missing_preferred_skills=["kafka"],
        )
        
        result = engine.decide(score)
        
        assert result.decision in ("REJECT", "DEEP_INTERVIEW", "LIGHT_RESCREEN")
        assert len(result.evidence) > 0
        assert result.reasoning
        assert 0 <= result.confidence <= 1
        assert result.to_dict()  # Should not raise
    
    def test_full_returning_workflow(self):
        """Simulate workflow cho returning candidate."""
        engine = InterviewDecisionEngine()
        
        score = MatchScore(composite_score=82.0, skill_score=85.0,
                          experience_score=80.0, education_score=80.0)
        prev = PreviousAssessment(
            assessment_id="prev-001",
            assessed_at=datetime.utcnow() - timedelta(days=120),
            composite_score=78.0,
            cv_skills_snapshot=["python", "django"],
            jd_skills_snapshot=["python", "django", "docker"],
        )
        
        result = engine.decide(
            score,
            previous_assessment=prev,
            cv_current_skills=["python", "django", "kubernetes", "terraform"],
        )
        
        assert result.decision in ("REUSE", "RESCORE", "LIGHT_RESCREEN", "DEEP_INTERVIEW")
        assert result.delta_analysis is not None
        assert result.delta_analysis.new_skills_count == 2  # kubernetes, terraform
