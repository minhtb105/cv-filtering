"""Version manager for tracking changes and emitting rescore events."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Types of changes that trigger rescoring."""
    CV_UPDATED = "CV_UPDATED"
    JD_UPDATED = "JD_UPDATED"
    INTERVIEW_RESULT = "INTERVIEW_RESULT"
    MANUAL_RESCORE = "MANUAL_RESCORE"


class RescoringEvent:
    """Event that triggers rescoring."""
    
    def __init__(
        self,
        event_type: ChangeType,
        entity_id: str,
        entity_type: str,  # "CV" or "JD"
        version: int,
        reason: str = "",
        priority: int = 5,
    ):
        self.event_id = f"{event_type}:{entity_id}:{datetime.now(datetime.timezone.utc).timestamp()}"
        self.event_type = event_type
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.version = version
        self.reason = reason
        self.priority = priority
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.status = "QUEUED"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "version": self.version,
            "reason": self.reason,
            "priority": self.priority,
            "timestamp": self.timestamp,
            "status": self.status,
        }


class VersionManager:
    """Manages versions and emits rescoring events."""
    
    def __init__(self):
        """Initialize version manager."""
        self.cv_versions = {}  # cv_id -> current version
        self.jd_versions = {}  # jd_id -> current version
        self.events = []       # [RescoringEvent]
        self.event_handlers = []
    
    def register_event_handler(self, handler: callable):
        """Register handler for rescore events."""
        self.event_handlers.append(handler)
    
    def emit_event(self, event: RescoringEvent):
        """Emit event and notify handlers."""
        self.events.append(event)
        logger.info(f"Emitted event: {event.event_type} for {event.entity_id}")
        
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    def on_cv_updated(self, cv_id: str, reason: str = "") -> RescoringEvent:
        """Track CV update and emit event."""
        current_version = self.cv_versions.get(cv_id, 0)
        new_version = current_version + 1
        self.cv_versions[cv_id] = new_version
        
        event = RescoringEvent(
            event_type=ChangeType.CV_UPDATED,
            entity_id=cv_id,
            entity_type="CV",
            version=new_version,
            reason=reason or "CV metadata updated",
            priority=8,
        )
        
        self.emit_event(event)
        return event
    
    def on_jd_updated(self, jd_id: str, reason: str = "") -> RescoringEvent:
        """Track JD update and emit event."""
        current_version = self.jd_versions.get(jd_id, 0)
        new_version = current_version + 1
        self.jd_versions[jd_id] = new_version
        
        event = RescoringEvent(
            event_type=ChangeType.JD_UPDATED,
            entity_id=jd_id,
            entity_type="JD",
            version=new_version,
            reason=reason or "Job description updated",
            priority=8,
        )
        
        self.emit_event(event)
        return event
    
    def on_interview_result(self, cv_id: str, reason: str = "") -> RescoringEvent:
        """Track interview result and emit event."""
        event = RescoringEvent(
            event_type=ChangeType.INTERVIEW_RESULT,
            entity_id=cv_id,
            entity_type="CV",
            version=self.cv_versions.get(cv_id, 0),
            reason=reason or "Interview result recorded",
            priority=9,
        )
        
        self.emit_event(event)
        return event
    
    def on_manual_rescore(self, entity_id: str, entity_type: str = "CV", reason: str = "") -> RescoringEvent:
        """Track manual rescore trigger."""
        version = (self.cv_versions if entity_type == "CV" else self.jd_versions).get(entity_id, 0)
        
        event = RescoringEvent(
            event_type=ChangeType.MANUAL_RESCORE,
            entity_id=entity_id,
            entity_type=entity_type,
            version=version,
            reason=reason or "Manual rescore triggered",
            priority=5,
        )
        
        self.emit_event(event)
        return event
    
    def get_events(self, entity_id: Optional[str] = None) -> List[RescoringEvent]:
        """Get events, optionally filtered by entity."""
        if entity_id:
            return [e for e in self.events if e.entity_id == entity_id]
        
        return list(self.events)
    
    def get_cv_version(self, cv_id: str) -> int:
        """Get current version of CV."""
        return self.cv_versions.get(cv_id, 0)
    
    def get_jd_version(self, jd_id: str) -> int:
        """Get current version of JD."""
        return self.jd_versions.get(jd_id, 0)
