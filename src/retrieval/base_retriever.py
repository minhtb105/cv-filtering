"""Base retriever for data access patterns."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class BaseRetriever(ABC):
    """Abstract base class for retrievers."""
    
    @abstractmethod
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve item by key."""
        pass
    
    @abstractmethod
    def retrieve_batch(self, keys: List[str]) -> Dict[str, Any]:
        """Retrieve multiple items."""
        pass
    
    @abstractmethod
    def is_cached(self, key: str) -> bool:
        """Check if item exists in cache."""
        return False