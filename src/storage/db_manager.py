"""
MongoDB Database Manager - Singleton connection
"""

import threading
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from src.config import settings


class DatabaseManager:
    """MongoDB singleton connection manager"""

    _instance: Optional["DatabaseManager"] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        
        return cls._instance

    def connect(self) -> Database:
        """Connect to MongoDB"""
        if self._client is None:
            with self._lock:
                if self._client is None:
                    self._client = MongoClient(
                        settings.MONGODB_URL,
                        serverSelectionTimeoutMS=5000,
                        connectTimeoutMS=5000,
                        socketTimeoutMS=30000,
                    )
                    self._db = self._client[settings.MONGODB_DB]
        
        return self._db

    def get_db(self) -> Database:
        """Get database instance"""
        if self._db is None:
            return self.connect()
        return self._db

    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

    def ping(self) -> bool:
        """Check MongoDB connection"""
        try:
            self.get_db().client.admin.command("ping")
            return True
        except Exception:
            return False


db_manager = DatabaseManager()

__all__ = ["DatabaseManager", "db_manager"]
