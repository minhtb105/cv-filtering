"""FastAPI application and routing."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse

from src.cache import CacheClient, CacheConfig
from src.repository import (
    CVRepository,
    ScoreRepository,
    InterviewRepository,
    JDRepository,
    VersionManager,
)
from src.retrieval import CVRetriever, ScoreRetriever, BulkRetriever
from src.scoring import CompositeScorer, RescoringEngine

from .models import (
    DetailedScoreRequest,
    BatchScoreRequest,
    InterviewResultRequest,
    RescoringRequest,
    NewCVVersionRequest,
    UpdateJDRequest,
    ScoreResult,
    ScoreBreakdown,
    ComparisonRequest,
    ComparisonResult,
    RankingRequest,
    RankingResult,
    HealthCheckResponse,
    MetricsResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CV Scoring API",
    description="API for scoring and ranking CVs against job descriptions",
    version="1.0.0",
)

# Initialize components
cache_config = CacheConfig()
cache_client = CacheClient(cache_config)
cv_repo = CVRepository()
score_repo = ScoreRepository()
interview_repo = InterviewRepository()
jd_repo = JDRepository()
version_manager = VersionManager()

cv_retriever = CVRetriever(cache_client, cv_repo)
score_retriever = ScoreRetriever(cache_client, score_repo)
bulk_retriever = BulkRetriever(cv_retriever, score_retriever)

composite_scorer = CompositeScorer()
rescoring_engine = RescoringEngine(composite_scorer, score_repo, version_manager)

# Track metrics
start_time = datetime.utcnow()
metrics = {
    "total_scores": 0,
    "scoring_times": [],
}


# ============================================================================
# Core Scoring Endpoints
# ============================================================================

@app.post("/api/v1/score/cv", response_model=ScoreResult)
async def score_cv(request: DetailedScoreRequest):
    """Score a single CV against a JD."""
    try:
        # Get CV and JD data
        cv_data = cv_retriever.get_cv(request.cv_id)
        jd_data = jd_repo.get(request.jd_id)
        
        if not cv_data:
            raise HTTPException(status_code=404, detail=f"CV {request.cv_id} not found")
        if not jd_data:
            raise HTTPException(status_code=404, detail=f"JD {request.jd_id} not found")
        
        # Get interview result if available
        interview_result = interview_repo.get(request.cv_id)
        
        # Calculate scores
        score_data = composite_scorer.score(cv_data, jd_data, interview_result)
        
        # Get versions
        cv_version = cv_retriever.cv_repository.get_latest_version(request.cv_id)
        jd_version = jd_repo.get_latest_version(request.jd_id)
        
        # Store score
        repo_key = f"{request.cv_id}:{request.jd_id}"
        score_entry = {
            "cv_id": request.cv_id,
            "jd_id": request.jd_id,
            "cv_version": cv_version,
            "jd_version": jd_version,
            **score_data,
        }
        score_repo.set(repo_key, score_entry)
        
        # Cache the score
        cached = cache_client.get(f"cvai:score:latest:{request.cv_id}:{request.jd_id}")
        
        return ScoreResult(
            cv_id=request.cv_id,
            jd_id=request.jd_id,
            cv_version=cv_version,
            jd_version=jd_version,
            skill_score=score_data["skill_score"],
            experience_score=score_data["experience_score"],
            education_score=score_data["education_score"],
            interview_score=score_data["interview_score"],
            composite_score=score_data["composite_score"],
            breakdown=ScoreBreakdown(**score_data["breakdown"]),
            timestamp=datetime.utcnow(),
            cached=cached is not None,
            cache_hit=cached is not None,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scoring CV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/score/batch")
async def score_batch(request: BatchScoreRequest):
    """Score multiple CVs in batch."""
    try:
        results = []
        
        # Get scores for all pairs
        scores = bulk_retriever.get_multiple_scores(request.cv_jd_pairs)
        
        for key, score in scores.items():
            if score:
                results.append(score)
        
        return {
            "results": results,
            "total": len(request.cv_jd_pairs),
            "successful": len(results),
            "failed": len(request.cv_jd_pairs) - len(results),
        }
    
    except Exception as e:
        logger.error(f"Error in batch scoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/score/{cv_id}")
async def get_latest_score(cv_id: str, jd_id: str):
    """Get latest score for a CV."""
    try:
        score = score_retriever.get_latest_score(cv_id, jd_id)
        
        if not score:
            raise HTTPException(status_code=404, detail=f"Score not found for CV {cv_id}")
        
        return score
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/score/{cv_id}/history")
async def get_score_history(cv_id: str, jd_id: str):
    """Get score history for a CV-JD pair."""
    try:
        history = score_retriever.get_score_history(cv_id, jd_id)
        
        return {
            "cv_id": cv_id,
            "jd_id": jd_id,
            "history": history,
            "total_scores": len(history),
        }
    
    except Exception as e:
        logger.error(f"Error getting score history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Rescoring & Management Endpoints
# ============================================================================

@app.post("/api/v1/rescore")
async def trigger_rescore(request: RescoringRequest):
    """Trigger rescoring for CVs or JDs."""
    try:
        if request.trigger == "CV_UPDATE":
            event = version_manager.on_cv_updated(request.cv_ids[0], request.reason)
        elif request.trigger == "JD_UPDATE":
            event = version_manager.on_jd_updated(request.jd_id, request.reason)
        elif request.trigger == "INTERVIEW_RESULT":
            event = version_manager.on_interview_result(request.cv_ids[0], request.reason)
        else:
            event = version_manager.on_manual_rescore(request.cv_ids[0], "CV", request.reason)
        
        # Handle the event
        affected_count = rescoring_engine.handle_rescore_event(event)
        
        return {
            "event_id": event.event_id,
            "status": "initiated",
            "affected_pairs": affected_count,
        }
    
    except Exception as e:
        logger.error(f"Error triggering rescore: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/cv/{cv_id}/interview-result")
async def add_interview_result(cv_id: str, request: InterviewResultRequest):
    """Add interview result for a CV."""
    try:
        interview_data = {
            "cv_id": cv_id,
            "technical_score": request.technical_score,
            "soft_skills_score": request.soft_skills_score,
            "cultural_fit_score": request.cultural_fit_score,
            "notes": request.notes,
        }
        
        interview_repo.set(cv_id, interview_data)
        
        # Trigger rescoring
        event = version_manager.on_interview_result(cv_id, "Interview result recorded")
        rescoring_engine.handle_rescore_event(event)
        
        return {
            "cv_id": cv_id,
            "status": "recorded",
            "rescore_triggered": True,
        }
    
    except Exception as e:
        logger.error(f"Error adding interview result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/job-description/{jd_id}")
async def update_jd(jd_id: str, request: UpdateJDRequest):
    """Update a job description."""
    try:
        jd_repo.set(jd_id, request.jd_data)
        
        # Trigger rescoring for all affected CVs
        event = version_manager.on_jd_updated(jd_id, request.reason or "Job description updated")
        rescoring_engine.handle_rescore_event(event)
        
        return {
            "jd_id": jd_id,
            "status": "updated",
            "rescore_triggered": True,
        }
    
    except Exception as e:
        logger.error(f"Error updating JD: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/cv/{cv_id}/new-version")
async def register_cv_version(cv_id: str, request: NewCVVersionRequest):
    """Register a new CV version."""
    try:
        event = version_manager.on_cv_updated(cv_id, request.reason or "CV updated")
        rescoring_engine.handle_rescore_event(event)
        
        # Clear cache for this CV
        cache_client.invalidate_cv(cv_id)
        
        return {
            "cv_id": cv_id,
            "version": version_manager.get_cv_version(cv_id),
            "rescore_triggered": True,
        }
    
    except Exception as e:
        logger.error(f"Error registering CV version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Analysis & Comparison Endpoints
# ============================================================================

@app.get("/api/v1/compare/{cv_id}/{jd_id}", response_model=ComparisonResult)
async def compare_cv_jd(cv_id: str, jd_id: str, request: ComparisonRequest = None):
    """Compare CV against JD in detail."""
    try:
        score = score_retriever.get_latest_score(cv_id, jd_id)
        
        if not score:
            raise HTTPException(status_code=404, detail="Score not found")
        
        return ComparisonResult(
            cv_id=cv_id,
            jd_id=jd_id,
            composite_score=score.get("composite_score", 0),
            skill_gaps=["SQL", "Kubernetes"],  # Placeholder
            experience_fit="Good",
            education_fit="Excellent",
            strengths=["Python", "Team Leadership"],
            weaknesses=["DevOps", "Kubernetes"],
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing CV and JD: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/ranking")
async def rank_cvs(request: RankingRequest):
    """Rank CVs by score for a JD."""
    try:
        scores = bulk_retriever.get_scores_for_multiple_cvs(request.cv_ids, request.jd_id)
        
        # Prepare rankings
        rankings = []
        for cv_id in request.cv_ids:
            cv_scores = scores.get(cv_id, [])
            avg_score = sum(s.get("composite_score", 0) for s in cv_scores) / len(cv_scores) if cv_scores else 0
            rankings.append((cv_id, avg_score))
        
        # Sort by score descending
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        # Apply limit if specified
        if request.limit:
            rankings = rankings[:request.limit]
        
        return RankingResult(
            jd_id=request.jd_id,
            rankings=rankings,
            total_ranked=len(rankings),
        )
    
    except Exception as e:
        logger.error(f"Error ranking CVs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system metrics."""
    try:
        cache_stats = cache_client.get_stats()
        queue_stats = rescoring_engine.get_queue_stats()
        
        uptime = (datetime.utcnow() - start_time).total_seconds()
        
        return MetricsResponse(
            cache_hit_rate=float(cache_stats.get("hit_rate", "0%").rstrip("%")),
            avg_scoring_time=sum(metrics["scoring_times"]) / len(metrics["scoring_times"]) if metrics["scoring_times"] else 0,
            rescore_queue_length=queue_stats.get("queue_length", 0),
            total_scores_computed=metrics["total_scores"],
            uptime_seconds=uptime,
        )
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# System Management Endpoints
# ============================================================================

@app.post("/api/v1/cache/clear")
async def clear_cache(pattern: Optional[str] = None):
    """Clear cache."""
    try:
        if pattern:
            count = cache_client.delete_pattern(pattern)
        else:
            cache_client.clear_all()
            count = -1
        
        return {
            "status": "cleared",
            "cleared_entries": count,
        }
    
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health", response_model=HealthCheckResponse)
async def health_check():
    """Check API and system health."""
    try:
        cache_health = cache_client.health_check()
        
        return HealthCheckResponse(
            status="healthy",
            cache_status=cache_health.get("status", "unknown"),
            database_status="healthy",  # Placeholder
            api_version="1.0.0",
        )
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTPException",
            detail=exc.detail,
        ).dict(),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
