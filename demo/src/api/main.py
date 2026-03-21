"""
FastAPI endpoints for CV Intelligence Platform
Provides API for ingestion, search, scoring, and recommendations
"""
from fastapi import FastAPI, HTTPException, File, UploadFile, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
from datetime import datetime

from src.models import Candidate, CVVersion, StructuredProfile, ContactInfo, Experience, Education
from src.handlers.input_handlers import InputHandlerFactory
from src.extraction.parser import CVExtractor
from src.embeddings.embedding_service import EmbeddingService
from src.retrieval.retrieval_service import HybridRetriever
from src.scoring.scoring_engine import ScoringEngine
import numpy as np


# Initialize FastAPI app
app = FastAPI(
    title="CV Intelligence API",
    description="AI-powered CV filtering and candidate ranking",
    version="0.1.0"
)

# Global services (initialized on startup)
extractor = None
embedding_service = None
retriever = None
scoring_engine = None
candidates_db = {}  # In-memory candidate store


# ============================================================================
# Schemas
# ============================================================================

class SearchRequest(BaseModel):
    """Search request"""
    query: str
    k: int = 10
    semantic_weight: float = 0.6


class SearchResult(BaseModel):
    """Search result"""
    candidate_id: str
    score: float
    semantic_score: float
    keyword_score: float
    name: Optional[str]
    skills: List[str]


class ScoreRequest(BaseModel):
    """Scoring request"""
    job_description: str
    candidate_ids: List[str]
    model: str = "hybrid"  # hybrid, rule_based, or llm


class ScoringResult(BaseModel):
    """Single scoring result"""
    candidate_id: str
    score: float
    skill_match: float
    experience_match: float
    breakdownstr: Dict


class ScoreResponse(BaseModel):
    """Scoring response"""
    results: List[ScoringResult]


class CandidateInfo(BaseModel):
    """Candidate information"""
    candidate_id: str
    name: Optional[str]
    email: Optional[str]
    skills: List[str]
    years_experience: float


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global extractor, embedding_service, retriever, scoring_engine
    
    print("Initializing CV Intelligence services...")
    
    extractor = CVExtractor()
    print("✓ CV Extractor initialized")
    
    embedding_service = EmbeddingService()
    print("✓ Embedding Service initialized")
    
    retriever = HybridRetriever(embedding_service)
    print("✓ Hybrid Retriever initialized")
    
    scoring_engine = ScoringEngine()
    print("✓ Scoring Engine initialized")
    
    print("✓ All services ready!")


# ============================================================================
# Search Endpoints
# ============================================================================

@app.post("/search", response_model=List[SearchResult])
async def search_candidates(request: SearchRequest):
    """
    Search for candidates using hybrid retrieval
    
    Combines semantic similarity and keyword matching
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    results = retriever.search(
        request.query,
        k=request.k,
        semantic_weight=request.semantic_weight
    )
    
    return [SearchResult(**r) for r in results]


@app.get("/candidates/{candidate_id}")
async def get_candidate(candidate_id: str):
    """Get candidate information"""
    if candidate_id not in candidates_db:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    candidate = candidates_db[candidate_id]
    latest = candidate.latest_version
    
    if not latest:
        raise HTTPException(status_code=404, detail="No CV versions found")
    
    return {
        "candidate_id": candidate_id,
        "name": latest.structured_data.contact.name,
        "email": latest.structured_data.contact.email,
        "skills": latest.structured_data.skills,
        "years_experience": latest.structured_data.years_experience,
        "experiences": [
            {
                "title": exp.title,
                "company": exp.company,
                "duration": exp.duration
            }
            for exp in latest.structured_data.experiences[:3]
        ]
    }


# ============================================================================
# Scoring Endpoints
# ============================================================================

@app.post("/score", response_model=ScoreResponse)
async def score_candidates(request: ScoreRequest):
    """
    Score candidates for a job
    
    Returns ranked candidates with explanation
    """
    if not request.job_description:
        raise HTTPException(status_code=400, detail="Job description required")
    
    if not request.candidate_ids:
        raise HTTPException(status_code=400, detail="At least one candidate required")
    
    results = []
    
    for cand_id in request.candidate_ids:
        if cand_id not in candidates_db:
            continue
        
        candidate = candidates_db[cand_id]
        latest = candidate.latest_version
        
        if not latest:
            continue
        
        # Score the candidate
        score_breakdown = scoring_engine.score_candidate(
            request.job_description,
            latest.structured_data
        )
        
        results.append(ScoringResult(
            candidate_id=cand_id,
            score=score_breakdown["total_score"],
            skill_match=score_breakdown.get("skill_match", 0.0),
            experience_match=score_breakdown.get("experience_match", 0.0),
            breakdownstr=score_breakdown
        ))
    
    # Sort by score
    results = sorted(results, key=lambda x: x.score, reverse=True)
    
    return ScoreResponse(results=results)


# ============================================================================
# Recommendation Endpoints
# ============================================================================

@app.get("/candidates/{candidate_id}/similar")
async def get_similar_candidates(candidate_id: str, k: int = Query(5, ge=1, le=20)):
    """Get candidates similar to specified candidate"""
    if candidate_id not in candidates_db:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    candidate = candidates_db[candidate_id]
    
    if not candidate.embedding:
        raise HTTPException(status_code=400, detail="Candidate embedding not available")
    
    # Search by embedding
    results = retriever.faiss_index.search(candidate.embedding, k=k+1)  # +1 to exclude self
    
    similar = []
    for cid, score in results:
        if cid != candidate_id:
            if cid in candidates_db:
                c = candidates_db[cid]
                similar.append({
                    "candidate_id": cid,
                    "name": c.contact_info.name if c.contact_info else None,
                    "similarity": float(score)
                })
    
    return similar[:k]


# ============================================================================
# System Status Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "total_candidates": len(candidates_db),
        "retrieval_stats": retriever.get_stats() if retriever else {},
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
