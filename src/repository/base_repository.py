"""Base repository for all data access patterns."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """Abstract base class for repositories."""
    
    def __init__(self, storage_backend: Optional[Any] = None):
        """Initialize repository."""
        self.storage_backend = storage_backend or {}
        self.created_at = datetime.utcnow()
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get item by key."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> bool:
        """Set item."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete item by key."""
        pass
    
    @abstractmethod
    def list_keys(self) -> List[str]:
        """List all keys."""
        pass
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return self.get(key) is not None
    
    def get_all(self) -> Dict[str, Any]:
        """Get all items."""
        return {key: self.get(key) for key in self.list_keys()}
