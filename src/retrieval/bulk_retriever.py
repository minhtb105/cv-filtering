"""Bulk retriever for batch operations."""

import logging
from typing import Dict, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.retrieval.cv_retriever import CVRetriever
from src.retrieval.score_retriever import ScoreRetriever

logger = logging.getLogger(__name__)


class BulkRetriever:
    """Handle bulk retrieval operations."""
    
    def __init__(
        self,
        cv_retriever: CVRetriever,
        score_retriever: ScoreRetriever,
    ):
        """Initialize bulk retriever."""
        self.cv_retriever = cv_retriever
        self.score_retriever = score_retriever
    
    def get_multiple_cvs(self, cv_ids: List[str]) -> Dict[str, Any]:
        """Retrieve multiple CVs in parallel."""
        results = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.cv_retriever.get_cv, cv_id): cv_id
                for cv_id in cv_ids
            }
            
            for future in as_completed(futures):
                cv_id = futures[future]
                try:
                    results[cv_id] = future.result()
                except Exception as e:
                    logger.error(f"Error retrieving CV {cv_id}: {e}")
                    results[cv_id] = None
        
        logger.info(f"Successfully retrieved {len([v for v in results.values() if v])} of {len(cv_ids)} CVs")
        return results
    
    def get_multiple_scores(
        self,
        cv_jd_pairs: List[tuple],  # [(cv_id, jd_id), ...]
    ) -> Dict[Tuple, Any]:
        """Retrieve multiple scores in parallel."""
        results = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.score_retriever.get_latest_score, cv_id, jd_id): (cv_id, jd_id)
                for cv_id, jd_id in cv_jd_pairs
            }
            
            for future in as_completed(futures):
                cv_id, jd_id = futures[future]
                key = (cv_id, jd_id)
                try:
                    results[key] = future.result()
                except Exception as e:
                    logger.error(f"Error retrieving score {cv_id}:{jd_id}: {e}")
                    results[key] = None
        
        logger.info(f"Successfully retrieved {len([v for v in results.values() if v])} of {len(cv_jd_pairs)} scores")
        return results
    
    def get_scores_for_multiple_cvs(self, cv_ids: List[str], jd_id: str) -> Dict[str, List[Any]]:
        """Get scores for multiple CVs against a single JD."""
        pairs = [(cv_id, jd_id) for cv_id in cv_ids]
        scores = self.get_multiple_scores(pairs)
        
        # Reorganize by CV
        results = {cv_id: [] for cv_id in cv_ids}
        for key, score in scores.items():
            cv_id, retrieved_jd_id = key.split(":")
            if score:
                results[cv_id].append(score)
        
        return results
    
    def get_scores_for_multiple_jds(self, cv_id: str, jd_ids: List[str]) -> Dict[str, List[Any]]:
        """Get scores for a single CV against multiple JDs."""
        pairs = [(cv_id, jd_id) for jd_id in jd_ids]
        scores = self.get_multiple_scores(pairs)
        
        # Reorganize by JD
        results = {jd_id: [] for jd_id in jd_ids}
        for key, score in scores.items():
            retrieved_cv_id, jd_id = key.split(":")
            if score:
                results[jd_id].append(score)
        
        return results
