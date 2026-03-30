"""Rescoring engine for handling version management and event-driven rescoring."""

import logging
from typing import Any, Dict, Optional, List, Callable
from datetime import datetime

from src.repository import VersionManager, RescoringEvent, ScoreRepository
from src.scoring.composite_scorer import CompositeScorer

logger = logging.getLogger(__name__)


class RescoringEngine:
    """Manage rescoring workflows and track score versions."""
    
    def __init__(
        self,
        composite_scorer: CompositeScorer,
        score_repository: ScoreRepository,
        version_manager: VersionManager,
    ):
        """Initialize rescoring engine."""
        self.composite_scorer = composite_scorer
        self.score_repository = score_repository
        self.version_manager = version_manager
        self.rescore_queue = []
        self.rescore_handlers = []
    
    def register_rescore_handler(self, handler: Callable):
        """Register handler for rescore events."""
        self.rescore_handlers.append(handler)
    
    def handle_rescore_event(self, event: RescoringEvent) -> int:
        """Handle a rescore event."""
        logger.info(f"Handling rescore event: {event.event_type} for {event.entity_id}")
        
        # Update event status
        event.status = "PROCESSING"
        
        # Queue rescoring tasks
        affected_count = 0
        if event.entity_type == "CV":
            affected_count = self._queue_cv_rescores(event.entity_id, event)
        elif event.entity_type == "JD":
            affected_count = self._queue_jd_rescores(event.entity_id, event)
        
        # Mark as completed
        event.status = "COMPLETED"
        
        # Notify handlers
        for handler in self.rescore_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in rescore handler: {e}")
        
        return affected_count
    
    def _queue_cv_rescores(self, cv_id: str, event: RescoringEvent) -> int:
        """Queue rescoring for all JDs associated with this CV."""
        # Get all scores for this CV
        cv_scores = self.score_repository.get_scores_for_cv(cv_id)
        
        for score_entry in cv_scores:
            jd_id = score_entry.get("jd_id")
            if jd_id:
                self.rescore_queue.append({
                    "cv_id": cv_id,
                    "jd_id": jd_id,
                    "event": event,
                    "priority": event.priority,
                    "timestamp": datetime.now(datetime.timezone.utc).isoformat(),
                })
        
        logger.info(f"Queued {len(cv_scores)} rescores for CV {cv_id}")
        return len(cv_scores)
    
    def _queue_jd_rescores(self, jd_id: str, event: RescoringEvent) -> int:
        """Queue rescoring for all CVs associated with this JD."""
        # Get all scores for this JD
        jd_scores = self.score_repository.get_scores_for_jd(jd_id)
        
        for score_entry in jd_scores:
            cv_id = score_entry.get("cv_id")
            if cv_id:
                self.rescore_queue.append({
                    "cv_id": cv_id,
                    "jd_id": jd_id,
                    "event": event,
                    "priority": event.priority,
                    "timestamp": datetime.now(datetime.timezone.utc).isoformat(),
                })
        
        logger.info(f"Queued {len(jd_scores)} rescores for JD {jd_id}")
        return len(jd_scores)
    
    def process_rescore_queue(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Process pending rescores."""
        # Sort by priority (descending) then timestamp (ascending)
        self.rescore_queue.sort(
            key=lambda x: (-x["priority"], x["timestamp"])
        )
        
        results = []
        items_to_process = self.rescore_queue[:limit] if limit else self.rescore_queue
        
        for item in items_to_process:
            try:
                cv_id = item["cv_id"]
                jd_id = item["jd_id"]
                
                # Rescore would happen here (integration with actual scoring)
                logger.info(f"Processing rescore: CV {cv_id} vs JD {jd_id}")
                
                results.append({
                    "cv_id": cv_id,
                    "jd_id": jd_id,
                    "status": "processed",
                    "timestamp": datetime.now(datetime.timezone.utc).isoformat(),
                })
            except Exception as e:
                logger.error(f"Error processing rescore item: {e}")
                results.append({
                    "cv_id": item["cv_id"],
                    "jd_id": item["jd_id"],
                    "status": "error",
                    "error": str(e),
                })
        
        # Remove processed items
        if limit:
            self.rescore_queue = self.rescore_queue[limit:]
        else:
            self.rescore_queue = []
        
        return results
    
    def get_queue_length(self) -> int:
        """Get number of pending rescores."""
        return len(self.rescore_queue)
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics about the rescore queue."""
        if not self.rescore_queue:
            return {
                "queue_length": 0,
                "total_priority": 0,
                "avg_priority": 0,
            }
        
        priorities = [item["priority"] for item in self.rescore_queue]
        
        return {
            "queue_length": len(self.rescore_queue),
            "total_priority": sum(priorities),
            "avg_priority": sum(priorities) / len(priorities),
            "min_priority": min(priorities),
            "max_priority": max(priorities),
        }
